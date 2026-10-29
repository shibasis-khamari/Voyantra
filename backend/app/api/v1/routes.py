import time
from collections import defaultdict
from fastapi import APIRouter, HTTPException, status, Request
from ...schemas.route import (
    RouteRequest, RouteResponse, RouteMatrixRequest, RouteMatrixResponse,
    DayOptimizationRequest, DayOptimizationResponse
)
from ...services.routing_service import routing_service
from ...services.tsp_service import tsp_service
from ...core.geo import is_within_operating_bounds

router = APIRouter(prefix="/routes", tags=["Routes & Navigation"])

# In-memory sliding-window rate limiter for /routes/* (30 requests per minute per IP)
_route_rate_limit_history = defaultdict(list)
ROUTE_RATE_LIMIT_MAX = 30
ROUTE_RATE_LIMIT_WINDOW = 60.0
MAX_MATRIX_WAYPOINTS = 10

def apply_route_rate_limit(client_ip: str):
    now = time.time()
    recent = [t for t in _route_rate_limit_history[client_ip] if now - t < ROUTE_RATE_LIMIT_WINDOW]
    _route_rate_limit_history[client_ip] = recent
    if len(recent) >= ROUTE_RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {ROUTE_RATE_LIMIT_MAX} routing requests per minute allowed."
        )
    _route_rate_limit_history[client_ip].append(now)


@router.post("/reset-rate-limit", include_in_schema=False)
def reset_route_rate_limit():
    """Reset rate limiter state for automated testing isolation."""
    _route_rate_limit_history.clear()
    return {"status": "cleared"}


@router.post("/plan", response_model=RouteResponse)
@router.post("/directions", response_model=RouteResponse, include_in_schema=False)
def calculate_route(request: RouteRequest, req: Request):
    """
    Compute turn-by-turn route between origin and destination coordinates.
    Employs 3-tier cascade: Local OSRM -> Public Demo (with walking speed correction) -> Haversine Detour.
    Returns polyline GeoJSON, turn-by-turn maneuvers, travel duration, distance, and `tier_used` stamp.
    """
    client_ip = req.client.host if req.client else "127.0.0.1"
    apply_route_rate_limit(client_ip)

    # 1. Coordinate Bounds Validation (Global geographic range)
    if not is_within_operating_bounds(request.origin_lat, request.origin_lng):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Origin coordinate ({request.origin_lat}, {request.origin_lng}) is not a valid coordinate."
        )
    if not is_within_operating_bounds(request.dest_lat, request.dest_lng):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Destination coordinate ({request.dest_lat}, {request.dest_lng}) is not a valid coordinate."
        )

    try:
        return routing_service.get_route(
            origin_lat=request.origin_lat,
            origin_lng=request.origin_lng,
            dest_lat=request.dest_lat,
            dest_lng=request.dest_lng,
            mode=request.mode,
            city_id=request.city_id or "pondicherry",
            traffic_multiplier=request.traffic_multiplier or 1.0,
            travel_date=request.travel_date
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route calculation error: {str(e)}"
        )


@router.post("/matrix", response_model=RouteMatrixResponse)
def calculate_matrix(request: RouteMatrixRequest, req: Request):
    """
    Compute NxN distance and duration matrix for a set of coordinates.
    Maximum of 10 waypoints allowed.
    """
    client_ip = req.client.host if req.client else "127.0.0.1"
    apply_route_rate_limit(client_ip)

    # 1. Waypoint Count Validation
    if len(request.coordinates) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 coordinate waypoints required to construct a matrix."
        )
    if len(request.coordinates) > MAX_MATRIX_WAYPOINTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Matrix calculation exceeds maximum waypoint limit of {MAX_MATRIX_WAYPOINTS} (received {len(request.coordinates)})."
        )

    # 2. Coordinate Bounds Validation
    for idx, c in enumerate(request.coordinates):
        if not is_within_operating_bounds(c.lat, c.lng):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Waypoint {idx + 1} ({c.lat}, {c.lng}) is not a valid coordinate."
            )

    try:
        return routing_service.get_matrix(
            coordinates=request.coordinates,
            mode=request.mode,
            city_id=request.city_id or "pondicherry"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matrix calculation error: {str(e)}"
        )


@router.post("/optimize-day", response_model=DayOptimizationResponse)
def optimize_day_schedule(request: DayOptimizationRequest, req: Request):
    """
    Solves Time-Constrained TSP with Anchored Slots.
    Fixes time-anchored slots (sunset, meals, pooja, user-locked) in their windows,
    optimizes flexible floating stops to minimize travel time, and produces transit legs.
    """
    client_ip = req.client.host if req.client else "127.0.0.1"
    apply_route_rate_limit(client_ip)

    # Validate coordinate bounds for all slots
    for s in request.slots:
        if not is_within_operating_bounds(s.coordinates.lat, s.coordinates.lng):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Slot '{s.place_name}' coordinates ({s.coordinates.lat}, {s.coordinates.lng}) are not valid coordinates."
            )

    try:
        return tsp_service.optimize_day(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Day schedule optimization error: {str(e)}"
        )
