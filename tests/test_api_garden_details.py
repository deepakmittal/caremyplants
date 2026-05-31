import os
import time
import requests
import pytest

BASE_URL = os.environ.get("BASE_URL", "https://caremyplants-dev4-ch4p6cqrla-ew.a.run.app")

@pytest.fixture(scope="module")
def test_image_path():
    return "sample.jpeg"

def test_create_garden_and_get_details(test_image_path):
    # 1. Create a new user
    email = f"testuser_{int(time.time())}@example.com"
    response = requests.post(f"{BASE_URL}/auth/email", json={"email": email})
    assert response.status_code == 200
    user_id = response.json()["user_id"]

    # 2. Create a new garden
    with open(test_image_path, "rb") as f:
        files = {"photos": (test_image_path, f, "image/jpeg")}
        data = {"user_id": user_id, "garden_name": "My Test Garden"}
        response = requests.post(f"{BASE_URL}/gardens/upload", files=files, data=data)
    
    assert response.status_code == 200
    garden_id = response.json()["id"]

    # 3. Poll for garden details until processing is complete
    timeout = 300  # 5 minutes
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "Ready":
                break
        time.sleep(10)
    else:
        pytest.fail("Garden processing timed out")

    # 4. Assert the structure of the response
    assert "id" in data
    assert "name" in data
    assert "status" in data
    assert "summary" in data
    assert "recommendation" in data
    assert "recommendation_show_more" in data
    assert "has_pests" in data
    assert "has_weeds" in data
    assert "is_overwatered" in data
    assert "is_underwatered" in data
    assert "created_at" in data
    assert "plants" in data

    # 5. Assert the types of the new fields
    assert isinstance(data["recommendation_show_more"], bool)
    assert isinstance(data["has_pests"], bool)
    assert isinstance(data["has_weeds"], bool)
    assert isinstance(data["is_overwatered"], bool)
    assert isinstance(data["is_underwatered"], bool)

    # 6. Assert that the recommendation is truncated
    assert len(data["recommendation"].split()) <= 10
