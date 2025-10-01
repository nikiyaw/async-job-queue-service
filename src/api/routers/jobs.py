from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from starlette.concurrency import run_in_threadpool
from datetime import datetime

from src.api.models.job import (
    JobCreate,
    JobSubmitResponse,
    JobStatus,
    JobStatusResponse,
)
from ..models.sql_models.job import Job as JobModel
from ..core.database import get_db
from ..core.celery_app import celery_app
from ..core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)


@router.post(
    "/submit",
    response_model=JobSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new job for asynchronous processing"
)
async def submit_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    request: Request = None
) -> JobSubmitResponse:
    client_host: str = getattr(getattr(request, "client", None), "host", "unknown")
    logger.info(f"Received new job submission request from {client_host}: type={job_data.job_type}")

    def submit_job_sync(db: Session, job_data: JobCreate) -> JobModel:
        new_job = JobModel(
            job_type=job_data.job_type,
            payload=job_data.payload,
            status=JobStatus.QUEUED.value
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        try:
            celery_app.send_task(
                "src.worker.celery_worker.process_job",
                args=[new_job.id],
                queue="job_queue"
            )
            logger.info(f"API received job {new_job.id} queued for processing (type: {new_job.job_type})")
        except Exception as e:
            logger.error(f"Failed to queue job {new_job.id} to Celery: {e}")
            new_job.status = JobStatus.FAILED.value  # type: ignore
            new_job.error_message = {"error": "Celery Connection Error", "details": str(e)}  # type: ignore
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Job saved but failed to queue to worker. Error: {str(e)}"
            )
        return new_job

    new_job: JobModel = await run_in_threadpool(submit_job_sync, db, job_data)

    return JobSubmitResponse(
        message="Job received successfully",
        job_id=int(new_job.id),
        job_type=str(new_job.job_type),
        status=JobStatus(new_job.status)
    )


@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    summary="Get the current status and final result of a specific job"
)
async def get_job_status(
    job_id: int,
    db: Session = Depends(get_db)
) -> JobStatusResponse:
    def get_job_sync(db: Session, job_id: int) -> Optional[JobModel]:
        return db.query(JobModel).filter(JobModel.id == job_id).first()

    job: Optional[JobModel] = await run_in_threadpool(get_job_sync, db, job_id)

    if not job:
        logger.warning(f"Job with ID {job_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )

    logger.info(f"Fetched status for job {job_id}: {job.status}")

    return JobStatusResponse(
        job_id=int(job.id),
        job_type=str(job.job_type),
        status=JobStatus(job.status),
        retries=int(job.retries or 0),
        created_at=job.created_at if isinstance(job.created_at, datetime) else datetime.utcnow(),
        updated_at=job.updated_at if isinstance(job.updated_at, datetime) else datetime.utcnow(),
        result=dict(job.result) if job.result else None,
        error_message=job.error_message if isinstance(job.error_message, (str, dict)) else None
    )


@router.get(
    "/",
    response_model=List[JobStatusResponse],
    summary="Get a list of the 50 most recent jobs"
)
async def get_all_jobs(
    db: Session = Depends(get_db)
) -> List[JobStatusResponse]:
    def get_all_jobs_sync(db: Session) -> List[JobModel]:
        return db.query(JobModel).order_by(JobModel.id.desc()).limit(50).all()

    jobs: List[JobModel] = await run_in_threadpool(get_all_jobs_sync, db)
    logger.info(f"Fetched {len(jobs)} recent jobs for dashboard.")

    return [
        JobStatusResponse(
            job_id=int(job.id),
            job_type=str(job.job_type),
            status=JobStatus(job.status),
            retries=int(job.retries or 0),
            created_at=job.created_at if isinstance(job.created_at, datetime) else datetime.utcnow(),
            updated_at=job.updated_at if isinstance(job.updated_at, datetime) else datetime.utcnow(),
            result=dict(job.result) if job.result else None,
            error_message=job.error_message if isinstance(job.error_message, (str, dict)) else None
        )
        for job in jobs
    ]