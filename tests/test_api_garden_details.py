import os
import requests
import time

BASE_URL = os.environ.get("BASE_URL")
TEST_USER_EMAIL = "test@example.com"

def test_get_garden_details_with_tiles():
    # 1. Create a user
    response = requests.post(f"{BASE_URL}/auth/email", json={"email": TEST_USER_EMAIL})
    assert response.status_code == 200
    user_id = response.json()["user_id"]

    # 2. Create a garden
    with open("/app/garden/sample.jpeg", "rb") as f:
        files = {"photos": ("sample.jpeg", f, "image/jpeg")}
        response = requests.post(f"{BASE_URL}/gardens/upload", files=files, data={"user_id": user_id})

    assert response.status_code == 200
    garden_id = response.json()["id"]
    garden_update_id = response.json()["garden_update_id"]

    # 3. Trigger processing
    response = requests.post(f"{BASE_URL}/jobs/process?stream=false")
    assert response.status_code == 200

    # 4. Poll for status
    for _ in range(20):
        response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
        if response.status_code == 200 and response.json()["status"] == "Ready":
            break
        time.sleep(5)
    
    assert response.status_code == 200
    assert response.json()["status"] == "Ready"

    # 5. Check for tiles
    details = response.json()
    assert "tiles" in details
    
    # This is a bit of a guess, but let's assume the sample image is vibrant
    assert len(details["tiles"]) > 0
    
    tile_names = [tile["name"] for tile in details["tiles"]]
    assert "Vibrancy" in tile_names
    assert "Hydration" in tile_names
    assert "Exposure" in tile_names
