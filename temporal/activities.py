
import logging
import uuid
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
        logger.info(f"Running garden overview AI for garden {garden_id}...")
        overview = gemini.analyze_garden_overview(image_list=image_contents)
        if not overview:
            raise RuntimeError("AI Overview analysis failed.")

        update.summary = overview.get('summary')
        update.recommendation = overview.get('general_suggestions')
        db.commit()

        activity.heartbeat()
        logger.info(f"Identifying plants for garden {garden_id}...")
        existing_plants_db = db.query(models.Plant).filter(models.Plant.garden_id == garden_id).all()
        existing_plant_names = [p.name for p in existing_plants_db]
        plants_list, _ = gemini.identify_plants_with_gemini(image_contents, existing_plants=existing_plant_names)

        return {"plants_list": plants_list, "garden_id": garden_id}
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
def gather_plant_details(plant_update_id: int) -> None:
    db = _get_db()
    try:
        logger.info(f"Activity 3: GATHER_PLANT_DETAILS for plant_update {plant_update_id}")
        activity.heartbeat()

        db_plant_update = db.query(models.PlantUpdate).filter(models.PlantUpdate.id == plant_update_id).first()
        if not db_plant_update:
            raise ValueError(f"PlantUpdate {plant_update_id} not found.")

        db_plant = db_plant_update.plant
        if not db_plant or not db_plant_update.image_url:
            logger.warning(f"Plant or image_url missing for update {plant_update_id}. Skipping.")
            return

        analysis_bytes = _download_photo_bytes(db_plant_update.image_url)
        if not analysis_bytes:
            raise ValueError(f"Could not download image for plant update {plant_update_id}")

        last_recommendation, last_condition = _get_last_plant_update_details(db, db_plant.id)

        activity.heartbeat()
        analysis = gemini.analyze_plant_detail(
            plant_image_bytes=analysis_bytes,
            plant_name=db_plant.name,
            last_plant_recommendation=last_recommendation,
            last_plant_condition=last_condition,
        )

        if not analysis.get("is_valid_plant"):
            logger.info(f"Deleting false positive plant '{db_plant.name}'.")
            db.delete(db_plant)
            db.commit()
            return

        recommendation = f"Recommendation: {analysis.get('recommendation', 'N/A')}"
        db_plant_update.condition_text = analysis.get("disease", db_plant.condition)
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

        # Re-run plant identification to get bounding boxes
        image_contents = [image_bytes]
        existing_plant_names = [p.name for p in plants]
        plants_list, _ = gemini.identify_plants_with_gemini(image_contents, existing_plants=existing_plant_names)


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

        # Create a new GardenVisualization record
        db_visualization = models.GardenVisualization(
            garden_id=garden.id,
            update_id=update_id,
            image_url=visualization_url,
        )
        db.add(db_visualization)
        db.commit()

        logger.info(f"Successfully generated and saved visualization for update {update_id}")

    finally:
        db.close()
