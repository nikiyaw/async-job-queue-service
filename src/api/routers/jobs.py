from fastapi import APIRouter, status
from ..models.job import JobSubmission

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

@router.post("/submit", status_code=status.HTTP_201_CREATED)
def submit_job(job: JobSubmission):
    print(f"Received job of type: {job.job_type} with payload: {job.payload}")
    return {"message": "Job received successfully", "job_type": job.job_type}