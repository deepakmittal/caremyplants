import os
import requests
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

def test_create_garden_with_default_name():
    """
    Tests that creating a garden without a name defaults to 'My Gardens'.
    """
    url = f"{BASE_URL}/gardens/upload"
    
    # Create a dummy file to upload
    with open("test_image.jpg", "w") as f:
        f.write("This is a test image.")

    with open("test_image.jpg", "rb") as f:
        files = {'photos': ('test_image.jpg', f, 'image/jpeg')}
        response = requests.post(url, files=files)

    # Clean up the dummy file
    os.remove("test_image.jpg")

    assert response.status_code == 200
    garden_data = response.json()
    assert "id" in garden_data
    assert garden_data["name"] == "My Gardens"

    # Verify the garden was created by fetching it
    garden_id = garden_data["id"]
    response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
    assert response.status_code == 200
    garden_details = response.json()
    assert garden_details["name"] == "My Gardens"

    # Cleanup: delete the created garden
    delete_response = requests.delete(f"{BASE_URL}/gardens/{garden_id}")
    assert delete_response.status_code == 200
