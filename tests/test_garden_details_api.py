import os
import time
import requests
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

@pytest.fixture(scope="module")
def test_user():
    email = f"testuser_{int(time.time())}@example.com"
    response = requests.post(f"{BASE_URL}/auth/email", json={"email": email})
    assert response.status_code == 200
    return response.json()

def test_garden_details_api(test_user):
    # 1. Create a garden with a photo
    user_id = test_user["user_id"]
    with open("sample.jpeg", "rb") as f:
        files = {"photos": ("sample.jpeg", f, "image/jpeg")}
        data = {"user_id": user_id, "garden_name": "My Test Garden"}
        response = requests.post(f"{BASE_URL}/gardens/upload", files=files, data=data)
    
    assert response.status_code == 200
    garden_data = response.json()
    garden_id = garden_data["id"]
    assert garden_id is not None

    # 2. Poll the processing job until it's complete
    timeout = 300  # 5 minutes
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = requests.post(f"{BASE_URL}/jobs/process", params={"stream": "false"})
        if response.status_code == 200:
            # Check garden status
            status_response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
            if status_response.status_code == 200 and status_response.json().get("status") == "Ready":
                break
        time.sleep(10)
    else:
        pytest.fail("Garden processing timed out")

    # 3. Fetch the garden details
    response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
    assert response.status_code == 200
    details = response.json()

    # 4. Assert that the new fields are present and the recommendation is truncated
    assert "pest_presence" in details
    assert "weed_presence" in details
    assert "flowering_status" in details
    assert "full_recommendation" in details
    
    if details["recommendation"]:
        assert len(details["recommendation"].split()) <= 11 # 10 words + ellipsis
        assert details["recommendation"].endswith("...")
        assert details["full_recommendation"] is not None
        assert len(details["full_recommendation"].split()) > 10

    # 5. Cleanup
    delete_response = requests.delete(f"{BASE_URL}/gardens/{garden_id}")
    assert delete_response.status_code == 200
