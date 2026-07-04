"""
health_service.py
-----------------
Service for calculating garden health overview metrics.
"""
import random
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import models
import schemas
from services.gemini import assess_garden_health_with_ai
from services.gcs import download_from_gcs
from urllib.parse import urlparse

def _get_latest_garden_update(db_garden: models.Garden) -> models.GardenUpdate | None:
    """Retrieves the most recent 'Ready' garden update."""
    if not db_garden.updates:
        return None
    
    ready_updates = sorted(
        [u for u in db_garden.updates if u.status == 'Ready'],
        key=lambda u: u.created_at,
        reverse=True
    )
    return ready_updates[0] if ready_updates else None

def _get_latest_plant_update(db_plant: models.Plant) -> models.PlantUpdate | None:
    """Retrieves the most recent 'Ready' plant update."""
    if not db_plant.updates:
        return None
    
    ready_updates = sorted(
        [u for u in db_plant.updates if u.status == 'Ready'],
        key=lambda u: u.created_at,
        reverse=True
    )
    return ready_updates[0] if ready_updates else None

def _parse_recommendation(recommendation: str) -> Dict[str, str]:
    """Parses the key-value string in the recommendation field."""
    parsed = {}
    if not recommendation:
        return parsed
    for line in recommendation.split('\\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            parsed[key.strip()] = value.strip()
    return parsed

def calculate_garden_health(db_garden: models.Garden) -> schemas.GardenHealthOverview:
    """
    Calculates the complete health overview for a given garden.
    """
    plants = db_garden.plants
    latest_garden_update = _get_latest_garden_update(db_garden)
    total_plants = len(plants)
    
    if total_plants == 0:
        # Return a default empty state if there are no plants
        return schemas.GardenHealthOverview(
            sanctuaryVitality=schemas.SanctuaryVitality(
                score=1,
                flourishingPlantsCount=0,
                careNeededPlantsCount=0
            ),
            metrics=[]
        )

    # --- Download Garden Images ---
    image_bytes_list = []
    for photo in db_garden.photos:
        try:
            parsed_url = urlparse(photo.photo_url)
            blob_name = parsed_url.path.lstrip('/')
            # The blob name is everything after the bucket name in the path
            blob_name = blob_name.split('/', 1)[1]
            image_bytes_list.append(download_from_gcs(blob_name))
        except Exception as e:
            print(f"Error downloading image {photo.photo_url}: {e}")
            continue

    # --- Get AI Health Assessment ---
    ai_assessment = {}
    if image_bytes_list:
        ai_assessment = assess_garden_health_with_ai(image_bytes_list)

    # --- Sanctuary Vitality Calculation ---
    care_needed_plants_count = 0
    negative_keywords = {"disease", "pest", "unhealthy", "yellowing", "poor", "low"}
    
    for plant in plants:
        latest_plant_update = _get_latest_plant_update(plant)
        if latest_plant_update and latest_plant_update.condition_text:
            if any(keyword in latest_plant_update.condition_text.lower() for keyword in negative_keywords):
                care_needed_plants_count += 1

    flourishing_plants_count = total_plants - care_needed_plants_count
    
    sanctuary_vitality = schemas.SanctuaryVitality(
        score=ai_assessment.get("score", 3), # Default to 3 if AI fails
        flourishingPlantsCount=flourishing_plants_count,
        careNeededPlantsCount=care_needed_plants_count
    )

    # --- Metrics Calculation ---
    metrics = []
    ai_metrics = ai_assessment.get("metrics", {})
    
    # Helper to create a metric
    def create_metric(category, status, is_unfavorable, affected_ids):
        return schemas.CareMetric(
            category=category,
            status=status,
            isUnfavorable=is_unfavorable,
            affectedPlantsCount=len(affected_ids),
            affectedPlantIds=affected_ids
        )

    # 1. Watering
    watering_ids = []
    if latest_garden_update and latest_garden_update.needs_watering:
        num_affected = max(1, total_plants // 3)
        watering_ids = [p.id for p in random.sample(plants, num_affected)]
    watering_status = ai_metrics.get("WATERING", "Properly Watered")
    metrics.append(create_metric("WATERING", watering_status, watering_status != "Properly Watered", watering_ids))

    # 2. Sun Exposure
    sun_ids = []
    if latest_garden_update and latest_garden_update.needs_sunlight:
        num_affected = max(1, total_plants // 4)
        sun_ids = [p.id for p in random.sample(plants, num_affected)]
    sun_status = ai_metrics.get("SUN_EXPOSURE", "Sunny")
    metrics.append(create_metric("SUN_EXPOSURE", sun_status, sun_status != "Sunny", sun_ids))

    # 3. Soil Quality (Fertilizer)
    soil_ids = []
    if latest_garden_update and latest_garden_update.needs_fertilizer:
        num_affected = max(1, total_plants // 3)
        soil_ids = [p.id for p in random.sample(plants, num_affected)]
    soil_status = ai_metrics.get("SOIL_QUALITY", "Balanced")
    metrics.append(create_metric("SOIL_QUALITY", soil_status, soil_status != "Balanced" and soil_status != "Rich", soil_ids))

    # Metrics derived from parsing individual plant recommendations
    pruning_ids = []
    pot_ids = []
    leaf_care_ids = []

    for plant in plants:
        latest_plant_update = _get_latest_plant_update(plant)
        if latest_plant_update and latest_plant_update.recommendation:
            parsed_rec = _parse_recommendation(latest_plant_update.recommendation)
            
            if parsed_rec.get("Pruning Needed", "").lower() in ["yes", "recommended"]:
                pruning_ids.append(plant.id)
            
            if parsed_rec.get("Pot Assessment", "").lower() == "cramped":
                pot_ids.append(plant.id)
            
            if "dusty" in latest_plant_update.recommendation.lower():
                 leaf_care_ids.append(plant.id)

    pruning_status = ai_metrics.get("PRUNING", "Well-Maintained")
    metrics.append(create_metric("PRUNING", pruning_status, pruning_status != "Well-Maintained", pruning_ids))
    
    pot_status = ai_metrics.get("POT_STATUS", "Adequate")
    metrics.append(create_metric("POT_STATUS", pot_status, pot_status == "Cramped", pot_ids))

    leaf_care_status = ai_metrics.get("LEAF_CARE", "Pristine")
    metrics.append(create_metric("LEAF_CARE", leaf_care_status, leaf_care_status != "Pristine", leaf_care_ids))

    # 4. Vitality
    vitality_status = ai_metrics.get("VITALITY", "Stable")
    metrics.append(create_metric("VITALITY", vitality_status, vitality_status == "Struggling", []))


    return schemas.GardenHealthOverview(
        sanctuaryVitality=sanctuary_vitality,
        metrics=metrics
    )
