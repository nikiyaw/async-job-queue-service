from celery import Celery
from .settings import settings

# Create the Celery app
celery_app = Celery(
    "async_job_queue",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# optional: Load task modules automatically if you have many tasks
celery_app.autodiscover_tasks(['src.worker.tasks'])