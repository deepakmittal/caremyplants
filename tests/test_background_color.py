
import os
import requests

def test_background_color():
    base_url = os.environ['BASE_URL']
    response = requests.get(f"{base_url}/frontend/src/index.css")
    assert response.status_code == 200
    assert "--bg-dark: #1a3c34;" in response.text
