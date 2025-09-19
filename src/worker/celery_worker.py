import time
from celery import Celery
from ..api.core.database import SessionLocal
from ..api.models.sql_models.job import Job as JobModel

# We will use an environment variable for the Redis URL later in a Docker Compose setup.
# For now, we'll hardcode it to match our docker-compose.yml file.
REDIS_URL = "redis://localhost:6379"

# Create the Celery application instance
celery_app = Celery("job_processor", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_default_queue = "job_queue"

# Celery will automatically discover and register tasks in this module.
@celery_app.task
def process_job(job_id: int):
    """
    A task to simulate a long-running job.
    In a real-world scenario, this would contain the actual job logic.
    """
    print(f"Processing job with ID: {job_id}")

    # Establish a database session
    db = SessionLocal()

    try:
        # Simulate a 5-second long-running task
        time.sleep(5) 

        # This will simulate a failure for odd-numbered job IDs.
        if job_id % 2 != 0:
            raise ValueError("simulated job failure for odd-numbered job IDs.")

        # If the job is successful, update the status to 'completed' and save the result
        dummy_result = {"message": f"Job {job_id} completed successfully!", "status_code": 200}
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        if job:
            job.status = "completed"
            job.result = dummy_result
            job.error_message = None
            db.commit()
            print(f"Finished processing job with ID: {job_id}. Status updated to 'completed'.")
        else:
            print(f"Job with ID: {job_id} not found in the database.")

    except Exception as e:
        # If an error occurs, update the status to 'failed' and save the error message
        db.rollback()
        try:
            job = db.query(JobModel).filter(JobModel.id == job_id).first()
            if job:
                job.status = "failed"
                job.result = None
                job.error_message = {"error": str(e), "details": "An unexpected error occurred during job processing."}
                db.commit()
                print(f"An error occurred while processing job {job_id}: {e}")
            else:
                print(f"Job with ID: {job_id} not found in the database.")
        except Exception as update_e:
            db.rollback()
            print(f"An error occured while updating job status for ID {job_id}: {update_e}")

        raise

    finally:
        db.close()