from pydantic import BaseModel
from typing import *
class ImageRequest(BaseModel):
    image: str 

class MessageRequest(BaseModel):
    message: str

class Spot(BaseModel):
    name: str
    location_user: Optional[List[float]] = None  
    description: str
    coordinates: List[float]
    distance_km: Optional[float] = None  

class TelegramSearchResponse(BaseModel):
    success: bool
    spots: List[Spot]
    message: Optional[str] = None
    user_location: Optional[str] = None

class BestPlacesRequest(BaseModel):
    target_fish: List[str]    
    water_space: List[str]

class CompareLocationRequest(BaseModel):
    """Запрос для сравнения места с существующими в базе"""
    message: str
    relax_type: str  # "рыбалка", "кемпинг" 

class TelegramSearchRequest(BaseModel):
    user_id: int
    query: str
    
