from fastapi import APIRouter, Query, HTTPException, status, Request, Header
from typing import Optional, Dict, Any
from ...services.crowd_service import crowd_service
from ...schemas.crowd import (
    CrowdReportRequest,
    CrowdReportResponse,
    LiveCrowdResponse
)

router = APIRouter(prefix="/crowd", tags=["Crowd Estimation & Crowdsourced Reporting"])

@router.get("/place/{place_id}")
def get_place_crowd_estimate(
    place_id: str,
    city_id: Optional[str] = Query(None, description="City identifier (pondicherry, chennai)"),
    city: Optional[str] = Query(None, description="City alias"),
    target_date: Optional[str] = Query(None, description="Date format YYYY-MM-DD"),
    date: Optional[str] = Query(None, description="Alternative date alias"),
    hour: Optional[int] = Query(None, ge=0, le=23, description="Hour of day (0-23)")
) -> Dict[str, Any]:
    """
    Returns rule-based dynamic crowd level, hourly trend curves, driver reasons,
    and festival warnings for a specific place.
    """
    resolved_city = (city_id or city or "pondicherry").strip().lower()
    resolved_date = target_date or date
    
    result = crowd_service.estimate_place_crowd(
        city_id=resolved_city,
        place_id=place_id,
        target_date_str=resolved_date,
        hour=hour
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Place with id '{place_id}' not found in '{resolved_city}'."
        )
    return result


@router.get("/place/{place_id}/live", response_model=LiveCrowdResponse)
def get_live_crowd_status(
    place_id: str,
    city_id: str = Query("pondicherry", description="City identifier (pondicherry, chennai)")
):
    """
    Phase 5: Returns live blended crowd density, confidence badge,
    active reporter counts, and real-time surge anomaly alerts.
    """
    try:
        return crowd_service.get_live_crowd_estimate(place_id=place_id, city_id=city_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Live crowd error: {str(e)}")


@router.post("/report", response_model=CrowdReportResponse)
def submit_crowd_report(
    report: CrowdReportRequest,
    req: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Phase 5: 1-Tap Geofenced Crowdsourced Footfall Submission.
    - Verified against place coordinates (<= 200m). If > 200m, returns 403 Forbidden.
    - Rate-limited to 1 report per place per 15 minutes (returns 429 Too Many Requests).
    - Logs anonymized feature snapshots without rule leakage.
    - Blends reported level using 30-minute exponential decay.
    """
    client_ip = req.client.host if req.client else "127.0.0.1"

    # Extract user_id from token if logged in
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        try:
            from ...core.security import verify_token
            token = authorization.split(" ")[1]
            payload = verify_token(token)
            if payload:
                user_id = payload.get("sub") or payload.get("email")
        except Exception:
            pass

    try:
        return crowd_service.submit_crowd_report(
            request=report,
            client_ip=client_ip,
            user_id=user_id
        )
    except PermissionError as pe:
        # Geofence violation (> 200m away)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except TimeoutError as te:
        # Cooldown violation (< 15 min since last report)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(te))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Submission error: {str(e)}")


@router.get("/city/{city_id}")
def get_city_crowd_index(
    city_id: str = "pondicherry",
    target_date: Optional[str] = Query(None, description="Date format YYYY-MM-DD"),
    date: Optional[str] = Query(None, description="Alternative date alias")
) -> Dict[str, Any]:
    """
    Returns overall city congestion index and active festival alerts.
    """
    resolved_city = city_id.strip().lower()
    if resolved_city not in ["pondicherry", "chennai"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City '{city_id}' not found. Supported cities are Pondicherry and Chennai."
        )
    resolved_date = target_date or date
    return crowd_service.get_city_crowd_index(city_id=resolved_city, target_date_str=resolved_date)
