import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.sql_models.job import Job as JobModel # This is the SQLAlchemy model (database)
# Import Celery app for task submission
from ...worker.celery_worker import celery_app
# Import updated Pydantic schemas (JobCreate, JobSubmitResponse, JobStatusResponse)
from src.api.models.job import (
    JobCreate,
    JobSubmitResponse,
    JobStatus,
    JobStatusResponse,
)

# NEW: Initialize logger for this module
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

@router.post("/submit", response_model=JobSubmitResponse, status_code=status.HTTP_201_CREATED)
def submit_job(job_data: JobCreate, db: Session = Depends(get_db)):
    """
    Submits a new job to the queue, saves its initial state to the database, 
    and sends the task to Celery.
    """
    # 1. Save job to database (initial state)
    new_job = JobModel(
        job_type=job_data.job_type,
        payload=job_data.payload,
        status=JobStatus.QUEUED.value # Explicitly set initial status to "queued"
    )

    # Add the job to the session and commit it to the database
    db.add(new_job)
    db.commit()
    db.refresh(new_job) # To get the newly created ID

    # 2. Send task to Celery
    try:
        # We pass the newly created database job ID, NOT the Celery task ID, 
        # as the database ID is our source of truth.
        celery_app.send_task(
            "src.worker.celery_worker.process_job",
            args=[new_job.id],
            queue="job_queue"
        )
        logger.info(f"API received job {new_job.id} (type: {new_job.job_type}) and queued it for processing.")
    except Exception as e:
        # If Celery is unreachable, log the error and mark the the job as failed immediately. 
        logger.error(f"Failed to queue job {new_job.id} to Celery: {e}")
        new_job.status = JobStatus.FAILED.value
        new_job.erro_message = f"Celery connection error: {str(e)}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Job saved but failed to queue to worker. Error: {str(e)}"
        )

    return JobSubmitResponse(
        message="Job received successfully", 
        job_id=new_job.id, 
        job_type=new_job.job_type, 
        status=JobStatus.QUEUED.value
    )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the current status, result, and error message for a specific job ID.
    
    CRITICAL CHANGE: response_model is now JobStatusResponse, which includes 
    result and error_message fields.
    """
    job = db.query(JobModel).filter(JobModel.id == job_id).first()

    if not job:
        logger.warning(f"Job with ID {job_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )
    
    # Because JobStatusResponse has `from_attributes = True`, FastAPI automatically 
    # maps the SQLAlchemy `job` object's attributes (including result/error_message) 
    # to the Pydantic response model.
    return job


@router.get("/", response_model=List[JobStatusResponse])
def get_all_jobs(db: Session = Depends(get_db)):
    """
    Retrieves a list of all jobs, used to power the dashboard feed.
    
    CRITICAL CHANGE: response_model is now List[JobStatusResponse], ensuring all 
    jobs in the list correctly include the result and error_message fields.
    """
    # Query all jobs, ordered by descending ID (most recent first)
    jobs = db.query(JobModel).order_by(JobModel.id.desc()).all()
    # FastAPI automatically handles the serialization of the list of SQLAlchemy objects
    return jobs