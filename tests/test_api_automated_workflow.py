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
async def test_automated_garden_workflow_with_visualization():
    """
    Tests the automated garden processing workflow, including visualization.
    1. Uploads a photo to trigger the workflow.
    2. Polls for the garden to become "Ready".
    3. Verifies that a visualization with an image_url is generated.
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
        details_json = None
        for _ in range(20):  # Poll for up to 100 seconds
            time.sleep(5)
            details_response = await client.get(f"{BASE_URL}/gardens/{garden_id}/details")
            if details_response.status_code == 200:
                details_json = details_response.json()
                if details_json.get("status") == "Ready":
                    break
        else:
            pytest.fail("Garden did not become 'Ready' within the timeout period.")

        # 3. Verify that a visualization with an image_url is generated.
        assert details_json is not None
        assert "visualization" in details_json
        assert details_json["visualization"] is not None
        assert "image_url" in details_json["visualization"]
        assert details_json["visualization"]["image_url"] is not None

# Cleanup the dummy image file
os.remove("dummy_image.jpg")
