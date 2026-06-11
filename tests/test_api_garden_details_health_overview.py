
import os
import httpx
import pytest

BASE_URL = os.environ.get("BASE_URL")
if not BASE_URL:
    raise ValueError("BASE_URL environment variable not set")

@pytest.mark.integration
def test_get_garden_details_with_health_overview():
    """
    Tests the GET /gardens/{garden_id}/details endpoint to ensure it returns
    the healthOverview object with the correct structure.
    """
    garden_id = 1
    url = f"{BASE_URL}/gardens/{garden_id}/details"

    with httpx.Client() as client:
        try:
            response = client.get(url, timeout=30.0)
            response.raise_for_status() 
        except httpx.RequestError as exc:
            pytest.fail(f"An error occurred while requesting {exc.request.url!r}: {exc}")
        except httpx.HTTPStatusError as exc:
            pytest.fail(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}")

    assert response.status_code == 200
    data = response.json()

    assert "healthOverview" in data
    health_overview = data["healthOverview"]
    assert health_overview is not None, "healthOverview should not be null"

    # 1. Validate SanctuaryVitality structure
    assert "sanctuaryVitality" in health_overview
    vitality = health_overview["sanctuaryVitality"]
    assert isinstance(vitality["score"], int)
    assert isinstance(vitality["flourishingPlantsCount"], int)
    assert isinstance(vitality["careNeededPlantsCount"], int)
    assert 0 <= vitality["score"] <= 100

    # 2. Validate Metrics structure
    assert "metrics" in health_overview
    metrics = health_overview["metrics"]
    assert isinstance(metrics, list)
    
    # Check if there are metrics, if the garden has plants
    if data.get("plants"):
        assert len(metrics) > 0

        # 3. Validate a single CareMetric item
        metric_item = metrics[0]
        assert "category" in metric_item
        assert "status" in metric_item
        assert "isUnfavorable" in metric_item
        assert "affectedPlantsCount" in metric_item
        assert "affectedPlantIds" in metric_item

        assert isinstance(metric_item["category"], str)
        assert isinstance(metric_item["status"], str)
        assert isinstance(metric_item["isUnfavorable"], bool)
        assert isinstance(metric_item["affectedPlantsCount"], int)
        assert isinstance(metric_item["affectedPlantIds"], list)

        # 4. Check category enum values
        valid_categories = [
            "WATERING", "SUN_EXPOSURE", "SOIL_QUALITY", "VITALITY",
            "LEAF_CARE", "POT_STATUS", "PRUNING"
        ]
        for metric in metrics:
            assert metric["category"] in valid_categories
            assert len(metric["affectedPlantIds"]) == metric["affectedPlantsCount"]

    print(f"Successfully validated healthOverview for garden {garden_id}")

