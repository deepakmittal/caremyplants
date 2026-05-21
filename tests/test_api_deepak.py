import os
import requests

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")

def test_deepak_endpoint():
    response = requests.get(f"{BASE_URL}/deepak")
    assert response.status_code == 200
    assert response.text == "hi"
