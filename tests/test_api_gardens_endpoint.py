import os
import httpx
import pytest

BASE_URL = os.environ.get("BASE_URL")
if not BASE_URL:
    raise ValueError("BASE_URL environment variable is not set")

USER_ID = "1"  # Assuming a test user with ID 1 exists

@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL) as client:
        yield client

def test_get_gardens(client: httpx.Client):
    """
    Tests fetching all gardens.
    """
    response = client.get("/gardens")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_user_gardens(client: httpx.Client):
    """
    Tests fetching gardens for a specific user.
    """
    response = client.get(f"/users/{USER_ID}/gardens")
    assert response.status_code == 200
    json_response = response.json()
    assert isinstance(json_response, list)
    # Further checks can be added if there's known state for user 1
    if json_response:
        assert "owner_id" in json_response[0]
        assert str(json_response[0]["owner_id"]) == USER_ID
