import os
import requests
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

def test_get_garden_details_with_plant_status_tickers():
    garden_id = 1  # Assuming a garden with ID 1 exists
    response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert "plant_status_tickers" in data
    
    tickers = data["plant_status_tickers"]
    assert isinstance(tickers, list)
    
    # Check that all items in the list are strings
    if tickers:
        assert all(isinstance(item, str) for item in tickers)
