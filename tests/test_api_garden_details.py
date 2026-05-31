import os
import requests
import time
from pathlib import Path

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

def test_get_garden_details_new_format():
    # Create a user
    email = f"testuser_{int(time.time())}@example.com"
    response = requests.post(f"{BASE_URL}/auth/email", json={"email": email})
    assert response.status_code == 200
    user_id = response.json()["user_id"]

    # Create a garden with a photo
    image_path = Path(__file__).parent.parent / "sample.jpeg"
    with open(image_path, "rb") as f:
        files = {"photos": ("sample.jpeg", f, "image/jpeg")}
        data = {"user_id": user_id, "garden_name": "My Test Garden"}
        response = requests.post(f"{BASE_URL}/gardens/upload", files=files, data=data)
    
    assert response.status_code == 200
    garden_id = response.json()["id"]

    # Trigger processing
    response = requests.post(f"{BASE_URL}/jobs/process?stream=false")
    assert response.status_code == 200

    # Poll for status
    for _ in range(30):  # Poll for 30 seconds
        response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
        if response.status_code == 200 and response.json()["status"] == "Ready":
            break
        time.sleep(1)
    
    assert response.status_code == 200
    details = response.json()

    # Assertions
    assert "recommendation" in details
    assert "recommendation_full" in details
    assert "has_pests" in details
    assert "has_disease" in details
    assert "needs_watering" in details
    assert "needs_fertilizing" in details

    assert "immediate_changes" not in details
    assert "disease_overview" not in details
    assert "growth_trend" not in details

    if details["recommendation_full"]:
        assert len(details["recommendation"].split()) <= 11 # 10 words + "..."
