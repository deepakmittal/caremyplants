import os
import requests
import time

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

def test_garden_details_new_feature():
    # 1. Create a new garden with a photo
    with open("sample.jpeg", "rb") as f:
        files = {"photos": ("sample.jpeg", f, "image/jpeg")}
        data = {"name": "My Test Garden"}
        response = requests.post(f"{BASE_URL}/gardens", files=files, data=data)
        assert response.status_code == 200
        garden_data = response.json()
        garden_id = garden_data["id"]

    # 2. Poll the garden details endpoint until the status is "Ready"
    timeout = 300  # 5 minutes
    start_time = time.time()
    while True:
        response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
        assert response.status_code == 200
        details = response.json()
        if details["status"] == "Ready":
            break
        if time.time() - start_time > timeout:
            raise TimeoutError("Garden processing timed out")
        time.sleep(10)

    # 3. Assert that the response contains the new boolean fields
    assert "pest_presence" in details
    assert "water_stress" in details
    assert "nutrient_deficiency" in details
    assert isinstance(details["pest_presence"], bool)
    assert isinstance(details["water_stress"], bool)
    assert isinstance(details["nutrient_deficiency"], bool)

    # 4. Assert that the recommendation is a string and is truncated
    if details["recommendation"]:
        assert isinstance(details["recommendation"], str)
        words = details["recommendation"].split()
        assert len(words) <= 11  # 10 words + "..."
        if len(words) > 10:
            assert details["recommendation"].endswith("...")
