import os
import requests
from datetime import datetime

def test_get_current_time():
    base_url = os.environ.get("BASE_URL")
    assert base_url, "BASE_URL environment variable not set"
    
    response = requests.get(f"{base_url}/time")
    assert response.status_code == 200
    
    data = response.json()
    assert "currentTime" in data
    
    try:
        # Validate that the returned string is a valid ISO 8601 timestamp
        datetime.fromisoformat(data["currentTime"])
    except ValueError:
        assert False, f"Invalid timestamp format: {data['currentTime']}"
