from fastapi import APIRouter, Query
from typing import List, Optional
from ...schemas.hotel import Hotel, HotelFilter
from ...schemas.place import BudgetTierEnum, DietaryOptionEnum
from ...services.hotels_service import hotels_service

router = APIRouter(prefix="/hotels", tags=["Hotels"])

@router.get("", response_model=List[Hotel])
def list_hotels(
    city_id: str = Query("pondicherry", description="Target city identifier"),
    budget: Optional[List[BudgetTierEnum]] = Query(None, description="Filter by budget tiers"),
    max_price: Optional[int] = Query(None, description="Maximum price per night in INR"),
    dietary: Optional[DietaryOptionEnum] = Query(None, description="Dietary option available at hotel"),
    near_lat: Optional[float] = Query(None, description="Latitude for proximity filter"),
    near_lng: Optional[float] = Query(None, description="Longitude for proximity filter"),
    max_distance_km: Optional[float] = Query(None, description="Maximum distance in km from given coordinates")
):
    filters = HotelFilter(
        city_id=city_id,
        budget_tiers=budget,
        max_price_inr=max_price,
        dietary_preference=dietary,
        near_lat=near_lat,
        near_lng=near_lng,
        max_distance_km=max_distance_km
    )
    return hotels_service.filter_hotels(filters)
