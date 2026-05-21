import os
import requests

BASE_URL = os.environ.get("BASE_URL")

def test_vayu_endpoint():
    assert BASE_URL, "BASE_URL environment variable not set"
    response = requests.get(f"{BASE_URL}/vayu")
    assert response.status_code == 200
    assert response.text == "hi"
