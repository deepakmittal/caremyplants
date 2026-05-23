import os
import requests
from datetime import datetime

def test_get_time():
    base_url = os.environ.get("BASE_URL")
    assert base_url, "BASE_URL environment variable not set"

    response = requests.get(f"{base_url}/api/v1/time")
    assert response.status_code == 200

    data = response.json()
    assert "delhi_time" in data
    assert "san_francisco_time" in data

    # Validate that the returned time strings are valid ISO 8601 timestamps
    try:
        datetime.fromisoformat(data["delhi_time"])
        datetime.fromisoformat(data["san_francisco_time"])
    except ValueError as e:
        assert False, f"Invalid timestamp format: {e}"
