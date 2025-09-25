from fastapi.testclient import TestClient
from src.api.main import app
import time

from unittest.mock import patch
from sqlalchemy.orm import Session
from src.api.models.sql_models.job import Job as JobModel


def test_read_root(client: TestClient):
    """
    Tests the root endpoint of the API.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Job Queue Service!"}

def test_submit_job(client: TestClient):
    """
    Tests submitting a new job and receiving a valid response with a 201 status code.
    """
    job_payload = {
        "job_type": "send_email",
        "payload": {
            "recipient_email": "test@example.com",
            "subject": "Hello from FastAPI!",
            "body": "This is a test email."
        }
    }
    response = client.post("/jobs/submit", json=job_payload)
    assert response.status_code == 201
    expected_response = {
        "message": "Job received successfully",
        "job_id": response.json()["job_id"], # Get the dynamically generated job ID from the response
        "job_type": "send_email"
    }
    assert response.json() == expected_response

def test_job_status(client: TestClient, db_session: Session):
    """
    Tests retrieving the status of a job and simulating a status change by a worker.
    """
    job_payload = {
        "job_type": "long_calculation",
        "payload": {}
    }
    # Mock the Celery task to prevent it from actually being called
    with patch("src.worker.celery_worker.celery_app.send_task") as mock_delay:
        submit_response = client.post("/jobs/submit", json=job_payload)
        job_id = submit_response.json()["job_id"]
        mock_delay.assert_called_once_with("src.worker.celery_worker.process_job", args=[job_id], queue="job_queue")
    
    try:
        job = db_session.query(JobModel).filter(JobModel.id == job_id).first()
        assert job.status == "queued"
        job.status = "completed"
        db_session.commit()
    finally:
        pass

    status_response_completed = client.get(f"/jobs/status/{job_id}")
    assert status_response_completed.status_code == 200
    assert status_response_completed.json()["status"] == "completed"

def test_job_not_found(client: TestClient):
    """
    Tests a non-existent job ID to ensure a 404 is returned with a specific message.
    """
    response = client.get("/jobs/status/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Job with ID 99999 not found."}

def test_malformed_payload(client: TestClient):
    """
    Tests an invalid job submission payload to ensure a 422 Unprocessable Entity is returned.
    """
    invalid_payload = {
        "job_type": "send_email",
        "payload": "this is not a dictionary"
    }
    response = client.post("/jobs/submit", json=invalid_payload)
    assert response.status_code == 422