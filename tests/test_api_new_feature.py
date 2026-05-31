import os
import requests
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

def test_get_garden_details_new_design():
    # Create a user
    email = "testuser_new_design@example.com"
    response = requests.post(f"{BASE_URL}/auth/email", json={"email": email})
    assert response.status_code == 200
    user_id = response.json()["user_id"]

    # Create a garden
    garden_name = "My Test Garden New Design"
    response = requests.post(
        f"{BASE_URL}/gardens/upload",
        files={"photos": ("test.jpg", b"test image data", "image/jpeg")},
        data={"garden_name": garden_name, "user_id": user_id},
    )
    assert response.status_code == 200
    garden_id = response.json()["id"]
    garden_update_id = response.json()["garden_update_id"]

    # Manually update the garden update with new fields for testing
    # This is a workaround for not having the AI analysis part implemented
    from sqlalchemy.orm import sessionmaker
    from database import engine
    from models import GardenUpdate

    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        garden_update = db.query(GardenUpdate).filter(GardenUpdate.id == garden_update_id).first()
        if garden_update:
            garden_update.recommendation = "This is a very long recommendation that should be truncated to ten words to test the new feature."
            garden_update.has_pests = True
            garden_update.has_disease = False
            garden_update.is_healthy = False
            garden_update.needs_water = True
            garden_update.needs_sunlight = False
            db.commit()
    finally:
        db.close()


    # Get garden details
    response = requests.get(f"{BASE_URL}/gardens/{garden_id}/details")
    assert response.status_code == 200
    details = response.json()

    # Assertions
    assert details["id"] == garden_id
    assert details["name"] == garden_name
    assert "recommendation" in details
    assert "recommendation_full" in details
    assert "show_more" in details
    assert "has_pests" in details
    assert "has_disease" in details
    assert "is_healthy" in details
    assert "needs_water" in details
    assert "needs_sunlight" in details

    assert details["recommendation"] == "This is a very long recommendation that should be truncated"
    assert details["recommendation_full"] == "This is a very long recommendation that should be truncated to ten words to test the new feature."
    assert details["show_more"] is True
    assert details["has_pests"] is True
    assert details["has_disease"] is False
    assert details["is_healthy"] is False
    assert details["needs_water"] is True
    assert details["needs_sunlight"] is False

    assert "immediate_changes" not in details
    assert "disease_overview" not in details
    assert "growth_trend" not in details
