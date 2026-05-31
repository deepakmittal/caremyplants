import os
import requests
import time
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

@pytest.fixture(scope="module")
def test_data():
    return {
        "garden_id": None,
        "update_id": None,
    }

def test_create_garden_and_upload_photo(test_data):
    """
    Tests creating a garden and uploading a photo.
    """
    # Create a user
    email = "testuser@example.com"
    response = requests.post(f"{BASE_URL}/auth/email", json={"email": email})
    assert response.status_code == 200
    user_id = response.json()["user_id"]

    # Create a garden
    response = requests.post(
        f"{BASE_URL}/gardens/upload",
        files={"photos": ("test.jpg", open("sample.jpeg", "rb"), "image/jpeg")},
        data={"user_id": user_id},
    )
    assert response.status_code == 200
    garden_data = response.json()
    test_data["garden_id"] = garden_data["id"]
    test_data["update_id"] = garden_data["garden_update_id"]
    assert test_data["garden_id"] is not None
    assert test_data["update_id"] is not None

def test_process_garden(test_data):
    """
    Tests triggering the garden processing.
    """
    assert test_data["garden_id"] is not None
    response = requests.post(f"{BASE_URL}/jobs/process?stream=false")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_get_garden_details(test_data):
    """
    Tests getting the garden details and checks for the new fields.
    """
    assert test_data["garden_id"] is not None
    garden_id = test_data["garden_id"]

    # Poll for status change
    for _ in range(20):  # Poll for 200 seconds max
        response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
        if response.status_code == 200 and response.json().get("status") == "Ready":
            break
        time.sleep(10)
    
    assert response.status_code == 200
    details = response.json()
    assert details["status"] == "Ready"
    assert "pest_presence" in details
    assert "weed_presence" in details
    assert "flowering_status" in details
    assert "recommendation_full" in details
    assert details["recommendation"] is not None
    assert len(details["recommendation"].split()) <= 10
    assert details["recommendation_full"] is not None
    assert len(details["recommendation_full"].split()) > 10
