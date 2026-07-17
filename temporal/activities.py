
import logging
import uuid
import json
from sqlalchemy.orm import Session
from temporalio import activity

import models
from services import gcs, gemini
from utils import image as image_utils
from database import SessionLocal

logger = logging.getLogger(__name__)

# --- Helper functions (adapted from services/garden_processor.py) ---

def _get_db():
    return SessionLocal()

def _download_photo_bytes(photo_url: str):
    try:
        parts = photo_url.split("storage.googleapis.com/", 1)
        if len(parts) < 2:
            return None
        blob_path = parts[1].split("/", 1)[-1]
        return gcs.download_from_gcs(blob_path)
    except Exception as e:
        logger.warning(f"Could not download photo {photo_url}: {e}")
        return None

def _find_or_create_plant(db: Session, garden_id: int, plant_name: str, variety: str, condition: str) -> models.Plant:
    existing = (
        db.query(models.Plant)
        .filter(models.Plant.garden_id == garden_id)
        .all()
    )
    name_lower = plant_name.strip().lower()
    for plant in existing:
        if plant.name.strip().lower() == name_lower:
            plant.plant_variety = variety or plant.plant_variety
            plant.condition = condition or plant.condition
            db.commit()
            return plant

    new_plant = models.Plant(
        garden_id=garden_id,
        name=plant_name,
        plant_variety=variety,
        condition=condition,
    )
    db.add(new_plant)
    db.commit()
    db.refresh(new_plant)
    logger.info(f"Created new plant '{plant_name}' (id={new_plant.id}) in garden {garden_id}")
    return new_plant

def _get_last_plant_update_details(db: Session, plant_id: int):
    last = (
        db.query(models.PlantUpdate)
        .filter(
            models.PlantUpdate.plant_id == plant_id,
            models.PlantUpdate.status == "Ready",
        )
        .order_by(models.PlantUpdate.created_at.desc())
        .first()
    )
    if last:
        return last.recommendation, last.condition_text
    return None, None

# --- Activities ---

@activity.defn
def gather_garden_details(update_id: int) -> dict:
    db = _get_db()
    try:
        activity.heartbeat()
        update = db.query(models.GardenUpdate).filter(models.GardenUpdate.id == update_id).first()
        if not update:
            raise ValueError(f"Update {update_id} not found.")

        garden_id = update.garden_id
        logger.info(f"Activity 1: GATHER_GARDEN_DETAILS for update {update_id}")

        photos = db.query(models.GardenPhoto).filter(models.GardenPhoto.update_id == update_id).all()
        if not photos:
            raise ValueError(f"No photos found for update {update_id}.")

        image_contents = [_download_photo_bytes(p.photo_url) for p in photos]
        image_contents = [img for img in image_contents if img]
        if not image_contents:
            raise ValueError(f"Could not download any photos for update {update_id}.")

        activity.heartbeat()
        logger.info(f"Running combined garden overview and plant identification for garden {garden_id}...")
        existing_plants_db = db.query(models.Plant).filter(models.Plant.garden_id == garden_id).all()
        existing_plant_names = [p.name for p in existing_plants_db]
        
        combined_result = gemini.analyze_garden_combined(image_contents, existing_plants=existing_plant_names)
        if not combined_result:
            raise RuntimeError("Combined Garden analysis failed.")

        overview = combined_result.get("overview", {})
        plants_list = combined_result.get("plants", [])

        update.summary = overview.get('summary')
        update.recommendation = overview.get('general_suggestions')
        update.immediate_changes = overview.get('immediate_changes')
        update.disease_overview = overview.get('disease_overview')
        update.growth_trend = overview.get('growth_trend')
        update.hydration = overview.get('hydration')
        update.exposure = overview.get('exposure')
        update.vibrancy = overview.get('vibrancy')
        update.temperature = overview.get('temperature')
        update.humidity = overview.get('humidity')
        update.needs_watering = overview.get('needs_watering', False)
        update.needs_fertilizer = overview.get('needs_fertilizer', False)
        update.has_pests = overview.get('has_pests', False)
        update.has_weeds = overview.get('has_weeds', False)
        update.has_disease = overview.get('has_disease', False)
        update.needs_sunlight = overview.get('needs_sunlight', False)
        
        # Save health overview metrics calculated in the background
        update.health_score = overview.get('health_score')
        metrics_dict = overview.get('health_metrics')
        if metrics_dict:
            update.health_metrics = json.dumps(metrics_dict)
        
        if update.garden:
            update.garden.summary = overview.get('summary')
            
        db.commit()

        filtered_plants = [p for p in plants_list if p.get("confidence", 0) >= 0.6]

        return {"plants_list": filtered_plants, "garden_id": garden_id}
    finally:
        db.close()


@activity.defn
def cut_plant_images(update_id: int, garden_id: int, plants_list: list) -> list[int]:
    db = _get_db()
    try:
        logger.info(f"Activity 2: CUT_PLANT_IMAGES for garden {garden_id}")
        plant_update_ids = []

        photos = db.query(models.GardenPhoto).filter(models.GardenPhoto.update_id == update_id).all()
        if not photos:
            raise ValueError(f"No photos found for update {update_id}.")
        image_contents = [_download_photo_bytes(p.photo_url) for p in photos]
        image_contents = [img for img in image_contents if img]
        if not image_contents:
            raise ValueError(f"Could not re-download photos for update {update_id}.")


        for plant_data in plants_list:
            activity.heartbeat()
            plant_name = plant_data.get("name", "Unknown Plant")
            variety = plant_data.get("variety", "")
            condition = plant_data.get("condition", "")

            photo_idx = plant_data.get("photo_index", 0)
            source_image = image_contents[photo_idx] if photo_idx < len(image_contents) else None

            if not source_image:
                logger.warning(f"No source image for plant '{plant_name}'. Skipping.")
                continue

            cropped_bytes = image_utils.crop_plant_image(source_image, plant_data.get("box_2d")) or source_image

            blob_name = f"garden_{garden_id}/plant_{uuid.uuid4()}.jpg"
            cropped_url = gcs.upload_to_gcs(cropped_bytes, blob_name)

            db_plant = _find_or_create_plant(db, garden_id, plant_name, variety, condition)
            db_plant_update = models.PlantUpdate(
                plant_id=db_plant.id,
                image_url=cropped_url,
                box_2d=json.dumps(plant_data.get("box_2d")),
                status="Processing",
            )
            db.add(db_plant_update)
            db.commit()
            db.refresh(db_plant_update)
            plant_update_ids.append(db_plant_update.id)

        return plant_update_ids
    finally:
        db.close()


@activity.defn
def gather_plants_details_batch(plant_update_ids: list[int]) -> None:
    db = _get_db()
    try:
        logger.info(f"Activity 3: GATHER_PLANTS_DETAILS_BATCH for {len(plant_update_ids)} plants")
        activity.heartbeat()

        plants_to_diagnose = []
        updates_by_id = {}

        for plant_update_id in plant_update_ids:
            db_plant_update = db.query(models.PlantUpdate).filter(models.PlantUpdate.id == plant_update_id).first()
            if not db_plant_update:
                logger.warning(f"PlantUpdate {plant_update_id} not found.")
                continue

            db_plant = db_plant_update.plant
            if not db_plant or not db_plant_update.image_url:
                logger.warning(f"Plant or image_url missing for update {plant_update_id}. Skipping.")
                continue

            analysis_bytes = _download_photo_bytes(db_plant_update.image_url)
            if not analysis_bytes:
                logger.warning(f"Could not download image for plant update {plant_update_id}. Skipping.")
                continue

            last_recommendation, last_condition = _get_last_plant_update_details(db, db_plant.id)
            
            plants_to_diagnose.append({
                "image_bytes": analysis_bytes,
                "name": db_plant.name,
                "last_condition": last_condition,
                "last_recommendation": last_recommendation,
                "temp_id": plant_update_id
            })
            updates_by_id[plant_update_id] = (db_plant, db_plant_update)

        if not plants_to_diagnose:
            return

        activity.heartbeat()
        diagnoses = gemini.analyze_plants_detail_batch(plants_to_diagnose)

        for diag in diagnoses:
            temp_id = diag.get("temp_id")
            if temp_id not in updates_by_id:
                continue

            db_plant, db_plant_update = updates_by_id[temp_id]

            if not diag.get("is_valid_plant"):
                logger.info(f"Deleting false positive plant '{db_plant.name}'.")
                db.delete(db_plant)
                db.commit()
                continue

            recommendation = f"Recommendation: {diag.get('recommendation', 'N/A')}"
            db_plant_update.condition_text = diag.get("disease", db_plant.condition)
            db_plant_update.recommendation = recommendation
            db_plant_update.status = "Ready"
            db.commit()

    finally:
        db.close()


@activity.defn
def update_garden_flags(update_id: int) -> None:
    db = _get_db()
    try:
        logger.info(f"Activity 4: UPDATE_GARDEN_FLAGS for update {update_id}")
        activity.heartbeat()

        update = db.query(models.GardenUpdate).filter(models.GardenUpdate.id == update_id).first()
        if not update:
            raise ValueError(f"Update {update_id} not found.")

        update.status = "Ready"
        db.query(models.Garden).filter(models.Garden.id == update.garden_id).update({"status": "Ready"})
        db.commit()
        logger.info(f"Update {update_id} successfully processed and marked as 'Ready'.")
    finally:
        db.close()

@activity.defn
def generate_garden_visualization(update_id: int) -> None:
    db = _get_db()
    try:
        logger.info(f"Activity 5: GENERATE_GARDEN_VISUALIZATION for update {update_id}")
        activity.heartbeat()

        update = db.query(models.GardenUpdate).filter(models.GardenUpdate.id == update_id).first()
        if not update:
            raise ValueError(f"Update {update_id} not found.")

        garden = update.garden
        if not garden:
            raise ValueError(f"Garden not found for update {update_id}.")

        # Get the first photo of the garden update
        photo = db.query(models.GardenPhoto).filter(models.GardenPhoto.update_id == update_id).first()
        if not photo:
            raise ValueError(f"No photo found for update {update_id}.")

        # Download the photo
        image_bytes = _download_photo_bytes(photo.photo_url)
        if not image_bytes:
            raise ValueError(f"Could not download photo for update {update_id}.")

        # Get all plants and their latest updates
        plants = db.query(models.Plant).filter(models.Plant.garden_id == garden.id).all()
        plants_data = []
        recommendations = []

        if update.recommendation:
            recommendations.append(update.recommendation)

        for plant in plants:
            latest_update = (
                db.query(models.PlantUpdate)
                .filter(models.PlantUpdate.plant_id == plant.id)
                .order_by(models.PlantUpdate.created_at.desc())
                .first()
            )
            if latest_update and latest_update.recommendation:
                recommendations.append(f"{plant.name}: {latest_update.recommendation}")

        # Build plants_list from database coordinates instead of re-running Gemini
        plants_list = []
        for plant in plants:
            latest_update = (
                db.query(models.PlantUpdate)
                .filter(models.PlantUpdate.plant_id == plant.id)
                .order_by(models.PlantUpdate.created_at.desc())
                .first()
            )
            if latest_update:
                box = None
                if latest_update.box_2d:
                    try:
                        box = json.loads(latest_update.box_2d)
                    except Exception:
                        pass
                
                plants_list.append({
                    "name": plant.name,
                    "variety": plant.plant_variety,
                    "condition": latest_update.condition_text or plant.condition,
                    "photo_index": 0,
                    "box_2d": box
                })

        # Generate the visualization
        visualization_bytes = gemini.generate_garden_visualization_with_gemini(
            image_bytes=image_bytes,
            plants=plants_list,
            recommendations=recommendations,
        )

        if not visualization_bytes:
            raise RuntimeError("AI visualization generation failed.")

        # Upload the visualization to GCS
        blob_name = f"garden_{garden.id}/visualization_{uuid.uuid4()}.jpg"
        visualization_url = gcs.upload_to_gcs(visualization_bytes, blob_name)

        # Find or create a GardenVisualization record
        db_visualization = db.query(models.GardenVisualization).filter(
            models.GardenVisualization.garden_id == garden.id
        ).first()

        if db_visualization:
            db_visualization.image_url = visualization_url
        else:
            db_visualization = models.GardenVisualization(
                garden_id=garden.id,
                image_url=visualization_url,
            )
            db.add(db_visualization)
            
        db.commit()

        logger.info(f"Successfully generated and saved visualization for update {update_id}")

    finally:
        db.close()


@activity.defn
def mark_workflow_failed(update_id: int) -> None:
    db = _get_db()
    try:
        logger.info(f"Activity: MARK_WORKFLOW_FAILED for update {update_id}")
        update = db.query(models.GardenUpdate).filter(models.GardenUpdate.id == update_id).first()
        if update:
            update.status = "Failed"
            update.upload_commentry = "There was an issue in the backend, but your garden will be created shortly."
            if update.garden:
                update.garden.status = "Failed"
            db.commit()
    finally:
        db.close()

