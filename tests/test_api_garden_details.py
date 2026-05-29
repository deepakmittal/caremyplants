import os
import requests
import pytest
import uuid

BASE_URL = os.environ.get("BASE_URL")
if not BASE_URL:
    raise ValueError("BASE_URL environment variable not set")

@pytest.fixture(scope="module")
def test_user():
    """Fixture to create a user for the tests."""
    email = f"testuser_{uuid.uuid4()}@example.com"
    response = requests.post(f"{BASE_URL}/auth/email", json={"email": email})
    response.raise_for_status()
    return response.json()

@pytest.fixture(scope="module")
def test_garden(test_user):
    """Fixture to create a garden for the tests."""
    garden_name = "My Test Garden for Details"
    files = {'photos': ('test.jpg', b'fake_image_data', 'image/jpeg')}
    data = {'name': garden_name, 'user_id': test_user['user_id']}
    response = requests.post(f"{BASE_URL}/gardens", files=files, data=data)
    response.raise_for_status()
    return response.json()

def test_get_garden_details_has_tiles_key(test_garden):
    """
    Tests that the /gardens/{garden_id}/details endpoint response
    includes the 'tiles' key.
    """
    garden_id = test_garden["id"]
    
    # Get garden details
    response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
    response.raise_for_status()
    
    garden_details = response.json()
    
    # Assert that the 'tiles' key is in the response
    assert "tiles" in garden_details
    # Initially, the tiles list will be empty because the scores are not set.
    # This test just ensures the API change is present.
    assert isinstance(garden_details["tiles"], list)

# Note: A more comprehensive test would involve seeding the database
# with a GardenUpdate that has beauty_score and color_score set,
# and then asserting that the tiles are generated correctly.
# This is not possible in the current testing setup without direct DB access.
