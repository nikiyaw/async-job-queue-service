from fastapi.testclient import TestClient
from src.api.main import app
import time

from unittest.mock import patch
from sqlalchemy.orm import Session
from src.api.models.sql_models.job import Job as JobModel


def test_read_root(client: TestClient):
    # Make a GET request to the root endpoint
    response = client.get("/")
    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200
    # Assert that the response JSON matches our expected output
    assert response.json() == {"message": "Welcome to the Job Queue Service!"}

def test_submit_job(client: TestClient):
    # Define a sample job payload
    job_payload = {
        "job_type": "send_email",
        "payload": {
            "recipient_email": "test@example.com",
            "subject": "Hello from FastAPI!",
            "body": "This is a test email."
        }
    }
    # Make a POST request to the root endpoint
    response = client.post("/jobs/submit", json=job_payload)
    # Assert that the response status code is 201 (Created)
    assert response.status_code == 201
    # Assert that the response JSON matches our expected output
    # Corrected assertion: Expect the 'job_id' field.
    expected_response = {
        "message": "Job received successfully",
        "job_id": response.json()["job_id"], # Get the dynamically generated job ID from the response
        "job_type": "send_email"
    }
    # Assert that the response JSON matches our expected output
    assert response.json() == expected_response

def test_job_status(client: TestClient, db: Session):
    # Submit a new job to start the process
    job_payload = {
        "job_type": "long_calculation",
        "payload": {}
    }

    # Mock the Celery task
    with patch("src.worker.celery_worker.celery_app.send_task") as mock_delay:
        submit_response = client.post("/jobs/submit", json=job_payload)
        job_id = submit_response.json()["job_id"]
        # Assert that the Celery task was called with the correct arguments
        mock_delay.assert_called_once_with("src.worker.celery_worker.process_job", args=[job_id], queue="job_queue")
    
    try:
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        assert job.status == "queued"
        # Manually change the status to simulate the worker completing the job
        job.status = "completed"
        db.commit()
    finally:
        pass

    # Check the status again, expecting 'completed'
    status_response_completed = client.get(f"/jobs/status/{job_id}")
    assert status_response_completed.status_code == 200
    assert status_response_completed.json()["status"] == "completed"

def test_job_not_found(client: TestClient):
    # Test a non-existent job ID
    response = client.get("/jobs/status/99999") # ID that shouldn't exist
    assert response.status_code == 404
    assert response.json() == {"detail": "Job with ID 99999 not found."}