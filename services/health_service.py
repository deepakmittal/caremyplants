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
                score=100,
                flourishingPlantsCount=0,
                careNeededPlantsCount=0
            ),
            metrics=[]
        )

    # --- Sanctuary Vitality Calculation ---
    care_needed_plants_count = 0
    negative_keywords = {"disease", "pest", "unhealthy", "yellowing", "poor", "low"}
    
    for plant in plants:
        latest_plant_update = _get_latest_plant_update(plant)
        if latest_plant_update and latest_plant_update.condition_text:
            if any(keyword in latest_plant_update.condition_text.lower() for keyword in negative_keywords):
                care_needed_plants_count += 1

    flourishing_plants_count = total_plants - care_needed_plants_count
    score = int((flourishing_plants_count / total_plants) * 100) if total_plants > 0 else 100
    
    sanctuary_vitality = schemas.SanctuaryVitality(
        score=score,
        flourishingPlantsCount=flourishing_plants_count,
        careNeededPlantsCount=care_needed_plants_count
    )

    # --- Metrics Calculation ---
    metrics = []
    
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
        # Heuristic: Assume 1/3 of plants are affected if the flag is true
        num_affected = max(1, total_plants // 3)
        watering_ids = [p.id for p in random.sample(plants, num_affected)]
    metrics.append(create_metric("WATERING", "Low" if watering_ids else "Optimal", bool(watering_ids), watering_ids))

    # 2. Sun Exposure
    sun_ids = []
    if latest_garden_update and latest_garden_update.needs_sunlight:
        num_affected = max(1, total_plants // 4)
        sun_ids = [p.id for p in random.sample(plants, num_affected)]
    metrics.append(create_metric("SUN_EXPOSURE", "Low" if sun_ids else "Optimal", bool(sun_ids), sun_ids))

    # 3. Soil Quality (Fertilizer)
    soil_ids = []
    if latest_garden_update and latest_garden_update.needs_fertilizer:
        num_affected = max(1, total_plants // 3)
        soil_ids = [p.id for p in random.sample(plants, num_affected)]
    metrics.append(create_metric("SOIL_QUALITY", "Poor" if soil_ids else "Optimal", bool(soil_ids), soil_ids))

    # Metrics derived from parsing individual plant recommendations
    pruning_ids = []
    pot_ids = []
    leaf_care_ids = [] # Assuming "Dusty" is a proxy for leaf care

    for plant in plants:
        latest_plant_update = _get_latest_plant_update(plant)
        if latest_plant_update and latest_plant_update.recommendation:
            parsed_rec = _parse_recommendation(latest_plant_update.recommendation)
            
            if parsed_rec.get("Pruning Needed", "").lower() in ["yes", "recommended"]:
                pruning_ids.append(plant.id)
            
            if parsed_rec.get("Pot Assessment", "").lower() == "cramped":
                pot_ids.append(plant.id)
            
            # This is a heuristic, as "Leaf Care" is not an explicit field
            if "dusty" in latest_plant_update.recommendation.lower():
                 leaf_care_ids.append(plant.id)

    metrics.append(create_metric("PRUNING", "Overdue" if pruning_ids else "Good", bool(pruning_ids), pruning_ids))
    metrics.append(create_metric("POT_STATUS", "Cramped" if pot_ids else "Balanced", bool(pot_ids), pot_ids))
    metrics.append(create_metric("LEAF_CARE", "Dusty" if leaf_care_ids else "Clean", bool(leaf_care_ids), leaf_care_ids))

    # 4. Vitality (Growth Trend)
    vitality_status = "Good"
    if latest_garden_update and latest_garden_update.growth_trend:
        trend = latest_garden_update.growth_trend.lower()
        if "stagnant" in trend or "declining" in trend:
            vitality_status = "Poor"
    metrics.append(create_metric("VITALITY", vitality_status, vitality_status != "Good", []))


    return schemas.GardenHealthOverview(
        sanctuaryVitality=sanctuary_vitality,
        metrics=metrics
    )
