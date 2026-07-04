from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal
from datetime import datetime

# --- NEW HEALTH OVERVIEW SCHEMAS ---

class SanctuaryVitality(BaseModel):
    """High-level summary of the garden's overall health."""
    score: int = Field(..., ge=1, le=5, description="An overall garden rating from 1 to 5, where 5 represents a perfect garden and 1 indicates significant improvements are needed.")
    flourishingPlantsCount: int
    careNeededPlantsCount: int

class CareMetric(BaseModel):
    """Detailed information for a specific care category."""
    category: Literal["WATERING", "SUN_EXPOSURE", "SOIL_QUALITY", "VITALITY", "LEAF_CARE", "POT_STATUS", "PRUNING"]
    status: str = Field(..., description="An AI-generated assessment category for the given metric. The possible values depend on the 'category' field. For example, for 'SUN_EXPOSURE', values could be 'Too Sunny', 'Sunny', or 'Dark'. For 'WATERING', values could be 'Overwatered', 'Properly Watered', or 'Underwatered'.")
    isUnfavorable: bool
    affectedPlantsCount: int
    affectedPlantIds: List[int]

class GardenHealthOverview(BaseModel):
    """A comprehensive overview of the garden's health."""
    sanctuaryVitality: SanctuaryVitality
    metrics: List[CareMetric]

# --- NEW VISUALIZATION SCHEMAS ---

class ProductRecommendation(BaseModel):
    title: str
    reason: str
    product_url: str
    image_url: str

    class Config:
        from_attributes = True

class GardenVisualization(BaseModel):
    image_url: str
    recommendations: List[ProductRecommendation] = []
    created_at: datetime

    class Config:
        from_attributes = True

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    message: str

# --- EXISTING SCHEMAS ---

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

# MODIFIED GardenResponse
class GardenResponse(BaseModel):
    id: int
    name: str
    status: Optional[str] = Field(None, description="The initial status of the garden update (e.g., 'Queued'). For real-time processing status, query the GET /updates/{update_id}/status endpoint.")
    garden_update_id: Optional[int] = None
    workflow_id: Optional[str] = Field(None, description="The unique identifier for the Temporal workflow processing this garden update.")
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
    status: Optional[str] = Field(None, description="The final status of the garden after processing is complete (e.g., 'Ready'). For updates that are currently being processed, query the GET /updates/{update_id}/status endpoint to get the real-time status.")
    summary: Optional[str] = None
    upload_commentry: Optional[str] = None
    recommendation: Optional[str] = None
    created_at: datetime
    photos: List[GardenPhotoResponse]
    plants: List[PlantLatestUpdateResponse] = []
    healthOverview: Optional[GardenHealthOverview] = None

    class Config:
        from_attributes = True

class GardenDetailsResponse(BaseModel):
    id: int
    name: str
    status: Optional[str] = Field(None, description="The final status of the garden after processing is complete (e.g., 'Ready'). For updates that are currently being processed, query the GET /updates/{update_id}/status endpoint to get the real-time status.")
    recommendation: Optional[str] = None
    recommendation_full: Optional[str] = None
    needs_watering: Optional[bool] = None
    needs_fertilizer: Optional[bool] = None
    has_pests: Optional[bool] = None
    has_weeds: Optional[bool] = None
    has_disease: Optional[bool] = None
    needs_sunlight: Optional[bool] = None
    created_at: datetime
    plants: List[PlantLatestUpdateResponse]
    healthOverview: Optional[GardenHealthOverview] = None
    visualization: Optional[GardenVisualization] = None


    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# --- NEW TEMPORAL WORKFLOW SCHEMAS ---

class ActivityStatus(BaseModel):
    name: Literal[
        "GATHER_GARDEN_DETAILS",
        "CUT_PLANT_IMAGES",
        "GATHER_PLANT_DETAILS",
        "UPDATE_GARDEN_FLAGS"
    ]
    status: Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    update_id: int
    status: Literal["RUNNING", "COMPLETED", "FAILED", "CANCELED", "TIMED_OUT"]
    created_at: datetime
    updated_at: datetime
    activities: List[ActivityStatus]
    error_message: Optional[str] = None
