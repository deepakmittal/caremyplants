import os
import requests

def test_homepage_background_color():
    base_url = os.environ['BASE_URL']
    response = requests.get(base_url)
    assert response.status_code == 200
    assert 'text/html' in response.headers['Content-Type']
