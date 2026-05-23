import os
import requests

def test_vayu_endpoint():
    base_url = os.environ.get("BASE_URL")
    assert base_url, "BASE_URL environment variable not set"
    
    response = requests.get(f"{base_url}/Vayu")
    
    assert response.status_code == 200
    assert response.text == '"Hi"'
