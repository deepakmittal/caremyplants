import os
import requests
import time

BASE_URL = os.environ.get("BASE_URL")

def test_get_garden_details_new_design():
    """
    Test the new design of the get_garden_details endpoint.
    1. Creates a new garden with a photo.
    2. Polls the details endpoint until processing is complete.
    3. Verifies the new response format.
    """
    # 1. Create a new garden
    with open("sample.jpeg", "rb") as f:
        files = {"photos": ("sample.jpeg", f, "image/jpeg")}
        response = requests.post(f"{BASE_URL}/gardens/upload", files=files)
    
    assert response.status_code == 200
    garden_id = response.json()["id"]

    # 2. Poll for completion
    for _ in range(30): # 30 * 5s = 150s timeout
        response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
        if response.status_code == 200 and response.json()["status"] == "Ready":
            break
        time.sleep(5)
    
    assert response.status_code == 200
    data = response.json()

    # 3. Verify the new response format
    assert "recommendation_short" in data
    assert "show_more" in data
    assert "tickers" in data
    assert isinstance(data["tickers"], list)

    # Check that old fields are gone
    assert "summary" not in data
    assert "immediate_changes" not in data
    assert "disease_overview" not in data
    assert "growth_trend" not in data
