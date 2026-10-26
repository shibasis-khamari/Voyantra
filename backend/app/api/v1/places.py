from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional
from ...schemas.place import Place, PlaceFilter, CategoryEnum, BudgetTierEnum, AgeGroupEnum, DietaryOptionEnum
from ...services.places_service import places_service
from ...services.internet_ingestion_service import internet_ingestion_service
from ...core.dependencies import require_admin

router = APIRouter(prefix="/places", tags=["Places"])

@router.get("", response_model=List[Place])
def list_places(
    city_id: Optional[str] = Query(None, description="Target city identifier"),
    city: Optional[str] = Query(None, description="Alternative city identifier alias"),
    category: Optional[List[CategoryEnum]] = Query(None, description="Filter by categories"),
    budget: Optional[List[BudgetTierEnum]] = Query(None, description="Filter by budget tiers"),
    age_group: Optional[AgeGroupEnum] = Query(None, description="Filter for specific age group"),
    dietary: Optional[DietaryOptionEnum] = Query(None, description="Dietary option filter"),
    max_cost: Optional[int] = Query(None, description="Maximum estimated cost in INR"),
    search: Optional[str] = Query(None, description="Keyword search in name, description, tags")
):
    resolved_city = (city_id or city or "pondicherry").strip().lower()
    filters = PlaceFilter(
        city_id=resolved_city,
        categories=category,
        budget_tiers=budget,
        age_group=age_group,
        dietary_preference=dietary,
        max_cost_inr=max_cost,
        search_query=search
    )
    return places_service.filter_places(filters)

@router.get("/cities/all")
def get_available_cities():
    """Returns all available cities in the system."""
    return places_service.get_cities()

@router.post("/fetch-from-internet")
def fetch_from_internet(
    city_name: str = Query(..., description="Name of the city to ingest from OpenStreetMap and Wikipedia"),
    admin_user: dict = Depends(require_admin)
):
    """
    Ingests live tourist destinations from Wikidata/Wikipedia. Restricted to Administrator role.
    """
    res = internet_ingestion_service.ingest_city_from_internet(city_name)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message", "Failed to ingest city places."))
    places_service.reload_data()
    return res

@router.post("/reload-data")
def reload_places_data():
    """Reload places data from disk JSON files for automated testing isolation."""
    places_service.reload_data()
    return {"status": "reloaded", "message": "Places data reloaded from disk"}

@router.get("/{place_id}", response_model=Place)
def get_place(
    place_id: str,
    city_id: Optional[str] = Query(None),
    city: Optional[str] = Query(None)
):
    resolved_city = (city_id or city or "pondicherry").strip().lower()
    place = places_service.get_place_by_id(place_id, resolved_city)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place
