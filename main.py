from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import os
import uuid

from database import engine, Base, get_db
import models, schemas
from services import auth, gcs, gemini, garden_logic
from utils import image as image_utils

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Garden Backend API")

@app.get("/")
def read_root():
    return {"message": "Welcome to Garden API"}

# 1. Login Endpoint
@app.post("/auth/login", response_model=schemas.Token)
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user, token = auth.authenticate_external_user(db, login_data)
    return {"access_token": token, "token_type": "bearer"}

# 2, 3, 4. Garden Creation & Photo Upload Endpoint
@app.post("/gardens", response_model=schemas.GardenResponse)
async def create_garden(
    name: str = Form(...),
    photos: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    # 3. Create new entry in garden table
    db_garden = models.Garden(name=name)
    db.add(db_garden)
    db.commit()
    db.refresh(db_garden)

    # Create ONE garden update for this session
    db_update = models.GardenUpdate(garden_id=db_garden.id, status="Initial Creation")
    db.add(db_update)
    db.commit()
    db.refresh(db_update)

    for photo in photos:
        content = await photo.read()
        await garden_logic.process_garden_photo(db, db_garden.id, db_update.id, content, photo.filename)

    # Build response with garden_update_id
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
    
    for photo in photos:
        content = await photo.read()
        await garden_logic.process_garden_photo(db, db_update.garden_id, update_id, content, photo.filename)
    
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
    return garden

# New: Get all gardens for a specific user
@app.get("/users/{user_id}/gardens", response_model=List[schemas.GardenResponse])
def get_user_gardens(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.gardens
