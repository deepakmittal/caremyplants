import os
import requests
import time
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

@pytest.fixture(scope="module")
def test_garden():
    # 1. Create a new garden
    with open("sample.jpeg", "rb") as f:
        files = {"photos": ("sample.jpeg", f, "image/jpeg")}
        data = {"garden_name": "Test Garden for Details API"}
        response = requests.post(f"{BASE_URL}/gardens/upload", files=files, data=data)
        assert response.status_code == 200
        garden_data = response.json()
        garden_id = garden_data["id"]

    # 2. Process the garden
    response = requests.post(f"{BASE_URL}/jobs/process?stream=false")
    assert response.status_code == 200

    # 3. Wait for processing to complete
    for _ in range(20): # 20 * 5s = 100s timeout
        time.sleep(5)
        response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
        if response.status_code == 200:
            details = response.json()
            if details.get("status") == "Ready":
                break
    
    yield garden_id

    # Teardown: Delete the garden
    response = requests.delete(f"{BASE_URL}/gardens/{garden_id}")
    assert response.status_code == 200

def test_get_garden_details(test_garden):
    garden_id = test_garden
    response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
    assert response.status_code == 200
    details = response.json()

    # Check for new boolean fields
    assert "needs_watering" in details
    assert "needs_fertilizer" in details
    assert "has_pests" in details
    assert "has_weeds" in details

    # Check for recommendation fields
    assert "recommendation" in details
    assert "recommendation_full" in details

    # Check that old fields are gone
    assert "immediate_changes" not in details
    assert "disease_overview" not in details
    assert "growth_trend" not in details

    # Check recommendation truncation
    if details["recommendation_full"]:
        full_rec_words = details["recommendation_full"].split()
        if len(full_rec_words) > 10:
            assert details["recommendation"].endswith("...")
        else:
            assert details["recommendation"] == details["recommendation_full"]
