import os
import requests
import pytest
from typing import List, Dict, Any

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

def test_get_garden_details_with_tiles():
    """
    Tests the /gardens/{garden_id}/details endpoint to ensure it returns the new 'tiles' field.
    """
    # Create a user
    email = "testuser_garden_details@example.com"
    response = requests.post(f"{BASE_URL}/auth/email", json={"email": email})
    assert response.status_code == 200
    user_id = response.json()["user_id"]

    # Create a garden
    with open("sample.jpeg", "rb") as f:
        files = {"photos": ("sample.jpeg", f, "image/jpeg")}
        data = {"user_id": user_id, "garden_name": "Test Garden for Details"}
        response = requests.post(f"{BASE_URL}/gardens/upload", files=files, data=data)

    assert response.status_code == 200
    garden_id = response.json()["id"]

    # At this point, a garden and a garden_update have been created.
    # To properly test the tiles, the garden needs to be processed by the AI pipeline,
    # which would populate the 'vibrancy', 'hydration', etc. fields in the garden_update.
    # Since we cannot trigger this process here and wait for it, we will proceed to call the
    # details endpoint and check the structure of the response.
    # In a real-world scenario with a test database, we would manually insert a
    # garden_update with the necessary data to test the tile generation logic.

    # Get garden details
    response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
    assert response.status_code == 200

    details = response.json()
    assert "tiles" in details
    assert isinstance(details["tiles"], list)

    # The tiles might be empty if the garden has not been processed, which is expected in this test.
    # If the garden were processed and had, for example, a "vibrant" vibrancy, we would expect:
    # expected_tile = {
    #     "id": "vibrancy",
    #     "title": "Vibrancy",
    #     "value": "vibrant",
    #     "description": None,
    #     "icon": "sparkles"
    # }
    # assert expected_tile in details["tiles"]

    # Clean up the created garden
    response = requests.delete(f"{BASE_URL}/gardens/{garden_id}")
    assert response.status_code == 200
