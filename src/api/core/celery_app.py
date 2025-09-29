from celery import Celery
from .settings import settings

# Centralized Celery app for both API and Worker
celery_app = Celery(
    "async_jobs",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Global Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_ack_late=True,
)

# optional: Load task modules automatically if you have many tasks
celery_app.autodiscover_tasks(['src.worker.tasks'])