import os
import httpx
import pytest
import time

BASE_URL = os.environ.get("BASE_URL")
if not BASE_URL:
    raise ValueError("BASE_URL environment variable not set")

# Create a dummy image file for testing
DUMMY_IMAGE_CONTENT = b"dummy image content"
with open("dummy_image.jpg", "wb") as f:
    f.write(DUMMY_IMAGE_CONTENT)

@pytest.mark.asyncio
async def test_automated_garden_workflow():
    """
    Tests the new automated garden processing workflow.
    1. Verifies that uploading photos triggers the workflow.
    2. Verifies that the old, manual-trigger endpoints are removed.
    """
    async with httpx.AsyncClient() as client:
        # 1. Test the new automated workflow via /gardens/upload
        files = {"photos": ("dummy_image.jpg", DUMMY_IMAGE_CONTENT, "image/jpeg")}
        data = {"garden_name": "My Automated Test Garden"}
        
        response = await client.post(f"{BASE_URL}/gardens/upload", files=files, data=data)
        
        assert response.status_code == 200
        response_json = response.json()
        assert "id" in response_json
        assert "workflow_id" in response_json
        assert response_json["name"] == "My Automated Test Garden"
        
        garden_id = response_json["id"]

        # Poll for garden status to become "Ready"
        for _ in range(10):  # Poll for up to 50 seconds
            time.sleep(5)
            details_response = await client.get(f"{BASE_URL}/gardens/{garden_id}/details")
            if details_response.status_code == 200:
                details_json = details_response.json()
                if details_json.get("status") == "Ready":
                    break
        else:
            pytest.fail("Garden did not become 'Ready' within the timeout period.")

        # 2. Verify that the old endpoints are removed (return 404)
        
        # Check POST /jobs/process
        response_jobs_post = await client.post(f"{BASE_URL}/jobs/process")
        assert response_jobs_post.status_code == 404

        # Check GET /jobs/process
        response_jobs_get = await client.get(f"{BASE_URL}/jobs/process")
        assert response_jobs_get.status_code == 404

        # Check POST /gardens/{garden_id}/visualize
        response_visualize = await client.post(f"{BASE_URL}/gardens/{garden_id}/visualize")
        assert response_visualize.status_code == 404

# Cleanup the dummy image file
os.remove("dummy_image.jpg")
