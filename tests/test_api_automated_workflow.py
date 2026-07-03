import os
import requests
import time
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
if BASE_URL.endswith("/"):
    BASE_URL = BASE_URL[:-1]

@pytest.fixture(scope="module")
def test_user():
    """Fixture to create a new user for the test session."""
    email = f"testuser_{int(time.time())}@example.com"
    response = requests.post(f"{BASE_URL}/auth/email", json={"email": email})
    assert response.status_code == 200
    return response.json()

def test_automated_garden_workflow(test_user):
    """
    Tests the full automated workflow from photo upload to garden readiness.
    1. Uploads a photo to create a new garden.
    2. Polls the garden details endpoint until processing is complete.
    3. Verifies the final garden status and structure of the response.
    """
    user_id = test_user["user_id"]
    garden_name = f"Automated Test Garden {int(time.time())}"

    # 1. Upload photo to create a new garden
    with open("tests/sample.jpg", "rb") as f:
        files = {"photos": ("sample.jpg", f, "image/jpeg")}
        data = {"user_id": user_id, "garden_name": garden_name}
        response = requests.post(f"{BASE_URL}/gardens/upload", files=files, data=data)

    assert response.status_code == 200
    upload_data = response.json()
    assert "id" in upload_data
    assert "workflow_id" in upload_data
    garden_id = upload_data["id"]

    # 2. Poll for garden status
    timeout = 300  # 5 minutes
    start_time = time.time()
    garden_status = ""
    garden_data = {}

    while time.time() - start_time < timeout:
        response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
        if response.status_code == 200:
            garden_data = response.json()
            garden_status = garden_data.get("status")
            if garden_status == "Ready":
                break
        time.sleep(10)

    # 3. Verify the final state
    assert garden_status == "Ready", f"Garden did not become 'Ready' within {timeout} seconds."
    
    assert garden_data["id"] == garden_id
    assert garden_data["name"] == garden_name
    assert "plants" in garden_data
    assert isinstance(garden_data["plants"], list)
    assert "healthOverview" in garden_data
    assert "visualization" in garden_data

