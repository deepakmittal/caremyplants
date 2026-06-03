import os
import requests
import io
from PIL import Image

def test_image_upload():
    base_url = os.environ['BASE_URL']

    # 1. Create a new user
    email = "test.user.image.upload@example.com"
    response = requests.post(f"{base_url}/auth/email", json={"email": email})
    assert response.status_code == 200
    user_id = response.json()["user_id"]

    # 2. Create a dummy image file
    img = Image.new('RGB', (100, 100), color = 'red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    # 3. Upload the image
    files = {'photos': ('test.jpg', img_byte_arr, 'image/jpeg')}
    data = {'user_id': user_id, 'garden_name': 'My Test Garden'}
    response = requests.post(f"{base_url}/gardens/upload", files=files, data=data)

    # 4. Assert the response
    assert response.status_code == 200
    garden_data = response.json()
    assert garden_data["name"] == "My Test Garden"
    assert "id" in garden_data
    assert "garden_update_id" in garden_data

    # 5. (Optional) Verify garden creation
    garden_id = garden_data["id"]
    response = requests.get(f"{base_url}/gardens/{garden_id}/details")
    assert response.status_code == 200
    garden_details = response.json()
    assert garden_details["name"] == "My Test Garden"
