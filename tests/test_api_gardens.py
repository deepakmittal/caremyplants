import os
import requests
import uuid

BASE_URL = os.environ.get("BASE_URL", "https://caremyplants-dev1-ch4p6cqrla-uc.a.run.app")

def test_get_user_gardens():
    """
    Tests the flow:
    1. Create a new, unique user via the /auth/email endpoint.
    2. Verify that the user initially has no gardens.
    3. Create a new garden for that user via /gardens/upload.
    4. Fetch the user's gardens again via /users/{user_id}/gardens/detailed.
    5. Verify that the newly created garden is present in the list.
    """
    # 1. Create a unique user
    unique_email = f"test_user_{uuid.uuid4()}@example.com"
    auth_response = requests.post(f"{BASE_URL}/auth/email", json={"email": unique_email})
    assert auth_response.status_code == 200
    auth_data = auth_response.json()
    assert "user_id" in auth_data
    user_id = auth_data["user_id"]

    # 2. Verify the user has no gardens initially
    initial_gardens_response = requests.get(f"{BASE_URL}/users/{user_id}/gardens/detailed")
    assert initial_gardens_response.status_code == 200
    assert initial_gardens_response.json() == []

    # 3. Create a new garden for the user
    garden_name = f"My Test Garden {uuid.uuid4()}"
    # The /gardens/upload endpoint requires a multipart/form-data request.
    # We need to send at least one file, even if it's empty.
    files = {'photos': ('test.jpg', b'', 'image/jpeg')}
    data = {
        'user_id': user_id,
        'garden_name': garden_name
    }
    create_response = requests.post(f"{BASE_URL}/gardens/upload", files=files, data=data)
    
    # Check for successful creation
    assert create_response.status_code == 200
    create_data = create_response.json()
    assert create_data["name"] == garden_name
    assert "id" in create_data
    garden_id = create_data["id"]

    # 4. Fetch the user's gardens again
    final_gardens_response = requests.get(f"{BASE_URL}/users/{user_id}/gardens/detailed")
    assert final_gardens_response.status_code == 200
    final_gardens_data = final_gardens_response.json()

    # 5. Verify the new garden is in the list
    assert isinstance(final_gardens_data, list)
    assert len(final_gardens_data) == 1
    
    user_garden = final_gardens_data[0]
    assert user_garden["id"] == garden_id
    assert user_garden["name"] == garden_name
    assert user_garden["status"] == "New"
