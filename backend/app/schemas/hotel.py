from pydantic import BaseModel
from typing import List, Optional
from .place import BudgetTierEnum, Coordinates, DietaryOptionEnum

class Hotel(BaseModel):
    id: str
    city_id: str
    name: str
    description: str
    budget_tier: BudgetTierEnum
    price_per_night_inr: int
    coordinates: Coordinates
    address: str
    image_url: str
    amenities: List[str] = []
    dietary_options: List[DietaryOptionEnum] = [DietaryOptionEnum.ALL]
    rating: float = 4.2
    review_count: int = 85
    booking_url: Optional[str] = None
    proximity_tag: Optional[str] = "White Town / Promenade"

class HotelFilter(BaseModel):
    city_id: Optional[str] = "pondicherry"
    budget_tiers: Optional[List[BudgetTierEnum]] = None
    max_price_inr: Optional[int] = None
    dietary_preference: Optional[DietaryOptionEnum] = None
    near_lat: Optional[float] = None
    near_lng: Optional[float] = None
    max_distance_km: Optional[float] = None
