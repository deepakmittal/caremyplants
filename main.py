from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import datetime
import asyncio

from database import engine, Base, get_db
import models, schemas
import queue
import threading
import logging
from fastapi.responses import StreamingResponse, PlainTextResponse
# Services are imported lazily inside endpoint functions to minimize container startup memory footprint

# Create database tables if they don't exist
try:
    print("Connecting to database and creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables verified/created successfully.")
    
    # Auto-migration check for box_2d column on plant_updates
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SHOW COLUMNS FROM plant_updates LIKE 'box_2d';"))
            if not res.fetchone():
                print("Adding box_2d column to plant_updates table...")
                conn.execute(text("ALTER TABLE plant_updates ADD COLUMN box_2d VARCHAR(255) NULL;"))
                conn.commit()
                print("Column box_2d added successfully.")

            # Auto-migration check for health_score and health_metrics on garden_updates
            res_score = conn.execute(text("SHOW COLUMNS FROM garden_updates LIKE 'health_score';"))
            if not res_score.fetchone():
                print("Adding health_score column to garden_updates table...")
                conn.execute(text("ALTER TABLE garden_updates ADD COLUMN health_score INT NULL;"))
                conn.commit()
                print("Column health_score added successfully.")

            res_metrics = conn.execute(text("SHOW COLUMNS FROM garden_updates LIKE 'health_metrics';"))
            if not res_metrics.fetchone():
                print("Adding health_metrics column to garden_updates table...")
                conn.execute(text("ALTER TABLE garden_updates ADD COLUMN health_metrics TEXT NULL;"))
                conn.commit()
                print("Column health_metrics added successfully.")

            # Auto-migration check for Enhance Your Garden URL columns on garden_visualizations
            for col_name in ("more_colours_url", "clean_up_url", "more_floor_space_url"):
                res_col = conn.execute(text(f"SHOW COLUMNS FROM garden_visualizations LIKE '{col_name}';"))
                if not res_col.fetchone():
                    print(f"Adding {col_name} column to garden_visualizations table...")
                    conn.execute(text(f"ALTER TABLE garden_visualizations ADD COLUMN {col_name} VARCHAR(512) NULL;"))
                    conn.commit()
                    print(f"Column {col_name} added successfully.")
    except Exception as migration_error:
        print(f"WARNING: Could not apply database migration for columns: {migration_error}")
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
    "http://localhost:8081",
    "http://127.0.0.1:8081",
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

# The root "/" route is served by the static files mount at the end of the file.

@app.get("/hello", response_class=PlainTextResponse)
def hello():
    return "hello"

@app.get("/ping")
def ping():
    return {"message": "pong"}

@app.get("/db/status")
async def get_db_status():
    # Try connecting to the database first
    try:
        from sqlalchemy import text
        from database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "online", "state": "RUNNABLE", "running": True}
    except Exception as db_err:
        print(f"Database connection check failed: {db_err}")
        
    # If connection fails and we are on Cloud Run, query the Google Cloud SQL Admin API
    if os.getenv('K_SERVICE') is not None:
        try:
            import urllib.request
            import json
            # 1. Get access token from metadata server
            req_token = urllib.request.Request(
                "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
                headers={"Metadata-Flavor": "Google"}
            )
            with urllib.request.urlopen(req_token, timeout=5) as response:
                token_data = json.loads(response.read().decode('utf-8'))
                access_token = token_data.get("access_token")
                
            # 2. Query Cloud SQL Admin API
            parts = os.getenv("INSTANCE_CONNECTION_NAME", "crawler-488903:us-central1:care-my-plants-v2").split(':')
            project = parts[0]
            instance = parts[-1]
            
            url = f"https://sqladmin.googleapis.com/sql/v1beta4/projects/{project}/instances/{instance}"
            req_get = urllib.request.Request(
                url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            with urllib.request.urlopen(req_get, timeout=5) as response:
                sql_data = json.loads(response.read().decode('utf-8'))
                state = sql_data.get("state", "UNKNOWN")
                policy = sql_data.get("settings", {}).get("activationPolicy", "UNKNOWN")
                return {
                    "status": "offline",
                    "state": state,
                    "policy": policy,
                    "running": policy == "ALWAYS" and state == "RUNNABLE"
                }
        except Exception as gcp_err:
            print(f"Failed to fetch Cloud SQL status from Google API: {gcp_err}")
            
    return {"status": "offline", "state": "STOPPED", "running": False}

@app.post("/db/start")
async def start_db():
    if os.getenv('K_SERVICE') is not None:
        try:
            import urllib.request
            import json
            
            # 1. Get access token from metadata server
            req_token = urllib.request.Request(
                "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
                headers={"Metadata-Flavor": "Google"}
            )
            with urllib.request.urlopen(req_token, timeout=5) as response:
                token_data = json.loads(response.read().decode('utf-8'))
                access_token = token_data.get("access_token")
            
            # 2. Patch Cloud SQL instance settings
            parts = os.getenv("INSTANCE_CONNECTION_NAME", "crawler-488903:us-central1:care-my-plants-v2").split(':')
            project = parts[0]
            instance = parts[-1]
            
            url = f"https://sqladmin.googleapis.com/sql/v1beta4/projects/{project}/instances/{instance}"
            data = json.dumps({
                "settings": {
                    "activationPolicy": "ALWAYS"
                }
            }).encode('utf-8')
            
            req_patch = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                method="PATCH"
            )
            with urllib.request.urlopen(req_patch, timeout=5) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                return {"status": "success", "message": "Database starting", "response": res_data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to start database: {str(e)}")
            
    return {"status": "success", "message": "Local environment simulated DB start"}


@app.get("/colour")
def colour():
    return "green"

@app.get("/deepak", response_class=PlainTextResponse)
def deepak():
    return "hi"

@app.get("/vayu", response_class=PlainTextResponse)
def vayu():
    return "hi"

@app.api_route("/echo", methods=["GET", "POST", "PUT", "DELETE"])
async def echo(request: Request):
    """
    Echo back information about the request.
    """
    response_data = {
        "message": "Echo response",
        "method": request.method,
        "path": request.url.path,
        "headers": dict(request.headers),
        "client": {
            "host": request.client.host,
            "port": request.client.port,
        },
    }
    if request.method in ["POST", "PUT"]:
        try:
            response_data["json_payload"] = await request.json()
        except Exception:
            response_data["body"] = (await request.body()).decode("utf-8")

    return response_data

# 1. Login Endpoint
@app.post("/auth/login", response_model=schemas.Token)
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    from services import auth
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
    from services import gcs
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
    background_tasks: BackgroundTasks,
    garden_id: Optional[int] = Form(None),
    garden_name: Optional[str] = Form(None),
    user_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload multiple garden photos to create a new garden update and automatically trigger the complete AI analysis workflow. This single action initiates garden and plant analysis, health assessment, and the generation of a visualization with product recommendations.

    - If **garden_id** is provided: creates a new update for an existing garden (returns 404 if not found).
    - If **garden_id** is omitted: creates a new garden (name defaults to 'My Garden' if garden_name is also omitted). Optionally associates it with a user via user_id.

    The response will include a `workflow_id` for the background job. The final results of the analysis, including the visualization, can be retrieved from the `GET /gardens/{garden_id}/details` endpoint once the garden's status is 'Ready'.
    """
    from services import gcs
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

    # Set status to "Processing" and trigger the workflow
    db_update.status = "Processing"
    db.commit()

    # Trigger Temporal workflow in the background
    from temporal.client import start_garden_processing_workflow
    background_tasks.add_task(start_garden_processing_workflow, db_update.id)

    response = schemas.GardenResponse.from_orm(db_garden)
    response.garden_update_id = db_update.id
    response.workflow_id = f"garden-update-{db_update.id}"
    return response

# New: Push photos to an existing update
@app.post("/updates/{update_id}/photos")
async def push_photos_to_update(
    update_id: int,
    photos: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    from services import gcs
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
    
    # Set status to Processing so cronjob picks it up
    db_update.status = "Processing"
    db.commit()

    # Trigger Temporal workflow in the background
    from temporal.client import start_garden_processing_workflow
    background_tasks.add_task(start_garden_processing_workflow, update_id)
    
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
    from services import health_service

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
    latest_garden_update = db.query(models.GardenUpdate).filter(
        models.GardenUpdate.garden_id == garden_id,
        models.GardenUpdate.recommendation.is_not(None)
    ).order_by(models.GardenUpdate.created_at.desc()).first()

    recommendation_full = latest_garden_update.recommendation if latest_garden_update else None
    recommendation_truncated = None
    if recommendation_full:
        words = recommendation_full.split()
        if len(words) > 10:
            recommendation_truncated = " ".join(words[:10]) + "..."
        else:
            recommendation_truncated = recommendation_full

    # --- NEW: Calculate Health Overview ---
    health_overview = health_service.calculate_garden_health(garden)

    return {
        "id": garden.id,
        "name": garden.name,
        "status": garden.status,
        "recommendation": recommendation_truncated,
        "recommendation_full": recommendation_full,
        "needs_watering": latest_garden_update.needs_watering if latest_garden_update else None,
        "needs_fertilizer": latest_garden_update.needs_fertilizer if latest_garden_update else None,
        "has_pests": latest_garden_update.has_pests if latest_garden_update else None,
        "has_weeds": latest_garden_update.has_weeds if latest_garden_update else None,
        "has_disease": latest_garden_update.has_disease if latest_garden_update else None,
        "needs_sunlight": latest_garden_update.needs_sunlight if latest_garden_update else None,
        "created_at": garden.created_at,
        "plants": plant_responses,
        "healthOverview": health_overview,
        "visualization": garden.visualization
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
                    "image_url": latest_p_update.image_url if (latest_p_update and latest_p_update.image_url) else plant.image_url,
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

            from services import health_service
            health_overview = health_service.calculate_garden_health(garden)

            results.append({
                "id": garden.id,
                "name": garden.name,
                "status": garden.status,
                "summary": garden.summary,
                "upload_commentry": getattr(latest_overall_update, 'upload_commentry', None),
                "recommendation": getattr(latest_update_with_rec, 'recommendation', None),
                "created_at": garden.created_at,
                "photos": photo_responses,
                "plants": plant_responses,
                "healthOverview": health_overview
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

# New: Upload a better photo for a specific plant
@app.post("/plants/{plant_id}/photos")
async def upload_plant_photo(
    plant_id: int,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    from services import gcs
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    content = await photo.read()
    unique_filename = f"garden_{plant.garden_id}/plant_{plant_id}_{uuid.uuid4()}_{photo.filename}"
    url = gcs.upload_to_gcs(content, unique_filename)

    # Create a new PlantUpdate with status Ready to Process so the cronjob can pick it up
    db_update = models.PlantUpdate(
        plant_id=plant_id,
        image_url=url,
        status="Ready to Process"
    )
    db.add(db_update)
    db.commit()

    return {"message": "Photo uploaded successfully", "update_id": db_update.id, "image_url": url}

@app.put("/gardens/{garden_id}/access")
def update_garden_access(garden_id: int, db: Session = Depends(get_db)):
    """Update the last_accessed_at timestamp for a garden."""
    garden = db.query(models.Garden).filter(models.Garden.id == garden_id).first()
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not. found")
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

# Mount Web UI static assets at / for Cloud Run serving
frontend_dir = "/var/www/html"
if os.path.exists(frontend_dir):
    class SPAStaticFiles(StaticFiles):
        async def get_response(self, path: str, scope):
            try:
                response = await super().get_response(path, scope)
                if response.status_code == 404:
                    return await super().get_response("index.html", scope)
                return response
            except Exception as ex:
                if getattr(ex, "status_code", None) == 404:
                    return await super().get_response("index.html", scope)
                raise ex

    app.mount("/", SPAStaticFiles(directory=frontend_dir, html=True), name="frontend")
