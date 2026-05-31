import os
import requests
import re

def test_background_color():
    base_url = os.environ['BASE_URL']
    
    # First, get the main page
    response = requests.get(base_url)
    response.raise_for_status()
    
    # In a real vite app, the css file would be linked in the index.html
    # with a hash in the name. For this test, we'll assume the dev server
    # is running and the file is served from its original location.
    css_path = "/src/index.css"
    css_url = f"{base_url}{css_path}"
    
    css_response = requests.get(css_url)
    css_response.raise_for_status()
    
    assert "--bg-dark: #166534;" in css_response.text
