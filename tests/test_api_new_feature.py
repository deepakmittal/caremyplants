import os
import requests
import pytest
from datetime import datetime

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

@pytest.fixture(scope="module")
def test_data():
    """Create a new garden and plant for testing."""
    # Create a user
    email = f"testuser_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"
    response = requests.post(f"{BASE_URL}/auth/email", json={"email": email})
    assert response.status_code == 200
    user_id = response.json()["user_id"]

    # Create a garden
    garden_name = f"Test Garden {datetime.now().strftime('%Y%m%d%H%M%S')}"
    with open("sample.jpeg", "rb") as f:
        files = {"photos": ("sample.jpeg", f, "image/jpeg")}
        data = {"name": garden_name, "user_id": user_id}
        response = requests.post(f"{BASE_URL}/gardens", files=files, data=data)
    
    assert response.status_code == 200
    garden_id = response.json()["id"]

    return {"user_id": user_id, "garden_id": garden_id}


def test_get_garden_details_enhanced_metrics(test_data):
    """
    Test the GET /gardens/{garden_id}/details endpoint with enhanced metrics.
    """
    garden_id = test_data["garden_id"]

    # The garden is created, now let's get the details
    response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
    assert response.status_code == 200

    data = response.json()

    # Check the new structure of the response
    assert "id" in data
    assert "name" in data
    assert "status" in data
    assert "created_at" in data
    assert "metrics" in data
    assert "plants" in data

    # Check that the old textual fields are removed
    assert "summary" not in data
    assert "recommendation" not in data
    assert "immediate_changes" not in data
    assert "disease_overview" not in data
    assert "growth_trend" not in data

    # Check the structure of the metrics
    if data["metrics"]:
        for metric in data["metrics"]:
            assert "name" in metric
            assert "value" in metric

    # Check the structure of the plants
    if data["plants"]:
        for plant in data["plants"]:
            assert "id" in plant
            assert "name" in plant
            assert "health_score" in plant
            assert "growth_stage" in plant
            assert "pest_issue" in plant
            assert "water_stress" in plant
            assert "latest_recommendation" in plant
            assert "detailed_recommendation" in plant
