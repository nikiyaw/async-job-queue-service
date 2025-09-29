from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from starlette.concurrency import run_in_threadpool

from src.api.models.job import (
    JobCreate,
    JobSubmitResponse,
    JobStatus,
    JobStatusResponse,
)
from ..models.sql_models.job import Job as JobModel
from ..core.database import get_db
from ..core.celery_app import celery_app

import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

# --- CONVERTED TO ASYNC ---
@router.post(
    "/submit", 
    response_model=JobSubmitResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new job for asynchronous processing" # Added documentation summary
)
async def submit_job(job_data: JobCreate, db: Session = Depends(get_db)):
    """
    Creates a new job entry in the database and queues it for processing by the worker 
    in a separate thread to maintain non-blocking API performance.
    """
    
    # Define a synchronous function to handle all blocking DB and Celery operations
    def submit_job_sync(db: Session, job_data: JobCreate):
        # 1. Save job to database (initial state)
        new_job = JobModel(
            job_type=job_data.job_type,
            payload=job_data.payload,
            status=JobStatus.QUEUED.value # Explicitly set initial status to "queued"
        )

        db.add(new_job)
        db.commit()
        db.refresh(new_job) # To get the newly created ID

        # 2. Send task to Celery
        try:
            celery_app.send_task(
                "src.worker.celery_worker.process_job",
                args=[new_job.id],
                queue="job_queue"
            )
            logger.info(f"API received job {new_job.id} (type: {new_job.job_type}) and queued it for processing.")
        except Exception as e:
            # If Celery is unreachable, log the error and mark the the job as failed immediately. 
            logger.error(f"Failed to queue job {new_job.id} to Celery: {e}")
            # Note: Typo fixed here: `erro_message` -> `error_message`
            new_job.status = JobStatus.FAILED.value
            new_job.error_message = {"error": "Celery Connection Error", "details": str(e)}
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Job saved but failed to queue to worker. Error: {str(e)}"
            )
        
        return new_job

    # Execute the blocking database and Celery logic in a separate thread
    new_job = await run_in_threadpool(submit_job_sync, db, job_data)
    
    return JobSubmitResponse(
        message="Job received successfully", 
        job_id=new_job.id, 
        job_type=new_job.job_type, 
        status=JobStatus.QUEUED.value
    )


# --- CONVERTED TO ASYNC ---
@router.get(
    "/status/{job_id}", 
    response_model=JobStatusResponse,
    summary="Get the current status and final result of a specific job" # Added documentation summary
)
async def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the current status, result, and error message for a specific job ID 
    by accessing the database in a non-blocking manner.
    """
    
    # Define a synchronous function to handle the blocking DB query
    def get_job_sync(db: Session, job_id: int):
        return db.query(JobModel).filter(JobModel.id == job_id).first()

    # Execute the blocking query in a separate thread
    job = await run_in_threadpool(get_job_sync, db, job_id)

    if not job:
        logger.warning(f"Job with ID {job_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )
    
    return job


# --- CONVERTED TO ASYNC ---
@router.get(
    "/", 
    response_model=List[JobStatusResponse],
    summary="Get a list of the 50 most recent jobs" # Added documentation summary
)
async def get_all_jobs(db: Session = Depends(get_db)):
    """
    Retrieves a list of the 50 most recent jobs, used to power the dashboard feed, 
    running the query in a separate thread.
    """
    
    # Define a synchronous function to handle the blocking DB query
    def get_all_jobs_sync(db: Session):
        # We limit the results to 50 for dashboard performance
        return db.query(JobModel).order_by(JobModel.id.desc()).limit(50).all() 

    # Execute the blocking query in a separate thread
    jobs = await run_in_threadpool(get_all_jobs_sync, db)
    
    return jobs