import os
import requests
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

@pytest.fixture(scope="module")
def test_user():
    email = "testuser_tickers@example.com"
    response = requests.post(f"{BASE_URL}/auth/email", json={"email": email})
    assert response.status_code == 200
    return response.json()

@pytest.fixture(scope="module")
def test_garden(test_user):
    user_id = test_user["user_id"]
    garden_name = "Test Garden for Tickers"
    
    # Create a dummy file for upload
    with open("test_image.jpg", "w") as f:
        f.write("test image data")

    with open("test_image.jpg", "rb") as f:
        files = {"photos": ("test_image.jpg", f, "image/jpeg")}
        data = {"garden_name": garden_name, "user_id": user_id}
        response = requests.post(f"{BASE_URL}/gardens/upload", files=files, data=data)
    
    os.remove("test_image.jpg")
    
    assert response.status_code == 200
    return response.json()

def test_get_plant_status_tickers(test_garden):
    garden_id = test_garden["id"]
    response = requests.get(f"{BASE_URL}/gardens/{garden_id}/plant_status_tickers")
    
    assert response.status_code == 200
    
    tickers = response.json()
    assert isinstance(tickers, list)
    assert len(tickers) > 0
    
    expected_tickers = [
        {"status": "warning", "message": "Tomato plant showing signs of blight."},
        {"status": "success", "message": "Cucumbers are thriving."},
        {"status": "info", "message": "Basil is ready for harvest."},
    ]
    
    assert tickers == expected_tickers
