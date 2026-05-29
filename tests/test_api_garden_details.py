import os
import requests
import pytest
from datetime import datetime

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

@pytest.fixture(scope="module")
def test_user():
    email = f"testuser_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"
    response = requests.post(f"{BASE_URL}/auth/email", json={"email": email})
    assert response.status_code == 200
    return response.json()

@pytest.fixture(scope="module")
def test_garden(test_user):
    user_id = test_user["user_id"]
    response = requests.post(
        f"{BASE_URL}/gardens/upload",
        files={"photos": ("test.jpg", b"test_image_content", "image/jpeg")},
        data={"garden_name": "Test Garden for Details", "user_id": user_id},
    )
    assert response.status_code == 200
    return response.json()

def test_get_garden_details_enhanced(test_user, test_garden):
    garden_id = test_garden["id"]

    # The garden is created, but the test database is likely empty,
    # so we can't assume plants or plant_updates exist yet.
    # For a real integration test, we would need to create them.
    # However, without an endpoint to create plants and plant_updates directly,
    # we can only test the structure of the response for a garden with no plants.

    response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == garden_id
    assert data["name"] == "Test Garden for Details"
    assert "status" in data
    assert "created_at" in data
    assert "plants" in data
    assert isinstance(data["plants"], list)

    # If there were plants, we would test this:
    if data["plants"]:
        plant = data["plants"][0]
        assert "id" in plant
        assert "name" in plant
        assert "plant_variety" in plant
        assert "image_url" in plant
        assert "recommendation" in plant
        assert "recommendation_details" in plant
        assert "health_score" in plant
        assert "growth_stage" in plant
        assert "pest_issue" in plant
        assert "disease_issue" in plant
        assert "last_update_date" in plant
