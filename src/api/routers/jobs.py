from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models.job import JobSubmission # This is the Pydantic model
from ..core.database import get_db # This is the database dependency
from ..models.sql_models.job import Job as JobModel # This is the SQLAlchemy model
from ...worker.celery_worker import celery_app

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

@router.post("/submit", status_code=status.HTTP_201_CREATED)
def submit_job(job: JobSubmission, db: Session = Depends(get_db)):
    # Create a new Job instance from the Pydantic model
    db_job = JobModel(
        job_type=job.job_type,
        payload=job.payload,
        status="queued"
    )

    # Add the job to the session and commit it to the database
    db.add(db_job)
    db.commit()
    db.refresh(db_job) # To get the newly created ID

    # Add the job to the Celery queue by using a task from Celery app directly, which handles serialization
    task_name = "src.worker.celery_worker.process_job"
    celery_app.send_task(task_name, args=[db_job.id], queue="job_queue")

    print(f"Received job of type: {db_job.job_type} and persisted to DB with ID: {db_job.id}")
    return {"message": "Job received successfully", "job_id": db_job.id, "job_type": db_job.job_type}

@router.get("/status/{job_id}", status_code=status.HTTP_200_OK)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the status of a job from the database.
    """
    job = db.query(JobModel).filter(JobModel.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )
    return {"job_id": job.id, "status": job.status}

@router.get("/{job_id}/result", status_code=status.HTTP_200_OK)
def get_job_result(job_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the result of a completed job from the database.
    """
    job = db.query(JobModel).filter(JobModel.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )
    
    # Check if the job has been completed
    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job {job_id} is still in status '{job.status}'. The result is not yet available."
        )
    
    return {"job_id": job.id, "result": job.result}