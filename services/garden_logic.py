import uuid
from sqlalchemy.orm import Session
import models
from services import gcs, gemini
from utils import image as image_utils

async def process_garden_photo(db: Session, garden_id: int, update_id: int, file_content: bytes, filename: str):
    """
    Handles the full processing pipeline for a single garden photo:
    1. Upload original photo to GCS.
    2. Create GardenPhoto record.
    3. Run Gemini identification.
    4. Create Plant entries.
    5. Crop and upload plant images.
    """
    # 1. Upload original to GCS
    unique_filename = f"garden_{garden_id}/{uuid.uuid4()}_{filename}"
    original_url = gcs.upload_to_gcs(file_content, unique_filename)
    
    # 2. Create photo record
    db_photo = models.GardenPhoto(
        garden_id=garden_id,
        update_id=update_id,
        photo_url=original_url
    )
    db.add(db_photo)
    db.commit()

    # 3. Identify plants
    identified_plants = gemini.identify_plants_with_gemini(file_content)
    
    for plant_data in identified_plants:
        # Create entry in plant table
        db_plant = models.Plant(
            garden_id=garden_id,
            name=plant_data["name"],
            plant_variety=plant_data["variety"],
            condition=plant_data["condition"]
        )
        db.add(db_plant)
        db.commit()
        db.refresh(db_plant)

        # 4. Extract plant image
        if "box_2d" in plant_data:
            cropped_content = image_utils.crop_plant_image(file_content, plant_data["box_2d"])
            cropped_filename = f"garden_{garden_id}/plant+{db_plant.id}.jpg"
            cropped_url = gcs.upload_to_gcs(cropped_content, cropped_filename)
            
            # Update plant entry with URL
            db_plant.image_url = cropped_url
            db.commit()
    
    return original_url
