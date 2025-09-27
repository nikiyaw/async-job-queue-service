import time
import random
import logging 
from celery import Celery
from ..api.core.database import SessionLocal
from ..api.models.sql_models.job import Job as JobModel
from .db_utils import get_db_session

# Set up logging for the worker
logger = logging.getLogger(__name__)

# We will use an environment variable for the Redis URL later in a Docker Compose setup.
# For now, we'll hardcode it to match our docker-compose.yml file.
REDIS_URL = "redis://localhost:6379"

# Create the Celery application instance
celery_app = Celery("job_processor", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_default_queue = "job_queue"

def update_job_status_on_failure(task, exc, task_id, args, kwargs, einfo):
    """
    This failure handler runs when a task permanently fails (all retries exhausted).
    It updates the job status in the PostgreSQL database to 'failed'.
    It uses the context manager, so no explicit db.commit() is needed.
    """
    job_id = args[0]
    logger.error(f"Job {job_id} permanently failed after retries.", exc_info=True)

    # Opens a new transaction specifically for updating the failure status
    with get_db_session() as db:
        try:
            job = db.query(JobModel).filter(JobModel.id == job_id).first()
            if job:
                job.status = "failed"
                job.result = None
                job.error_message = {"error": str(exc), "details": "Job failed after all retries were exhausted."}
                logger.info(f"Database status for job {job_id} updated to 'failed'.")
        except Exception as update_e:
            # The context manager will handle rollback, but we log the critical failure
            logger.error(f"FATAL: Could not update status for failed job {job_id}: {update_e}")

@celery_app.task(bind=True, on_failure=update_job_status_on_failure, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def process_job(self, job_id: int):
    """
    Simulates a long-running job and updates its status and result.
    This version includes an automatic retry mechanism.
    In a real-world scenario, this would contain the actual job logic.
    """

    # Determine if this is the first run or a retry attempt
    is_retry = self.request.retries > 0
    logger.info(f"Processing job with ID: {job_id}, Attempt: {self.request.retries + 1}")

    try:
        # Transaction 1: Fetch job and execute main logic
        with get_db_session() as db:
            # Get job payload and update status to reflect worker pickup
            job = db.query(JobModel).filter(JobModel.id == job_id).first()
            if not job:
                # Raise an error that will be caught by the autoretry and eventually on the on_failure handler
                raise ValueError(f"Job with ID {job_id} not found in database.")
            
            job_type = job.job_type

            # Update status (This will be committed if the job succeeds, or rolled back if it fails)
            job.status = "processing" if not is_retry else "retrying"
            # We rely on the context manager to commit this change *if* the try block finishes.
            logger.info(f"Database status for job {job_id} tentatively updated to '{job.status}'.")

            final_result = None
            
            # --- Actual Job Logic Implementation ---
            if job_type == "Send Email":
                logger.info(f"Job {job_id}: Simulating quick email send ...")
                time.sleep(2)
                final_result = {"status": "success", "message": "Email sent successfully to target list."}
            
            elif job_type == "Long Computation":
                logger.info(f"Job {job_id}: Starting long-running calculation ...")
                time.sleep(10)
                final_result = {"status": "success", "message": "Calculation completed successfully."}

            elif job_type == "Data Analysis":
                # Simulate a job that is likely to fail transiently (e.g., network timeout)
                # It will fail 70% of the time on the first two attempts, but succeed on the third.
                
                # We check the retry count. Since it starts at 0, this checks attempts 1 and 2.
                if self.request.retries < 2 and random.random() < 0.7:
                    logger.warning(f"Job {job_id}: Simulated transient failure for 'Data Analysis'.")
                    # Raising an Exception causes the current database transaction (Transaction 1) to ROLLBACK.
                    raise RuntimeError("External service connection timed out (simulated transient error).")
                
                # If it's the 3rd attempt (retries = 2) or it passes the random check:
                logger.info(f"Job {job_id}: Data analysis successful on attempt {self.request.retries + 1}.")
                time.sleep(3)
                final_result = {"status": "success", "data": "Analysis complete. Report available."}
            
            else:
                # Default case for an unknown job type
                raise ValueError(f"Unknown job type: {job_type}")
            
            # Success: Update the job object with the final result.
            job.status = "completed"
            job.result = final_result
            job.error_message = None

            # The db_utils context manager will now automatically commit Transaction 1
            logger.info(f"Finished processing job {job.id}. Status updated to 'completed'.")

    # This exception block correctly catches any failure from the job logic above
    except Exception as e:

        # This logic handles setting the status to 'retrying' before Celery re-queues it
        if self.request.retries < self.max_retries:

            # Transaction 2: Open a new transaction specifically to update the RETRY status
            with get_db_session() as db:
                job = db.query(JobModel).filter(JobModel.id == job_id).first()
                if job:
                    job.status = "retrying"
                    job.retries = self.request.retries + 1
                    # The context manager automatically commits Transaction 2

            logger.warning(f"Job {job_id} failed on attempt {self.request.retries + 1}. Retrying in 5 seconds ...")
            # Signal Celery to re-queue the task after a 5-second countdown
            raise self.retry(exc=e, countdown=5)
        
        else:
            # If max retries are reached, we just re-raise the exception, and the 'on_failure' handler takes over to set the final 'failed' status.
            logger.error(f"Job {job_id} failed on final attempt. Passing on failure handler.")
            raise e