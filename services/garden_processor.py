"""
garden_processor.py
-------------------
Core AI processing pipeline for gardens with status 'New'.

Pipeline per garden:
  New → Processing Garden → Processing Plants → Ready

PlantUpdate status per plant:
  New → Processing → Ready
"""

import uuid
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
import models
from . import gcs, gemini
from utils import image as image_utils
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from database import SessionLocal

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_update_status(db: Session, update_id: int, status: str, commentary: str = None) -> None:
    update_data = {"status": status}
    if commentary is not None:
        update_data["upload_commentry"] = commentary

    db.query(models.GardenUpdate).filter(models.GardenUpdate.id == update_id).update(update_data)
    # Also update parent garden status to reflect latest progress
    db_update = db.query(models.GardenUpdate).filter(models.GardenUpdate.id == update_id).first()
    if db_update:
        db.query(models.Garden).filter(models.Garden.id == db_update.garden_id).update(
            {"status": status, "updated_at": datetime.datetime.utcnow()}
        )
    db.commit()
    logger.info(f"Update {update_id} (Garden {db_update.garden_id if db_update else '?'}) → {status}")


def _set_plant_update_status(db: Session, plant_update_id: int, status: str) -> None:
    db.query(models.PlantUpdate).filter(models.PlantUpdate.id == plant_update_id).update(
        {"status": status}
    )
    db.commit()


def _download_photo_bytes(photo_url: str) -> Optional[bytes]:
    """Download a photo from GCS given its public URL."""
    try:
        # Extract the blob path from the full GCS URL
        # URL format: https://storage.googleapis.com/{bucket}/{blob_path}
        parts = photo_url.split("storage.googleapis.com/", 1)
        if len(parts) < 2:
            return None
        blob_path = parts[1].split("/", 1)[-1]  # strip bucket name
        return gcs.download_from_gcs(blob_path)
    except Exception as e:
        logger.warning(f"Could not download photo {photo_url}: {e}")
        return None


def _find_or_create_plant(db: Session, garden_id: int, plant_name: str, variety: str, condition: str) -> models.Plant:
    """
    Case-insensitive match against existing plants in the garden.
    Creates a new Plant row if no match is found.
    """
    existing = (
        db.query(models.Plant)
        .filter(models.Plant.garden_id == garden_id)
        .all()
    )
    name_lower = plant_name.strip().lower()
    for plant in existing:
        if plant.name.strip().lower() == name_lower:
            # Update variety/condition if more detail is now available
            plant.plant_variety = variety or plant.plant_variety
            plant.condition = condition or plant.condition
            db.commit()
            return plant

    # New plant
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


def _get_last_garden_recommendation(db: Session, garden_id: int, current_update_id: int) -> Optional[str]:
    """Return the recommendation text from the most recent *previous* GardenUpdate."""
    last = (
        db.query(models.GardenUpdate)
        .filter(
            models.GardenUpdate.garden_id == garden_id,
            models.GardenUpdate.id != current_update_id,
            models.GardenUpdate.recommendation.isnot(None),
        )
        .order_by(models.GardenUpdate.created_at.desc())
        .first()
    )
    return last.recommendation if last else None


def _get_last_plant_recommendation(db: Session, plant_id: int) -> Optional[str]:
    """Return the recommendation from the most recent PlantUpdate for this plant."""
    last = (
        db.query(models.PlantUpdate)
        .filter(
            models.PlantUpdate.plant_id == plant_id,
            models.PlantUpdate.recommendation.isnot(None),
            models.PlantUpdate.status == "Ready",
        )
        .order_by(models.PlantUpdate.created_at.desc())
        .first()
    )
    return last.recommendation if last else None


# ---------------------------------------------------------------------------
# Per-plant processing
# ---------------------------------------------------------------------------

def _process_single_plant(
    garden_id: int,
    plant_data: dict,
    image_contents: list[bytes],
) -> None:
    """
    For one identified plant:
    1. Crop photo using bounding box → upload to GCS
    2. Find or create Plant row
    3. Create PlantUpdate (New → Processing → Ready)
    """
    db: Session = SessionLocal()
    try:
        plant_name = plant_data.get("name", "Unknown Plant")

        # --- Update Commentary ---
        logger.info(f"[{garden_id}] Starting plant processing for a plant...")
        latest_update = db.query(models.GardenUpdate).filter(models.GardenUpdate.garden_id == garden_id).order_by(models.GardenUpdate.created_at.desc()).first()
        if latest_update:
            latest_update.upload_commentry = f"analyzing {plant_name}"
            db.commit()

        variety = plant_data.get("variety", "")
        condition = plant_data.get("condition", "")

        # --- Crop image ---
        photo_idx = plant_data.get("photo_index", 0)
        cropped_bytes: Optional[bytes] = None
        source = image_contents[photo_idx] if photo_idx < len(image_contents) else (image_contents[0] if image_contents else None)

        if source:
            if "box_2d" in plant_data:
                cropped_bytes = image_utils.crop_plant_image(source, plant_data["box_2d"])
                if not cropped_bytes:
                    logging.info(f"Could not get a clear crop for '{plant_name}' — will use full photo as fallback.")
                    cropped_bytes = source
            else:
                logging.info(f"No box_2d for '{plant_name}' — using full source photo as cutout.")
                cropped_bytes = source
        else:
            logging.warning(f"No source image available for plant '{plant_name}'.")

        # --- Upload cropped image ---
        cropped_url: Optional[str] = None
        if cropped_bytes:
            logger.info(f"[{garden_id}] Uploading cutout for {plant_name}...")
            blob_name = f"garden_{garden_id}/plant_{uuid.uuid4()}.jpg"
            cropped_url = gcs.upload_to_gcs(cropped_bytes, blob_name)

        # --- Find or create Plant ---
        db_plant = _find_or_create_plant(db, garden_id, plant_name, variety, condition)

        # --- Create PlantUpdate (status=New) ---
        db_plant_update = models.PlantUpdate(
            plant_id=db_plant.id,
            condition_text=condition,
            image_url=cropped_url,
            status="New",
        )
        db.add(db_plant_update)
        db.commit()
        db.refresh(db_plant_update)

        # --- Transition to Processing ---
        _set_plant_update_status(db, db_plant_update.id, "Processing")

        # --- Fetch previous recommendation for comparison ---
        last_recommendation = _get_last_plant_recommendation(db, db_plant.id)

        # --- Call Gemini for detailed plant diagnosis ---
        analysis_bytes = cropped_bytes or (image_contents[photo_idx] if photo_idx < len(image_contents) else b"")
        if analysis_bytes:
            logger.info(f"[{garden_id}] Running detailed Gemini analysis for {plant_name}...")
            analysis = gemini.analyze_plant_detail(
                plant_image_bytes=analysis_bytes,
                plant_name=plant_name,
                last_plant_recommendation=last_recommendation,
            )
        else:
            analysis = {}

        # --- Check if it's a valid plant ---
        is_valid = analysis.get("is_valid_plant")
        if is_valid is False or str(is_valid).lower() == "false":
            logging.info(f"Deleting false positive plant '{plant_name}' as no plant material was detected in details.")
            db.delete(db_plant)
            db.commit()
            return

        # --- Build recommendation text ---
        recommendation = (
            f"Soil Quality: {analysis.get('soil_quality', 'N/A')}\n"
            f"Disease: {analysis.get('disease', 'N/A')}\n"
            f"Pot Assessment: {analysis.get('pot_assessment', 'N/A')}\n"
            f"Pruning Needed: {analysis.get('pruning_needed', 'N/A')}\n"
            f"Growth Comparison: {analysis.get('growth_comparison', 'First assessment')}\n"
            f"Recommendation: {analysis.get('recommendation', 'N/A')}"
        )

        # --- Update PlantUpdate with full diagnosis ---
        db_plant_update.condition_text = analysis.get("disease", condition) or condition
        db_plant_update.recommendation = recommendation
        db.commit()

        # --- Update Plant image if better one now available ---
        if cropped_url:
            db_plant.image_url = cropped_url
            db.commit()

        # --- Transition PlantUpdate to Ready ---
        _set_plant_update_status(db, db_plant_update.id, "Ready")
        logger.info(f"Plant '{plant_name}' (id={db_plant.id}) update complete → Ready")
    except Exception as e:
        db.rollback()
        logger.error(f"Error in _process_single_plant: {e}")
        raise e
    finally:
        db.close()



# ---------------------------------------------------------------------------
# Main garden pipeline
# ---------------------------------------------------------------------------

def process_single_update(db: Session, update: models.GardenUpdate) -> None:
    """
    Run the full AI processing pipeline for one specific update session.
    Updates statuses on the GardenUpdate record.
    """
    garden_id = update.garden_id
    update_id = update.id
    logger.info(f"--- Processing update {update_id} for garden {garden_id} ---")

    # ── Step 1: Processing Garden ─────────────────────────────────────────
    _set_update_status(db, update_id, "Processing Garden")

    latest_update = update

    if not latest_update:
        logger.warning(f"Update {update_id} not found. Skipping.")
        return

    # Download all photos for this update
    photos = (
        db.query(models.GardenPhoto)
        .filter(models.GardenPhoto.update_id == latest_update.id)
        .all()
    )
    if not photos:
        logger.warning(f"Garden update {latest_update.id} has no photos. Skipping.")
        _set_update_status(db, update_id, "Ready")
        return

    image_contents: list[bytes] = []
    for photo in photos:
        data = _download_photo_bytes(photo.photo_url)
        if data:
            image_contents.append(data)

    if not image_contents:
        logger.warning(f"Could not download any photos for garden {garden_id}. Skipping.")
        _set_update_status(db, update_id, "Ready")
        return

    try:
        # ── Garden Overview AI ────────────────────────────────────────────────
        latest_update.upload_commentry = "assessing garden condition"
        db.commit()
        
        last_garden_recommendation = _get_last_garden_recommendation(
            db, garden_id, latest_update.id
        )

        logger.info(f"Running garden overview AI for garden {garden_id}...")
        overview = gemini.analyze_garden_overview(
            image_list=image_contents,
            last_update_recommendation=last_garden_recommendation,
        )

        if not overview:
             raise Exception("AI Overview failed (likely API error)")

        latest_update.summary = overview.get('summary', 'No summary available')
        latest_update.immediate_changes = overview.get('immediate_changes')
        latest_update.disease_overview = overview.get('disease_overview')
        latest_update.growth_trend = overview.get('growth_trend')
        latest_update.recommendation = overview.get('general_suggestions')
        latest_update.hydration = overview.get('hydration')
        latest_update.exposure = overview.get('exposure')
        latest_update.vibrancy = overview.get('vibrancy')
        latest_update.temperature = overview.get('temperature')
        latest_update.humidity = overview.get('humidity')
        
        # Also update the main garden summary for the list view
        db_garden = db.query(models.Garden).filter(models.Garden.id == garden_id).first()
        if db_garden:
            db_garden.summary = latest_update.summary
            
        db.commit()

        # New: Get binary details for tickers
        logger.info(f"Getting binary details for garden {garden_id}...")
        ticker_details = gemini.analyze_garden_tickers(image_list=image_contents)
        
        if ticker_details:
            latest_update.has_pests = ticker_details.get('has_pests', False)
            latest_update.has_disease = ticker_details.get('has_disease', False)
            latest_update.needs_watering = ticker_details.get('needs_watering', False)
            latest_update.needs_fertilizing = ticker_details.get('needs_fertilizing', False)

        db.commit()

        # ── Step 2: Processing Plants ─────────────────────────────────────────
        _set_update_status(db, update_id, "Processing Plants", commentary="identifying plants")

        # Identify plants from all photos
        logger.info(f"Identifying plants for garden {garden_id}...")
        plants_list, suggested_name = gemini.identify_plants_with_gemini(image_contents)

        if not plants_list and not suggested_name:
             # If both are empty, it might be an AI failure or just no plants found. 
             # We check identify_plants_with_gemini implementation (it returns [] on error).
             # To be safe, we only throw if we expected something or if the function explicitly failed.
             pass

        # Optionally update garden name if it's still generic and Gemini has a better one
        db_garden = db.query(models.Garden).filter(models.Garden.id == garden_id).first()
        if suggested_name and db_garden and db_garden.name in ("My Garden", ""):
            db_garden.name = suggested_name
            db.commit()

        # Process plants sequentially for stability and to avoid DB connection conflicts
        if plants_list:
            logger.info(f"Processing {len(plants_list)} plants sequentially...")
            for plant_data in plants_list:
                try:
                    _process_single_plant(garden_id, plant_data, image_contents)
                except Exception as e:
                    logger.error(f"Error processing plant: {e}")
                
        # --- Finalize ---
        _set_update_status(db, update_id, "Ready", commentary="done")

    except Exception as e:
        db.rollback()
        logger.error(f"Error in process_single_update for garden {garden_id}: {e}")
        try:
             _set_update_status(db, update_id, "Failed", commentary=f"AI Error: {str(e)[:100]}")
        except:
             pass
        raise e

def _run_update_in_thread(update_id: int) -> None:
    """Wrapper to process a single garden update in its own DB session."""
    db: Session = SessionLocal()
    try:
        update = db.query(models.GardenUpdate).filter(models.GardenUpdate.id == update_id).first()
        if not update:
            logger.warning(f"Thread: Update {update_id} not found.")
            return

        # Status is still "Ready to Process"? Proceed.
        if update.status != "Ready to Process":
            return
            
        process_single_update(db, update)
    except Exception as e:
        logger.error(f"Unhandled error processing update {update_id} in thread: {e}")
        try:
            # Set to Failed first to log the error, then back to Ready to Process so next cron picks it up
            _set_update_status(db, update_id, "Failed", commentary=f"AI Error: {str(e)[:100]}")
            # Optional: Add a delay or only reset to Ready to Process if retry count < threshold
            db.query(models.GardenUpdate).filter(models.GardenUpdate.id == update_id).update({"status": "Ready to Process"})
            db.commit()
        except Exception:
            pass
    finally:
        db.close()

def process_new_gardens(db: Session) -> int:
    """
    Entry point for the cronjob.
    Finds all garden updates with status='Ready to Process' and processes them.
    """
    new_updates = (
        db.query(models.GardenUpdate)
        .filter(models.GardenUpdate.status == "Ready to Process")
        .all()
    )

    if not new_updates:
        logger.info("No garden updates with status='Ready to Process' found.")
        return 0

    update_ids = [update.id for update in new_updates]
    logger.info(f"Found {len(update_ids)} update(s) to process. Starting execution...")
    
    # Process sequentially for now as multi-threading had issues
    for uid in update_ids:
        try:
            _run_update_in_thread(uid)
        except Exception as e:
            logger.error(f"Execution failed for update {uid}: {e}")

    return len(update_ids)
