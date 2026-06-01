from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import datetime

from database import engine, Base, get_db
import models, schemas
import queue
import threading
import logging
from fastapi.responses import StreamingResponse
from services import auth, gcs, gemini, garden_processor
from utils import image as image_utils

# Create database tables if they don't exist
try:
    print("Connecting to database and creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables verified/created successfully.")
except Exception as e:
    print(f"WARNING: Could not connect to database or create tables on startup: {e}")
    print("Continuing startup... DB connection will be retried on first request.")

app = FastAPI(title="Garden Backend API")

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static images directory for local photo serving
if not os.path.exists("static_images"):
    os.makedirs("static_images")
app.mount("/static", StaticFiles(directory="static_images"), name="static")

@app.get("/")
def read_root():
    return {"message": "Welcome to Garden API"}

# 1. Login Endpoint
@app.post("/auth/login", response_model=schemas.Token)
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user, token = auth.authenticate_external_user(db, login_data)
    return {"access_token": token, "token_type": "bearer"}

# New: Simple Email Authentication (returns user_id)
@app.post("/auth/email")
def login_with_email(login_data: schemas.UserEmailLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_email == login_data.email).first()
    if not user:
        # Create new user if not found
        user = models.User(user_email=login_data.email)
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"user_id": user.id, "email": user.user_email}

# 2, 3, 4. Garden Creation & Photo Upload Endpoint (legacy – requires explicit name)
@app.post("/gardens", response_model=schemas.GardenResponse)
async def create_garden(
    name: str = Form(...),
    photos: List[UploadFile] = File(...),
    user_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    # Create new entry in garden table
    db_garden = models.Garden(name=name, status="New")
    db.add(db_garden)
    db.commit()
    db.refresh(db_garden)

    # Create ONE garden update for this session
    db_update = models.GardenUpdate(garden_id=db_garden.id, status="New")
    db.add(db_update)
    db.commit()
    db.refresh(db_update)

    # Standardize on asynchronous processing: upload photos to GCS 
    # and let the cronjob handle AI analysis.
    for photo in photos:
        content = await photo.read()
        unique_filename = f"garden_{db_garden.id}/{uuid.uuid4()}_{photo.filename}"
        url = gcs.upload_to_gcs(content, unique_filename)
        
        db_photo = models.GardenPhoto(
            garden_id=db_garden.id,
            update_id=db_update.id,
            photo_url=url
        )
        db.add(db_photo)
    db.commit()

    db.refresh(db_garden)

    # Build response with garden_update_id
    db.commit()
    db.refresh(db_garden)

    # Ensure user-garden association if user_id provided
    if user_id is not None:
        db_user = db.query(models.User).get(user_id)
        if db_user and db_user not in db_garden.users:
            db_garden.users.append(db_user)
            db.commit()
            db.refresh(db_garden)

    # Return response
    response = schemas.GardenResponse.from_orm(db_garden)
    response.garden_update_id = db_update.id
    return response


# New: Upload photos – auto-create garden if garden_id not provided
@app.post("/gardens/upload", response_model=schemas.GardenResponse)
async def upload_garden_photos(
    photos: List[UploadFile] = File(...),
    garden_id: Optional[int] = Form(None),
    garden_name: Optional[str] = Form(None),
    user_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload multiple garden photos and create a new garden update entry.

    - If **garden_id** is provided: uses an existing garden (returns 404 if not found).
    - If **garden_id** is omitted: creates a new garden (name defaults to 'My Garden'
      if garden_name is also omitted). Optionally associates it with a user via user_id.

    Garden status transitions during processing:
      New → Processing Garden → Processing Plants → Ready
    """
    if garden_id is not None:
        # Use existing garden
        db_garden = db.query(models.Garden).filter(models.Garden.id == garden_id).first()
        if not db_garden:
            raise HTTPException(status_code=404, detail=f"Garden with id {garden_id} not found")
    else:
        # Auto-create a new garden
        name = garden_name or "My Garden"
        db_garden = models.Garden(name=name, status="New")
        db.add(db_garden)
        db.commit()
        db.refresh(db_garden)



    # Create a garden update entry for this upload session
    # Initial status is "Uploading" to prevent the cronjob from picking it up mid-upload
    db_update = models.GardenUpdate(garden_id=db_garden.id, status="Uploading")
    db.add(db_update)
    db.commit()
    db.refresh(db_update)

    # Standardize on asynchronous processing: upload photos to GCS 
    # and let the cronjob handle AI analysis.
    for photo in photos:
        content = await photo.read()
        unique_filename = f"garden_{db_garden.id}/{uuid.uuid4()}_{photo.filename}"
        url = gcs.upload_to_gcs(content, unique_filename)
        
        db_photo = models.GardenPhoto(
            garden_id=db_garden.id,
            update_id=db_update.id,
            photo_url=url
        )
        db.add(db_photo)
    db.commit()
    db.refresh(db_garden)

    # Ensure user-garden association if user_id provided
    if user_id is not None:
        db_user = db.query(models.User).get(user_id)
        if db_user and db_user not in db_garden.users:
            db_garden.users.append(db_user)
            db.commit()
            db.refresh(db_garden)

    # ALL photos are now uploaded and DB records created.
    # Set status to "Ready to Process" so the cronjob can finally pick it up safely.
    db_update.status = "Ready to Process"
    db.commit()

    response = schemas.GardenResponse.from_orm(db_garden)
    response.garden_update_id = db_update.id
    return response

# New: Push photos to an existing update
@app.post("/updates/{update_id}/photos")
async def push_photos_to_update(
    update_id: int,
    photos: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    db_update = db.query(models.GardenUpdate).filter(models.GardenUpdate.id == update_id).first()
    if not db_update:
        raise HTTPException(status_code=404, detail="Garden update not found")
    
    # Standardize on asynchronous processing: upload photos to GCS 
    # and let the cronjob handle AI analysis.
    for photo in photos:
        content = await photo.read()
        unique_filename = f"garden_{db_update.garden_id}/{uuid.uuid4()}_{photo.filename}"
        url = gcs.upload_to_gcs(content, unique_filename)
        
        db_photo = models.GardenPhoto(
            garden_id=db_update.garden_id,
            update_id=update_id,
            photo_url=url
        )
        db.add(db_photo)
    
    # Set status to Ready to Process so cronjob picks it up
    db_update.status = "Ready to Process"
    db.commit()
    
    return {"message": "Photos added and processed", "update_id": update_id, "count": len(photos)}

# 5. Return List of Plants
@app.get("/gardens/{garden_id}/plants", response_model=List[schemas.PlantResponse])
def get_garden_plants(garden_id: int, db: Session = Depends(get_db)):
    plants = db.query(models.Plant).filter(models.Plant.garden_id == garden_id).all()
    if not plants:
        raise HTTPException(status_code=404, detail="No plants found for this garden")
    return plants

# New: Get garden details including its plants
@app.get("/gardens/{garden_id}/details", response_model=schemas.GardenDetailsResponse)
def get_garden_details(garden_id: int, db: Session = Depends(get_db)):
    garden = db.query(models.Garden).filter(models.Garden.id == garden_id).first()
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")
    
    plant_responses = []
    for plant in garden.plants:
        # Get latest update for this specific plant
        latest_update = db.query(models.PlantUpdate).filter(
            models.PlantUpdate.plant_id == plant.id
        ).order_by(models.PlantUpdate.created_at.desc()).first()
        
        # Use image_url from update if available, otherwise from plant
        image_url = latest_update.image_url if (latest_update and latest_update.image_url) else plant.image_url
        
        plant_responses.append(schemas.PlantLatestUpdateResponse(
            id=plant.id,
            name=plant.name,
            plant_variety=plant.plant_variety,
            image_url=image_url,
            latest_condition=latest_update.condition_text if latest_update else None,
            latest_recommendation=latest_update.recommendation if latest_update else None,
            last_update_date=latest_update.created_at if latest_update else None
        ))
    
    # Get latest garden-level recommendation from updates
    latest_update = db.query(models.GardenUpdate).filter(
        models.GardenUpdate.garden_id == garden_id,
        models.GardenUpdate.recommendation.is_not(None)
    ).order_by(models.GardenUpdate.created_at.desc()).first()

    recommendation_full = latest_update.recommendation if latest_update else None
    recommendation_truncated = None
    if recommendation_full:
        words = recommendation_full.split()
        if len(words) > 10:
            recommendation_truncated = " ".join(words[:10]) + "..."
        else:
            recommendation_truncated = recommendation_full

    return {
        "id": garden.id,
        "name": garden.name,
        "status": garden.status,
        "recommendation": recommendation_truncated,
        "recommendation_full": recommendation_full,
        "needs_watering": latest_update.needs_watering if latest_update else None,
        "needs_fertilizer": latest_update.needs_fertilizer if latest_update else None,
        "has_pests": latest_update.has_pests if latest_update else None,
        "has_weeds": latest_update.has_weeds if latest_update else None,
        "has_disease": latest_update.has_disease if latest_update else None,
        "needs_sunlight": latest_update.needs_sunlight if latest_update else None,
        "created_at": garden.created_at,
        "plants": plant_responses
    }

# New: Get all gardens for a specific user
@app.get("/users/{user_id}/gardens", response_model=List[schemas.GardenResponse])
def get_user_gardens(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.gardens

# New: Get all gardens for a specific user with their photos
@app.get("/users/{user_id}/gardens/detailed", response_model=List[schemas.GardenWithPhotosResponse])
def get_user_gardens_detailed(user_id: int, db: Session = Depends(get_db)):
    try:
        # Fetch gardens for the user, ordered by created_at DESC
        gardens = db.query(models.Garden).join(models.garden_users).filter(
            models.garden_users.c.user_id == user_id
        ).order_by(models.Garden.created_at.desc()).all()

        if not gardens:
            # Check if user exists but has no gardens
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return []

        results = []
        for garden in gardens:
            # Get latest recommendation (where recommendation is not null)
            latest_update_with_rec = db.query(models.GardenUpdate).filter(
                models.GardenUpdate.garden_id == garden.id,
                models.GardenUpdate.recommendation.is_not(None)
            ).order_by(models.GardenUpdate.created_at.desc()).first()

            # Get the absolute latest update for processing commentary
            latest_overall_update = db.query(models.GardenUpdate).filter(
                models.GardenUpdate.garden_id == garden.id
            ).order_by(models.GardenUpdate.created_at.desc()).first()

            # Get plants with their latest updates
            plant_responses = []
            for plant in garden.plants:
                latest_p_update = db.query(models.PlantUpdate).filter(
                    models.PlantUpdate.plant_id == plant.id
                ).order_by(models.PlantUpdate.created_at.desc()).first()

                plant_responses.append({
                    "id": plant.id,
                    "name": plant.name,
                    "plant_variety": plant.plant_variety,
                    "image_url": plant.image_url,
                    "latest_condition": latest_p_update.condition_text if latest_p_update else None,
                    "latest_recommendation": latest_p_update.recommendation if latest_p_update else None,
                    "last_update_date": latest_p_update.created_at if latest_p_update else None
                })

            # Explicitly map photos to avoid lazy-loading issues during serialization
            photo_responses = []
            for photo in garden.photos:
                photo_responses.append({
                    "id": photo.id,
                    "photo_url": photo.photo_url,
                    "created_at": photo.created_at
                })

            results.append({
                "id": garden.id,
                "name": garden.name,
                "status": garden.status,
                "summary": garden.summary,
                "upload_commentry": getattr(latest_overall_update, 'upload_commentry', None),
                "recommendation": getattr(latest_update_with_rec, 'recommendation', None),
                "created_at": garden.created_at,
                "photos": photo_responses,
                "plants": plant_responses
            })
        return results
    except Exception as e:
        print(f"ERROR in get_user_gardens_detailed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# New: Get all health updates for a specific plant
@app.get("/plants/{plant_id}/updates", response_model=List[schemas.PlantUpdateResponse])
def get_plant_updates(plant_id: int, db: Session = Depends(get_db)):
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant.updates

@app.put("/gardens/{garden_id}/access")
def update_garden_access(garden_id: int, db: Session = Depends(get_db)):
    """Update the last_accessed_at timestamp for a garden."""
    garden = db.query(models.Garden).filter(models.Garden.id == garden_id).first()
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")
    garden.last_accessed_at = datetime.datetime.utcnow()
    db.commit()
    return {"status": "ok"}

@app.get("/gardens/{garden_id}/environment")
def get_garden_environment(garden_id: int, db: Session = Depends(get_db)):
    """Return the latest environment metrics (hydration, exposure, vibrancy) for a garden."""
    garden = db.query(models.Garden).filter(models.Garden.id == garden_id).first()
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")
    latest_update = (
        db.query(models.GardenUpdate)
        .filter(
            models.GardenUpdate.garden_id == garden_id,
            models.GardenUpdate.hydration.isnot(None),
        )
        .order_by(models.GardenUpdate.created_at.desc())
        .first()
    )
    if not latest_update:
        return {"hydration": None, "exposure": None, "vibrancy": None, "temperature": None, "humidity": None}
    return {
        "hydration": latest_update.hydration,
        "exposure": latest_update.exposure,
        "vibrancy": latest_update.vibrancy,
        "temperature": latest_update.temperature or "24°C",
        "humidity": latest_update.humidity or "60%"
    }

@app.delete("/gardens/{garden_id}")
def delete_garden(garden_id: int, db: Session = Depends(get_db)):
    """Delete a garden and all associated plants, photos, and updates."""
    garden = db.query(models.Garden).filter(models.Garden.id == garden_id).first()
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")
    
    db.delete(garden)
    db.commit()
    return {"status": "ok", "message": f"Garden {garden_id} deleted successfully"}

class LogQueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        log_entry = self.format(record)
        self.log_queue.put(log_entry)

@app.api_route("/jobs/process", methods=["GET", "POST"])
async def trigger_garden_processing(stream: bool = True, db: Session = Depends(get_db)):
    """
    Trigger the garden AI processing pipeline.
    - stream=true (default): Streams logs via SSE. HTTP status is 200 as long as the stream starts.
    - stream=false: Runs synchronously. Returns 200 on success, or 500 with details on failure.
    """
    if not stream:
        try:
            logging.info("Sync Trigger: Starting garden processing job...")
            count = garden_processor.process_new_gardens(db)
            logging.info(f"Sync Trigger: Finished processing {count} garden(s).")
            return {"status": "success", "processed_count": count}
        except Exception as e:
            logging.error(f"Sync Trigger ERROR: {str(e)}")
            import traceback
            error_details = traceback.format_exc()
            raise HTTPException(
                status_code=500,
                detail={
                    "error": str(e),
                    "traceback": error_details
                }
            )

    # --- SSE Streaming Mode ---
    log_queue = queue.Queue()
    queue_handler = LogQueueHandler(log_queue)
    queue_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    
    # Capture logs from the entire application to provide detailed feedback
    root_logger = logging.getLogger()
    root_logger.addHandler(queue_handler)

    def run_processing():
        try:
            logging.info("SSE Stream: Starting garden processing job...")
            # Use a new session to avoid thread safety issues
            from database import SessionLocal
            thread_db = SessionLocal()
            try:
                count = garden_processor.process_new_gardens(thread_db)
                logging.info(f"SSE Stream: Finished processing {count} garden(s).")
            finally:
                thread_db.close()
        except Exception as e:
            logging.error(f"SSE Stream ERROR: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
        finally:
            # Signal the end of the stream
            log_queue.put(None)
            root_logger.removeHandler(queue_handler)

    # Start processing in a background thread
    threading.Thread(target=run_processing).start()

    async def log_generator():
        try:
            while True:
                try:
                    message = log_queue.get(timeout=1.0)
                    if message is None:
                        yield "data: [DONE]\n\n"
                        break
                    yield f"data: {message}\n\n"
                except queue.Empty:
                    # Keep-alive
                    yield ": keep-alive\n\n"
        except Exception as e:
            yield f"data: Error in stream: {str(e)}\n\n"

    return StreamingResponse(log_generator(), media_type="text/event-stream")
