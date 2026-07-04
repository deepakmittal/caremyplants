import os
import requests
import pytest

BASE_URL = os.environ.get("BASE_URL")
if not BASE_URL:
    pytest.skip("BASE_URL environment variable not set, skipping integration tests.", allow_module_level=True)

def test_get_garden_details_with_ai_assessment():
    """
    Tests the GET /gardens/{garden_id}/details endpoint to ensure it returns
    the new AI-generated health assessment format.
    """
    # Arrange
    garden_id = 1  # Assuming a garden with ID 1 exists
    url = f"{BASE_URL}/gardens/{garden_id}/details"

    # Act
    response = requests.get(url)

    # Assert
    assert response.status_code == 200
    
    data = response.json()
    assert "healthOverview" in data
    
    health_overview = data["healthOverview"]
    assert health_overview is not None

    # Assert SanctuaryVitality
    vitality = health_overview.get("sanctuaryVitality")
    assert vitality is not None
    assert "score" in vitality
    assert isinstance(vitality["score"], int)
    assert 1 <= vitality["score"] <= 5
    assert "flourishingPlantsCount" in vitality
    assert "careNeededPlantsCount" in vitality

    # Assert CareMetric
    metrics = health_overview.get("metrics")
    assert metrics is not None
    assert isinstance(metrics, list)
    assert len(metrics) > 0

    for metric in metrics:
        assert "category" in metric
        assert "status" in metric
        assert isinstance(metric["status"], str)
        assert len(metric["status"]) > 0
        assert "isUnfavorable" in metric
        assert "affectedPlantsCount" in metric
        assert "affectedPlantIds" in metric

    # Check for specific metric categories and their statuses
    metric_categories = {m["category"] for m in metrics}
    expected_categories = {"WATERING", "SUN_EXPOSURE", "SOIL_QUALITY", "VITALITY", "LEAF_CARE", "POT_STATUS", "PRUNING"}
    assert expected_categories.issubset(metric_categories)

    # Example check for a specific metric's status value
    watering_metric = next((m for m in metrics if m["category"] == "WATERING"), None)
    assert watering_metric is not None
    assert watering_metric["status"] in ["Overwatered", "Properly Watered", "Underwatered"]

    sun_exposure_metric = next((m for m in metrics if m["category"] == "SUN_EXPOSURE"), None)
    assert sun_exposure_metric is not None
    assert sun_exposure_metric["status"] in ["Too Sunny", "Sunny", "Dark"]
