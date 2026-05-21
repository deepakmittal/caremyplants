import os
import requests

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")

def test_get_name():
    response = requests.get(f"{BASE_URL}/name")
    assert response.status_code == 200
    assert response.json() == {"name": "Deepak"}
