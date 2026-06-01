import os
import requests
import pytest

BASE_URL = os.environ.get("BASE_URL")

@pytest.fixture(scope="module")
def base_url():
    if not BASE_URL:
        pytest.fail("BASE_URL environment variable is not set.")
    return BASE_URL

def test_get_garden_details_v2(base_url):
    # Assuming garden with ID 1 exists and has been processed
    garden_id = 1
    response = requests.get(f"{base_url}/gardens/{garden_id}/details")
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert "id" in data
    assert "name" in data
    assert "status" in data
    assert "recommendation" in data
    assert "recommendation_full" in data
    assert "needs_watering" in data
    assert "needs_fertilizer" in data
    assert "has_pests" in data
    assert "has_weeds" in data
    assert "has_disease" in data
    assert "needs_sunlight" in data
    assert "created_at" in data
    assert "plants" in data
    
    # Check that summary is not in the response
    assert "summary" not in data
    
    # Check recommendation truncation
    if data["recommendation_full"]:
        words = data["recommendation_full"].split()
        if len(words) > 10:
            assert data["recommendation"].endswith("...")
        else:
            assert data["recommendation"] == data["recommendation_full"]
