from fastapi.testclient import TestClient
from src.api.main import app

# Create a test client
client = TestClient(app)

def test_read_root():
    # Make a GET request to the root endpoint
    response = client.get("/")

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # Assert that the response JSON matches our expected output
    assert response.json() == {"message": "Welcome to the Job Queue Service!"}

def test_submit_job():
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