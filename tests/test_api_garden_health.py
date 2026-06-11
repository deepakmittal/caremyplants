import os
import requests
import pytest

# Ensure the BASE_URL is set, otherwise skip the tests
BASE_URL = os.environ.get("BASE_URL")
if not BASE_URL:
    pytest.skip("BASE_URL environment variable not set, skipping integration tests.", allow_module_level=True)

def test_get_garden_details_with_health_overview():
    """
    Tests the GET /gardens/{garden_id}/details endpoint to ensure it returns
    the new healthOverview structure.
    """
    # Arrange
    garden_id = 1  # Assuming a garden with ID 1 exists in the test database
    url = f"{BASE_URL}/gardens/{garden_id}/details"
    
    # Act
    response = requests.get(url)
    
    # Assert
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response: {response.text}"
    
    data = response.json()
    
    # Check for the presence of the main health overview object
    assert "healthOverview" in data, "The 'healthOverview' key is missing from the response."
    assert data["healthOverview"] is not None, "The 'healthOverview' object should not be null."
    
    health_overview = data["healthOverview"]
    
    # Validate the SanctuaryVitality structure and values
    assert "sanctuaryVitality" in health_overview, "The 'sanctuaryVitality' key is missing from healthOverview."
    vitality = health_overview["sanctuaryVitality"]
    assert "score" in vitality
    assert "flourishingPlantsCount" in vitality
    assert "careNeededPlantsCount" in vitality
    assert isinstance(vitality["score"], int)
    assert 0 <= vitality["score"] <= 100
    assert isinstance(vitality["flourishingPlantsCount"], int)
    assert isinstance(vitality["careNeededPlantsCount"], int)

    # Validate the Metrics structure
    assert "metrics" in health_overview, "The 'metrics' key is missing from healthOverview."
    metrics = health_overview["metrics"]
    assert isinstance(metrics, list), "Metrics should be a list."
    
    if len(metrics) > 0:
        # If there are metrics, validate the structure of the first one
        metric = metrics[0]
        expected_keys = ["category", "status", "isUnfavorable", "affectedPlantsCount", "affectedPlantIds"]
        for key in expected_keys:
            assert key in metric, f"Key '{key}' is missing from a metric object."
        
        assert isinstance(metric["category"], str)
        assert isinstance(metric["status"], str)
        assert isinstance(metric["isUnfavorable"], bool)
        assert isinstance(metric["affectedPlantsCount"], int)
        assert isinstance(metric["affectedPlantIds"], list)
        if metric["affectedPlantsCount"] > 0:
            assert len(metric["affectedPlantIds"]) == metric["affectedPlantsCount"]
            assert all(isinstance(pid, int) for pid in metric["affectedPlantIds"])

def test_garden_health_for_nonexistent_garden():
    """
    Tests that the endpoint returns a 404 for a garden that does not exist.
    """
    # Arrange
    garden_id = 99999  # An ID that is unlikely to exist
    url = f"{BASE_URL}/gardens/{garden_id}/details"
    
    # Act
    response = requests.get(url)
    
    # Assert
    assert response.status_code == 404, f"Expected status code 404 for a non-existent garden, but got {response.status_code}."
