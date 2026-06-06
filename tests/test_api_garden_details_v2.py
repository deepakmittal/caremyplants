import os
import httpx
import pytest

BASE_URL = os.environ.get("BASE_URL")
if not BASE_URL:
    raise ValueError("BASE_URL environment variable not set")

GARDEN_ID_TO_TEST = 1 

@pytest.mark.integration
def test_get_garden_details_new_format():
    """
    Tests the GET /gardens/{garden_id}/details endpoint for the new V2 response format.
    """
    # Arrange
    url = f"{BASE_URL}/gardens/{GARDEN_ID_TO_TEST}/details"
    
    # Act
    with httpx.Client() as client:
        response = client.get(url)
    
    # Assert
    # Check for successful response
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response: {response.text}"
    
    # Parse the JSON response
    data = response.json()
    
    # Verify the new V2 fields are present
    assert "id" in data
    assert "name" in data
    assert "summary" in data
    assert "photo_url" in data
    assert "tickers" in data
    assert "plants" in data
    
    # Verify the format of the new fields
    assert isinstance(data["summary"], (str, type(None))), "summary should be a string or null"
    if data["summary"] is not None:
        # Check if the summary is roughly 10 words
        assert len(data["summary"].split()) <= 11, "Summary should be around 10 words."

    assert isinstance(data["tickers"], list), "tickers should be a list"
    if data["tickers"]:
        for ticker in data["tickers"]:
            assert "label" in ticker
            assert "value" in ticker
            assert isinstance(ticker["label"], str)
            assert isinstance(ticker["value"], str)

    assert isinstance(data["plants"], list), "plants should be a list"

    # Verify that the old, removed fields are NOT present
    assert "recommendation" not in data
    assert "recommendation_full" not in data
    assert "needs_watering" not in data
    assert "needs_fertilizer" not in data
    assert "has_pests" not in data
    assert "has_weeds" not in data
    assert "has_disease" not in data
    assert "needs_sunlight" not in data

    print(f"Successfully validated new garden details format for garden ID {GARDEN_ID_TO_TEST}")
    print(f"Response JSON: {data}")

