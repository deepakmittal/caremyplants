
import os
import requests

def test_background_color_change():
    base_url = os.environ.get("BASE_URL")
    if not base_url:
        raise ValueError("BASE_URL environment variable not set")

    response = requests.get(base_url)
    assert response.status_code == 200
    assert "text/html" in response.headers["Content-Type"]
    assert '<link rel="stylesheet" href="/assets/index' in response.text
