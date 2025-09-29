import os
import time
import random
import logging 

from celery import Celery
from ..api.core.database import SessionLocal
from ..api.models.sql_models.job import Job as JobModel
from .db_utils import get_db_session

# Set up logging for the worker
logger = logging.getLogger(__name__)

# Read broker/result backend from environment (works in Docker and locally).
# Fallback to the Docker service host "redis" and default DB 0 if env not set.
BROKER_URL = os.environ.get("CELERY_BROKEN_URL", "redis://redis:6379/0")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", BROKER_URL)

# Create the Celery application instance using environment-provided URLs.
celery_app = Celery("job_processor", broker=BROKER_URL, backend=RESULT_BACKEND)
celery_app.conf.task_default_queue = "job_queue"
# sensible default config for JSON serialization and timezone
celery_app.conf.update({
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "task_ack_late": True
})

def update_job_status_on_failure(task, exc, task_id, args, kwargs, einfo):
    """
    This failure handler runs when a task permanently fails (all retries exhausted).
    It updates the job status in the database to 'failed'.
    """
    job_id = args[0] if args else None
    logger.error(f"Job {job_id} permanently failed after retries.", exc_info=True)

    if job_id is None:
        logger.error("No job_id passed to failure handler.")
        return

    with get_db_session() as db:
        try:
            job = db.query(JobModel).filter(JobModel.id == job_id).first()
            if job:
                job.status = "failed"
                job.result = None
                job.error_message = {"error": str(exc), "details": "Job failed after all retries were exhausted."}
                logger.info(f"Database status for job {job_id} updated to 'failed'.")
        except Exception as update_e:
            logger.error(f"FATAL: Could not update status for failed job {job_id}: {update_e}", exc_info=True)

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def process_job(self, job_id: int):
    """
    Processes a job (simulated). This task is robust to different job_type string formats
    and will match common phrases case-insensitively (e.g., 'send_email', 'Send Email', 'send email').
    """
    is_retry = self.request.retries > 0
    attempt = self.request.retries + 1
    logger.info(f"Processing job with ID: {job_id}, Attempt: {attempt}")

    try:
        # Transaction: fetch job, update status, perform logic, write result
        with get_db_session() as db:
            job = db.query(JobModel).filter(JobModel.id == job_id).first()
            if not job:
                raise ValueError(f"Job with ID {job_id} not found in database.")
            
            # normalize job_type to allow flexible strings
            raw_job_type = (job.job_type or "").strip() 
            jt = raw_job_type.lower() 

            # tentatively set status to reflect pickup / retrying 
            job.status = "processing" if not is_retry else "retrying"
            logger.info(f"Job {job_id} status set to '{job.status}' (raw job_type='{raw_job_type}').")

            final_result = None
            
            # -- Main logic --
            if "email" in jt or "send" in jt:
                logger.info(f"Job {job_id}: Simulating quick email send ...")
                time.sleep(2)
                final_result = {"status": "success", "message": "Email sent successfully."}
            
            elif "long" in jt or "calculation" in jt or "compute" in jt:
                logger.info(f"Job {job_id}: Starting long-running calculation ...")
                time.sleep(10)
                final_result = {"status": "success", "message": "Calculation completed successfully."}

            elif "data" in jt or "analysis" in jt:
                if self.request.retries < 2 and random.random() < 0.7:
                    logger.warning(f"Job {job_id}: Simulated transient failure for data analysis.")
                    raise RuntimeError("External service connection timed out (simulated transient error).")
                time.sleep(3)
                final_result = {"status": "success", "data": "Analysis complete. Report available."}
            
            else:
                # Default fallback: perform a short no-op (so unknown job types don't crash system)
                logger.warning(f"Job {job_id}: Unknown job type '{raw_job_type}'. Running default handler.")
                time.sleep(1)
                final_result = {"status": "success", "message": f"Default handler executed."}
            
            # mark job completed
            job.status = "completed"
            job.result = final_result
            job.error_message = None

            logger.info(f"Finished processing job {job.id}. Status updated to 'completed'.")

    except Exception as e:
        logger.exception(f"Error while processing job {job_id}: {e}")

        # If autoretry remains, set retrying status then re-raise with retry
        if self.request.retries < self.max_retries:
            with get_db_session() as db:
                job = db.query(JobModel).filter(JobModel.id == job_id).first()
                if job:
                    job.status = "retrying"
                    job.retries = self.request.retries + 1
            logger.warning(f"Job {job_id} failed on attempt {attempt}. Retrying in 5 seconds ...")
            raise self.retry(exc=e, countdown=5)
        
        else:
            # Final failure: let on_failure / outer handler update status
            logger.error(f"Job {job_id} failed on final attempt. Letting failure handler set final status.")
            # pass exception up so Celery marks it as failed and our on_failure can run
            raise e