from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    user_email: EmailStr
    user_phone: Optional[str] = None

class UserLogin(BaseModel):
    provider: str
    access_token: str

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
    garden_update_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PlantResponse(BaseModel):
    id: int
    name: str
    plant_variety: str
    condition: str
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class GardenDetailsResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    plants: List[PlantResponse]

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
