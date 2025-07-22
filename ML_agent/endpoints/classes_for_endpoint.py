from pydantic import BaseModel
from typing import *
class ImageRequest(BaseModel):
    image: str 

class MessageRequest(BaseModel):
    message: str

class TelegramSearchRequest(BaseModel):
    user_id: int
    query: str

class FishingSpot(BaseModel):
    name: str
    location_user: List[float]
    description: str
    short_description: dict
    coordinates: List[float]
    distance_km: Optional[float] = None

class TelegramSearchResponse(BaseModel):
    success: bool
    spots: List[FishingSpot]
    message: Optional[str] = None
    user_location: Optional[str] = None

class BestPlacesRequest(BaseModel):
    target_fish: List[str]    
    water_space: List[str]