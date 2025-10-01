from fastapi.testclient import TestClient
from unittest.mock import patch
from sqlalchemy.orm import Session
from src.api.models.sql_models.job import Job as JobModel
from src.api.models.job import JobStatus


def test_read_root(client: TestClient):
    """
    Tests the root endpoint of the API (which serves the dashboard HTML).
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers['content-type'] == 'text/html; charset=utf-8'
    assert response.content.decode().startswith('<!DOCTYPE html>')

# --- New Test: Retrieve All Jobs for Dashboard Feed ---
def test_retrieve_all_jobs(client: TestClient):
    """
    Tests the GET /jobs/ endpoint, which powers the dashboard status feed.
    It submits a job and verifies it appears in the list of all jobs.
    """
    job_payload = {
        "job_type": "dashboard_check",
        "payload": {"data": 1}
    }

    # 1. Submit a job
    submit_response = client.post("/jobs/submit", json=job_payload)
    assert submit_response.status_code == 201
    job_id = submit_response.json()["job_id"]

    # 2. Retrieve all jobs
    all_jobs_response = client.get("/jobs/")
    assert all_jobs_response.status_code == 200

    jobs = all_jobs_response.json()

    # The API might return the list directly, or a dictionary wrapper like {"jobs": [...]}.
    # We test for the list structure, which is what the front-end expects.
    assert isinstance(jobs, list)
    assert len(jobs) > 0 # At least the job we submitted must be present

    # 3. Verify the submitted job's details are in the list
    found_job = next((job for job in jobs if job['job_id'] == job_id), None)
    assert found_job is not None
    assert found_job["job_type"] == "dashboard_check"
    assert found_job["status"] == JobStatus.QUEUED.value

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
        "job_id": response.json()["job_id"], 
        "job_type": "send_email",
        "status": JobStatus.QUEUED.value
    }
    # different 1
    assert response.json() == expected_response

def test_job_status(client: TestClient, db_session: Session):
    """
    Tests retrieving the status of a job and simulating a status change by a worker.
    This test ensures we can retrieve simple status changes.
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
    
    # Manually update status to processing
    job = db_session.query(JobModel).filter(JobModel.id == job_id).first()
    assert job.status == JobStatus.QUEUED.value
    job.status = JobStatus.PROCESSING.value
    db_session.commit()

    status_response_completed = client.get(f"/jobs/status/{job_id}")
    assert status_response_completed.status_code == 200
    assert status_response_completed.json()["status"] == JobStatus.PROCESSING.value

# --- New Test: Retrieve Final Result and Error Data ---
def test_job_final_result_and_error(client: TestClient, db_session: Session):
    """
    Tests that when a job is completed or failed, the API correctly returns 
    the result (JSONB) or error_message (string/JSONB) stored in the database.
    """
    job_payload = {"job_type": "final_data_set", "payload": {}}

    # Submit job 1 (will be completed)
    submit_response_1 = client.post("/jobs/submit", json=job_payload)
    job_id_1 = submit_response_1.json()["job_id"]

    # Submit job 2 (will be failed)
    submit_response_2 = client.post("/jobs/submit", json=job_payload)
    job_id_2 = submit_response_2.json()["job_id"]

    # 1. Simulate Completion and Result Storage (Job 1)
    job_1 = db_session.query(JobModel).filter(JobModel.id == job_id_1).first()
    job_1.status = JobStatus.COMPLETED.value
    final_result = {"calculation": 42, "user_id": 101}
    job_1.result = final_result
    db_session.commit()

    # Verify API returns the result
    status_response_completed = client.get(f"/jobs/status/{job_id_1}")
    assert status_response_completed.status_code == 200
    assert status_response_completed.json()["status"] == JobStatus.COMPLETED.value
    assert status_response_completed.json()["result"] == final_result
    assert status_response_completed.json()["error_message"] is None # Must be None

    # 2. Simulate Failure and Error Storage (Job 2)
    job_2 = db_session.query(JobModel).filter(JobModel.id == job_id_2).first()
    job_2.status = JobStatus.FAILED.value
    final_error = "Database connection timed out after 3 retries."
    job_2.error_message = final_error
    db_session.commit()

    # Verify API returns the error
    status_response_failed = client.get(f"/jobs/status/{job_id_2}")
    assert status_response_failed.status_code == 200
    assert status_response_failed.json()["status"] == JobStatus.FAILED.value
    assert status_response_failed.json()["error_message"] == final_error
    assert status_response_failed.json()["result"] is None # Must be None

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