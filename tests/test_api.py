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