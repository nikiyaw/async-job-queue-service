from fastapi import FastAPI, HTTPException, status
from src.api.models import JobSubmission

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Job Queue Service!"}

@app.post("/jobs/submit", status_code=status.HTTP_201_CREATED)
def submit_job(job: JobSubmission):
    # In Week 2, we will add the logic to store this job in the database
    # and add it to the message queue. For now, we'll just return a success message.
    print(f"Received job of type: {job.job_type} with payload: {job.payload}")
    return {"message": "Job received successfully", "job_type": job.job_type}