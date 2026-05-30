import os
import requests
import pytest
from typing import Generator
import uuid

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

@pytest.fixture(scope="module")
def test_garden() -> Generator[int, None, None]:
    """
    Creates a new garden with a photo and returns the garden ID.
    Deletes the garden after the test.
    """
    garden_name = f"test_garden_{uuid.uuid4()}"
    with open("sample.jpeg", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/gardens",
            data={"name": garden_name},
            files={"photos": ("sample.jpeg", f, "image/jpeg")},
        )
    assert response.status_code == 200
    garden_id = response.json()["id"]
    yield garden_id
    response = requests.delete(f"{BASE_URL}/gardens/{garden_id}")
    assert response.status_code == 200


def test_get_garden_details_high_density(test_garden: int):
    """
    Tests the GET /gardens/{garden_id}/details endpoint with the new high-density metrics.
    """
    response = requests.get(f"{BASE_URL}/gardens/{test_garden}/details")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "name" in data
    assert "status" in data
    assert "created_at" in data
    assert "metrics" in data
    assert "plants" in data
    metrics = data["metrics"]
    assert "hydration" in metrics
    assert "exposure" in metrics
    assert "vibrancy" in metrics
    assert "plant_count" in metrics
    assert "species_count" in metrics
    assert "average_plant_health" in metrics
