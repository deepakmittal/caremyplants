from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    user_email: EmailStr
    user_phone: Optional[str] = None

class UserLogin(BaseModel):
    provider: str
    access_token: str

class UserEmailLogin(BaseModel):
    email: EmailStr

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class GardenCreate(BaseModel):
    name: str

class GardenResponse(BaseModel):
    id: int
    name: str
    status: Optional[str] = None
    garden_update_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PlantUpdateResponse(BaseModel):
    id: int
    condition_text: Optional[str] = None
    recommendation: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PlantResponse(BaseModel):
    id: int
    name: str
    plant_variety: Optional[str] = None
    condition: Optional[str] = None
    image_url: Optional[str] = None
    updates: List[PlantUpdateResponse] = []

    class Config:
        from_attributes = True

class GardenPhotoResponse(BaseModel):
    id: int
    photo_url: str
    created_at: datetime

    class Config:
        from_attributes = True

class PlantLatestUpdateResponse(BaseModel):
    id: int
    name: str
    plant_variety: Optional[str] = None
    image_url: Optional[str] = None
    latest_condition: Optional[str] = None
    latest_recommendation: Optional[str] = None
    last_update_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class GardenWithPhotosResponse(BaseModel):
    id: int
    name: str
    status: Optional[str] = None
    summary: Optional[str] = None
    upload_commentry: Optional[str] = None
    recommendation: Optional[str] = None
    created_at: datetime
    photos: List[GardenPhotoResponse]
    plants: List[PlantLatestUpdateResponse] = []

    class Config:
        from_attributes = True

class GardenDetailsResponse(BaseModel):
    id: int
    name: str
    status: Optional[str] = None
    summary: Optional[str] = None
    short_recommendation: Optional[str] = None
    full_recommendation: Optional[str] = None
    created_at: datetime
    plants: List[PlantLatestUpdateResponse]
    needs_water: Optional[bool] = None
    pest_detected: Optional[bool] = None
    low_sunlight: Optional[bool] = None


    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
