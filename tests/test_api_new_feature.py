import os
import time
import requests
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

@pytest.fixture(scope="module")
def test_user():
    email = "testuser@example.com"
    response = requests.post(f"{BASE_URL}/auth/email", json={"email": email})
    assert response.status_code == 200
    return response.json()

def test_garden_details_new_feature(test_user):
    # Create a garden
    garden_name = "My Test Garden"
    user_id = test_user["user_id"]
    with open("sample.jpeg", "rb") as f:
        files = {"photos": ("sample.jpeg", f, "image/jpeg")}
        data = {"name": garden_name, "user_id": user_id}
        response = requests.post(f"{BASE_URL}/gardens", files=files, data=data)
    
    assert response.status_code == 200
    garden = response.json()
    garden_id = garden["id"]

    # Trigger processing
    response = requests.post(f"{BASE_URL}/jobs/process?stream=false")
    assert response.status_code == 200

    # Poll for status
    for _ in range(30):
        response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
        if response.status_code == 200 and response.json()["status"] == "Ready":
            break
        time.sleep(10)
    
    assert response.status_code == 200
    details = response.json()
    assert details["status"] == "Ready"

    # Check for new fields
    assert "needs_water" in details
    assert "pest_detected" in details
    assert "low_sunlight" in details
    assert "short_recommendation" in details
    assert "full_recommendation" in details

    # Clean up
    response = requests.delete(f"{BASE_URL}/gardens/{garden_id}")
    assert response.status_code == 200
