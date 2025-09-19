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

        # This is a dummy result, In a real-world scenario, this would be the actual output of your task.
        dummy_result = {"message": f"Job {job_id} completed successfully!", "status_code": 200}

        # Find the job by its ID
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        if job:
            # Update the job's status
            job.status = "completed"
            # Set the new result here
            job.result = dummy_result
            db.commit()
            print(f"Finished processing job with ID: {job_id}. Status updated to 'completed'.")
        else:
            print(f"Job with ID: {job_id} not found in the database.")
    except Exception as e:
        db.rollback()
        print(f"An error occured while updating job status for ID {job_id}: {e}")
    finally:
        db.close()

    return f"Job {job_id} completed successfully!"