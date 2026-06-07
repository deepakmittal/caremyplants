import os
import requests
import pytest

BASE_URL = os.environ.get("BASE_URL", "https://caremyplants-dev1-ch4p6cqrla-uc.a.run.app")

def test_get_garden_details_summary():
    """
    Test the garden details endpoint to ensure it returns the summary and photos,
    and does not return the old textual details.
    """
    garden_id = 1
    url = f"{BASE_URL}/gardens/{garden_id}/details"
    
    response = requests.get(url)
    
    assert response.status_code == 200
    
    data = response.json()
    
    # Check for new fields
    assert "summary" in data
    assert "photos" in data
    
    # Check the types of the new fields
    assert isinstance(data["summary"], str) or data["summary"] is None
    assert isinstance(data["photos"], list)
    
    # Check that old fields are removed
    assert "recommendation" not in data
    assert "recommendation_full" not in data
    assert "needs_watering" not in data
    assert "needs_fertilizer" not in data
    assert "has_pests" not in data
    assert "has_weeds" not in data
    assert "has_disease" not in data
    assert "needs_sunlight" not in data
    
    # Check for other expected fields
    assert "id" in data
    assert "name" in data
    assert "status" in data
    assert "created_at" in data
    assert "plants" in data
    
    assert data["id"] == garden_id
