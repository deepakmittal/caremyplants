import os
import requests
import time
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
GARDEN_ID = 1  # Assuming a garden with ID 1 exists for testing

def test_generate_garden_visualization():
    """
    Test the garden visualization endpoint.
    Triggers the visualization and polls the details endpoint to check the result.
    """
    # Step 1: Trigger the visualization generation
    visualize_url = f"{BASE_URL}/gardens/{GARDEN_ID}/visualize"
    response = requests.post(visualize_url)
    assert response.status_code == 202
    job_data = response.json()
    assert "job_id" in job_data
    assert job_data["status"] == "queued"

    # Step 2: Poll the details endpoint to check for the result
    details_url = f"{BASE_URL}/gardens/{GARDEN_ID}/details"
    max_retries = 15
    retry_interval = 2  # seconds
    for i in range(max_retries):
        response = requests.get(details_url)
        if response.status_code == 200:
            details_data = response.json()
            if details_data.get("visualization") is not None:
                # Visualization is ready, validate the structure
                vis_data = details_data["visualization"]
                assert "image_url" in vis_data
                assert "recommendations" in vis_data
                assert isinstance(vis_data["recommendations"], list)
                if vis_data["recommendations"]:
                    recommendation = vis_data["recommendations"][0]
                    assert "title" in recommendation
                    assert "reason" in recommendation
                    assert "product_url" in recommendation
                    assert "image_url" in recommendation
                return  # Test successful
        time.sleep(retry_interval)
    
    pytest.fail("Timed out waiting for garden visualization to be generated.")

