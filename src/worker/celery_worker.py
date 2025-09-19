from celery import Celery
from ..api.core.database import SessionLocal
from ..api.models.sql_models.job import Job as JobModel
from .db_utils import get_db_session

# We will use an environment variable for the Redis URL later in a Docker Compose setup.
# For now, we'll hardcode it to match our docker-compose.yml file.
REDIS_URL = "redis://localhost:6379"

# Create the Celery application instance
celery_app = Celery("job_processor", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_default_queue = "job_queue"

def update_job_status_on_failure(task, exc, task_id, args, kwargs, einfo):
    """
    This function is a failure handler. It runs when a task permanently fails.
    """
    job_id = args[0]
    with get_db_session() as db:
        try:
            job = db.query(JobModel).filter(JobModel.id == job_id).first()
            if job:
                job.status = "failed"
                job.result = None
                job.error_message = {"error": str(exc), "details": "Job failed after all retries."}
        except Exception as update_e:
            db.rollback()
            print(f"An error occurred while trying to update status for failed job {job_id}: {e}")

@celery_app.task(bind=True, on_failure=update_job_status_on_failure, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def process_job(self, job_id: int):
    """
    Simulates a long-running job and updates its status and result.
    This version includes an automatic retry mechanism.
    In a real-world scenario, this would contain the actual job logic.
    """
    print(f"Processing job with ID: {job_id}, Attempt: {self.request.retries + 1}")

    try:
        with get_db_session() as db:
            job = db.query(JobModel).filter(JobModel.id == job_id).first()
            payload = job.payload
            
            raise ValueError("Simulated permanent job failure.")

            final_result = {"status": "success", "message": "Email sent successfully."}
            
            job.status = "completed"
            job.result = final_result
            job.error_message = None
            print(f"Finished processing job with ID: {job_id}. Status updated to 'completed'.")

    except Exception as e:
        with get_db_session() as db:
            job = db.query(JobModel).filter(JobModel.id == job_id).first()
            if job:
                job.retries = self.request.retries + 1
                job.status = "retrying"
            print(f"An error occurred while processing job {job_id}: {e}. Retrying...")

        raise self.retry(exc=e, countdown=10)