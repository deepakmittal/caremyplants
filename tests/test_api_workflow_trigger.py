import os
import requests
import time
import pytest

BASE_URL = os.environ.get("BASE_URL")
if not BASE_URL:
    raise ValueError("BASE_URL environment variable not set")

@pytest.mark.asyncio
async def test_upload_garden_and_trigger_workflow():
    """
    Tests that uploading a garden photo automatically triggers the processing workflow.
    """
    # 1. Upload a photo to create a new garden
    with open("tests/test_image.jpg", "rb") as f:
        files = {"photos": ("test_image.jpg", f, "image/jpeg")}
        response = requests.post(f"{BASE_URL}/gardens/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "workflow_id" in data
    garden_id = data["id"]
    workflow_id = data["workflow_id"]
    assert workflow_id is not None

    # 2. Poll the garden details endpoint until the status is "Ready"
    timeout = 300  # 5 minutes
    start_time = time.time()
    while time.time() - start_time < timeout:
        details_response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
        if details_response.status_code == 200:
            details_data = details_response.json()
            if details_data.get("status") == "Ready":
                break
        time.sleep(10)
    else:
        pytest.fail("Garden processing timed out.")

    # 3. Assert that the garden has been processed and has plants
    details_response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
    assert details_response.status_code == 200
    details_data = details_response.json()
    assert details_data["status"] == "Ready"
    assert "plants" in details_data
    # The dummy image won't have any real plants, but the processing should complete.
    # We can't be sure if plants will be detected, so we don't assert on the number of plants.
