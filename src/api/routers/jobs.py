from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session
from ..models.job import JobSubmission # This is the Pydantic model
from ..core.database import get_db # This is the database dependency
from ..models.sql_models.job import Job as JobModel # This is the SQLAlchemy model

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

    print(f"Received job of type: {job.job_type} with payload: {job.payload}")
    return {"message": "Job received successfully", "job_type": job.job_type}