import os
import requests
import time
import pytest

BASE_URL = os.environ.get("BASE_URL")
if not BASE_URL:
    raise ValueError("BASE_URL environment variable not set")

# A simple image file is needed for garden creation.
# We'll create a dummy file for this test.
DUMMY_IMAGE_NAME = "test_image.jpg"

@pytest.fixture(scope="module")
def test_garden_for_visualization():
    # Create a dummy image file
    with open(DUMMY_IMAGE_NAME, "w") as f:
        f.write("dummy image data")

    # 1. Create a new garden
    try:
        with open(DUMMY_IMAGE_NAME, "rb") as f:
            files = {"photos": (DUMMY_IMAGE_NAME, f, "image/jpeg")}
            data = {"garden_name": "Test Garden for Visualization"}
            response = requests.post(f"{BASE_URL}/gardens/upload", files=files, data=data)
            assert response.status_code == 200
            garden_data = response.json()
            garden_id = garden_data["id"]
    except requests.exceptions.ConnectionError as e:
        pytest.fail(f"Connection to BASE_URL ({BASE_URL}) failed. Please ensure the service is running and accessible: {e}")


    # 2. Process the garden to get it into a 'Ready' state
    # This is important because the visualization logic might depend on processed data.
    process_response = requests.post(f"{BASE_URL}/jobs/process?stream=false")
    assert process_response.status_code == 200

    # 3. Wait for processing to complete
    for _ in range(20):  # Poll for up to 100 seconds
        time.sleep(5)
        details_response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
        if details_response.status_code == 200:
            details = details_response.json()
            if details.get("status") == "Ready":
                break
    else:
        pytest.fail("Garden did not become 'Ready' within the timeout period.")

    yield garden_id

    # Teardown: Delete the garden and the dummy image file
    delete_response = requests.delete(f"{BASE_URL}/gardens/{garden_id}")
    assert delete_response.status_code == 200
    os.remove(DUMMY_IMAGE_NAME)

def test_garden_visualization_workflow(test_garden_for_visualization):
    garden_id = test_garden_for_visualization

    # 1. Trigger the visualization process
    visualize_response = requests.post(f"{BASE_URL}/gardens/{garden_id}/visualize")
    assert visualize_response.status_code == 202

    # 2. Poll the details endpoint until the visualization is ready
    visualization_data = None
    for _ in range(10):  # Poll for up to 20 seconds
        time.sleep(2)
        details_response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
        assert details_response.status_code == 200
        details = details_response.json()
        if details.get("visualization") is not None:
            visualization_data = details["visualization"]
            break
    
    assert visualization_data is not None, "Visualization data was not generated in time."

    # 3. Validate the structure of the visualization data
    assert "image_url" in visualization_data
    assert "products" in visualization_data
    assert isinstance(visualization_data["image_url"], str)
    assert isinstance(visualization_data["products"], list)

    # 4. Validate the contents of the products list
    if visualization_data["products"]:
        product = visualization_data["products"][0]
        assert "name" in product
        assert "reason" in product
        assert "url" in product
        assert "product_type" in product
        
        # Check for a valid product type
        valid_product_types = [
            "PLANTER_BOX", "HIGH_POT", "HANGING_POT", "SOIL", "MANURE",
            "DECORATIVE_POT", "STANDARD_POT", "WATERING_CAN"
        ]
        assert product["product_type"] in valid_product_types
