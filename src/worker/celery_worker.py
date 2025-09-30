import os
import time
import random
from typing import Any, Dict, Optional, Tuple
from celery import Task

from ..api.core.celery_app import celery_app
from ..api.core.database import SessionLocal
from ..api.core.logging_config import setup_logging, get_logger
from ..api.models.sql_models.job import Job as JobModel
from .db_utils import get_db_session

# Setup logging for worker process
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    json_logs=os.getenv("JSON_LOGS", "false").lower() == "true"
)
logger = get_logger(__name__)


def update_job_status_on_failure(
        task: Task,
        exc: BaseException, 
        task_id: str, 
        args: Tuple[Any, ...], 
        kwargs: Dict[str, Any],
        einfo: Any
        ) -> None:
    """
    Failure handler that runs when a task permanently fails.
    Updates the job status in the database to 'failed'.
    """
    job_id: Optional[int] = args[0] if args else None
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
                job.error_message = {
                    "error": str(exc),
                    "details": "Job failed after all retries were exhausted."
                }
                logger.info(f"Database status for job {job_id} updated to 'failed'.")
        except Exception as update_e:
            logger.error(
                f"FATAL: Could not update status for failed job {job_id}: {update_e}",
                exc_info=True
            )


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def process_job(
    self: Task,
    job_id: int) -> None:
    """
    Processes a job (simulated). Supports retries and updates job status accordingly.
    """
    is_retry = self.request.retries > 0
    attempt = self.request.retries + 1
    logger.info(f"Processing job with ID: {job_id}, Attempt: {attempt}")

    try:
        with get_db_session() as db:
            job = db.query(JobModel).filter(JobModel.id == job_id).first()
            if not job:
                raise ValueError(f"Job with ID {job_id} not found in database.")
            
            raw_job_type = (job.job_type or "").strip()
            jt: str = raw_job_type.lower()

            job.status = "processing" if not is_retry else "retrying"
            logger.info(f"Job {job_id} status set to '{job.status}'.")

            final_result: Optional[Dict[str, Any]] = None

            # Main job logic simulation
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
                logger.warning(f"Job {job_id}: Unknown job type '{raw_job_type}'. Running default handler.")
                time.sleep(1)
                final_result = {"status": "success", "message": "Default handler executed."}
            
            # Mark job completed
            job.status = "completed"
            job.result = final_result
            job.error_message = None
            logger.info(f"Finished processing job {job.id}. Status updated to 'completed'.")

    except Exception as e:
        logger.exception(f"Error while processing job {job_id}: {e}")
        if self.request.retries < self.max_retries:
            with get_db_session() as db:
                job = db.query(JobModel).filter(JobModel.id == job_id).first()
                if job:
                    job.status = "retrying"
                    job.retries = self.request.retries + 1
            logger.warning(f"Job {job_id} failed on attempt {attempt}. Retrying in 5 seconds ...")
            raise self.retry(exc=e, countdown=5)
        else:
            logger.error(f"Job {job_id} failed on final attempt. Letting failure handler set final status.")
            raise e
