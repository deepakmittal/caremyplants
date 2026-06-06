import os
import requests
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

def test_get_garden_details_v2():
    """
    Test the refactored garden details endpoint to ensure it returns tickers,
    a truncated summary, and other expected fields.
    """
    garden_id = 1  # Assuming a garden with ID 1 exists for testing
    response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")

    assert response.status_code == 200

    data = response.json()

    # 1. Check for the existence of key fields
    assert "id" in data
    assert "name" in data
    assert "summary" in data
    assert "photo_url" in data
    assert "tickers" in data
    assert "plants" in data
    assert "created_at" in data

    # 2. Validate the data types
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert (data["summary"] is None or isinstance(data["summary"], str))
    assert (data["photo_url"] is None or isinstance(data["photo_url"], str))
    assert isinstance(data["tickers"], list)
    assert isinstance(data["plants"], list)

    # 3. Validate the summary truncation (max 10 words)
    if data["summary"]:
        summary_words = data["summary"].split()
        # The truncated summary might end with "...", so we check for <= 11 words
        assert len(summary_words) <= 11 

    # 4. Validate the structure of tickers
    for ticker in data["tickers"]:
        assert "label" in ticker
        assert "value" in ticker
        assert isinstance(ticker["label"], str)
        assert isinstance(ticker["value"], str)

    # 5. Validate the structure of plants list
    if data["plants"]:
        plant = data["plants"][0]
        assert "id" in plant
        assert "name" in plant
        assert "plant_variety" in plant
        assert "image_url" in plant
        assert "latest_condition" in plant
        assert "latest_recommendation" in plant
        assert "last_update_date" in plant

    # 6. Check that old, removed fields are not present
    assert "recommendation" not in data
    assert "recommendation_full" not in data
    assert "needs_watering" not in data
    assert "has_pests" not in data

if __name__ == "__main__":
    pytest.main()
