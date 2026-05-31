import os
import requests

def test_background_color():
    base_url = os.environ['BASE_URL']
    response = requests.get(base_url)
    assert response.status_code == 200
    # The background color is set in the index.css file
    # We need to fetch the index.css file and check its content
    css_path = None
    for line in response.text.split('\n'):
        if 'link rel="stylesheet"' in line:
            css_path = line.split('href="')[1].split('"')[0]
            break
    
    assert css_path is not None, "Could not find css file in html response"

    css_url = f"{base_url}{css_path}"
    css_response = requests.get(css_url)
    assert css_response.status_code == 200
    assert "--bg-dark: #1a3c34;" in css_response.text
