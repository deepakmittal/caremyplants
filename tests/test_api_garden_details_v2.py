import os
import requests
import time
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

@pytest.fixture(scope="module")
def test_data():
    return {
        "garden_id": None,
        "user_id": 1 
    }

def test_create_garden_for_details_v2(test_data):
    """
    Create a new garden to test the details endpoint.
    """
    with open("sample.jpeg", "rb") as f:
        files = {"photos": ("sample.jpeg", f, "image/jpeg")}
        data = {"user_id": test_data["user_id"]}
        response = requests.post(f"{BASE_URL}/gardens/upload", files=files, data=data)
    
    assert response.status_code == 200
    garden_data = response.json()
    assert "id" in garden_data
    test_data["garden_id"] = garden_data["id"]

def test_get_garden_details_v2_processing(test_data):
    """
    Poll the garden details endpoint until the status is "Ready".
    """
    garden_id = test_data["garden_id"]
    timeout = 300  # 5 minutes
    start_time = time.time()

    while time.time() - start_time < timeout:
        response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "Ready":
                break
        time.sleep(10)
    
    assert data.get("status") == "Ready", "Garden processing timed out"

def test_get_garden_details_v2_response(test_data):
    """
    Check the response of the updated garden details endpoint.
    """
    garden_id = test_data["garden_id"]
    response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
    
    assert response.status_code == 200
    data = response.json()

    assert "id" in data
    assert "name" in data
    assert "status" in data
    assert "summary" in data
    assert "recommendation" in data
    assert "recommendation_full" in data
    assert "needs_watering" in data
    assert "needs_fertilizer" in data
    assert "has_pests" in data
    assert "has_weeds" in data
    assert "created_at" in data
    
    assert "plants" not in data

    if data["recommendation_full"]:
        words = data["recommendation_full"].split()
        if len(words) > 10:
            assert data["recommendation"] == " ".join(words[:10])
        else:
            assert data["recommendation"] == data["recommendation_full"]

def test_delete_garden_for_details_v2(test_data):
    """
    Delete the garden created for the test.
    """
    garden_id = test_data["garden_id"]
    response = requests.delete(f"{BASE_URL}/gardens/{garden_id}")
    assert response.status_code == 200
