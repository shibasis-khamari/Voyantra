from fastapi import APIRouter, Query, HTTPException, Depends, status
from typing import Optional, List, Dict, Any
from ...services.festivals_service import festivals_service
from ...schemas.festival import FestivalCreate, FestivalUpdate
from ...core.dependencies import require_admin

router = APIRouter(prefix="/festivals", tags=["Local Festival Advisory Calendar"])

@router.get("", response_model=List[Dict[str, Any]])
def get_city_festivals(
    city_id: Optional[str] = Query(None, description="City identifier (pondicherry, chennai)"),
    city: Optional[str] = Query(None, description="City alias (Pondicherry, Chennai)")
):
    """
    Returns full local festival calendar for a city.
    """
    resolved_city = (city_id or city or "pondicherry").strip().lower()
    return festivals_service.get_city_festivals(resolved_city)

@router.get("/active", response_model=List[Dict[str, Any]])
def get_active_festivals(
    city_id: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    date: Optional[str] = Query(None, description="Date format YYYY-MM-DD"),
    target_date: Optional[str] = Query(None, description="Date format YYYY-MM-DD")
):
    """
    Returns active festivals for a given travel date.
    """
    resolved_city = (city_id or city or "pondicherry").strip().lower()
    resolved_date = date or target_date
    return festivals_service.get_active_festivals_for_date(resolved_city, resolved_date)

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_festival(
    req: FestivalCreate,
    admin_user: dict = Depends(require_admin)
):
    """
    Create a new festival entry. Restricted to Admin.
    """
    created = festivals_service.create_festival(req.model_dump())
    return created

@router.put("/{festival_id}", response_model=Dict[str, Any])
def update_festival(
    festival_id: str,
    req: FestivalUpdate,
    admin_user: dict = Depends(require_admin)
):
    """
    Update an existing festival entry. Restricted to Admin.
    """
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    updated = festivals_service.update_festival(festival_id, update_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Festival with ID '{festival_id}' not found."
        )
    return updated
