from celery import Celery
import time

# We will use an environment variable for the Redis URL later in a Docker Compose setup.
# For now, we'll hardcode it to match our docker-compose.yml file.
REDIS_URL = "redis://localhost:6379"

# Create the Celery application instance
celery_app = Celery("job_processor", broker=REDIS_URL, backend=REDIS_URL)

# Celery will automatically discover and register tasks in this module.
@celery_app.task
def process_job(job_id):
    """
    A task to simulate a long-running job.
    In a real-world scenario, this would contain the actual job logic.
    """
    print(f"Processing job with ID: {job_id}")
    time.sleep(5)  # Simulate a 5-second long-running task
    print(f"Finished processing job with ID: {job_id}")
    return f"Job {job_id} completed successfully"