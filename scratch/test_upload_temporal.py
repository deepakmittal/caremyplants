import requests
BASE_URL = "https://caremyplants-1059916488233.us-central1.run.app"
with open("/Users/ritika/Garden/sample.jpeg", "rb") as f:
    files = {"photos": ("sample.jpeg", f, "image/jpeg")}
    data = {"garden_name": "Test Garden for Temporal"}
    response = requests.post(f"{BASE_URL}/gardens/upload", files=files, data=data)
    print("Response Status:", response.status_code)
    print("Response JSON:", response.json())
