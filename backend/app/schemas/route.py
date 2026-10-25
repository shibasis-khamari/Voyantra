from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from .place import Coordinates

class RoutingTier(str, Enum):
    local_osrm = "local_osrm"
    public_demo = "public_demo"
    haversine_detour = "haversine_detour"

class WalkingSource(str, Enum):
    fossgis_foot = "fossgis_foot"
    local_foot = "local_foot"
    corrected_car = "corrected_car"

RouteModeEnum = Literal["driving", "walking"]

class TurnStep(BaseModel):
    instruction: str
    distance_meters: float
    duration_seconds: float
    street_name: Optional[str] = ""

class RouteRequest(BaseModel):
    origin_lat: float = Field(..., ge=-90.0, le=90.0, description="Origin latitude (-90 to 90)")
    origin_lng: float = Field(..., ge=-180.0, le=180.0, description="Origin longitude (-180 to 180)")
    dest_lat: float = Field(..., ge=-90.0, le=90.0, description="Destination latitude (-90 to 90)")
    dest_lng: float = Field(..., ge=-180.0, le=180.0, description="Destination longitude (-180 to 180)")
    mode: RouteModeEnum = "driving"
    city_id: Optional[str] = "pondicherry"
    travel_date: Optional[str] = Field(None, description="Optional travel date in YYYY-MM-DD format for festival closure checks")
    traffic_multiplier: Optional[float] = Field(1.0, ge=0.1, le=5.0)

class RouteResponse(BaseModel):
    origin: Coordinates
    destination: Coordinates
    mode: str
    distance_km: float
    estimated_travel_time_minutes: float
    tier_used: RoutingTier
    walking_source: Optional[WalkingSource] = None
    is_approximate: bool
    approximate_label: str = "(Approximate travel time)"
    polyline_geojson: Dict[str, Any]
    turn_by_turn_steps: List[TurnStep] = []
    warning: Optional[str] = None
    closure_affected: bool = False
    closure_warning: Optional[str] = None
    closure_events: List[str] = []

class RouteMatrixRequest(BaseModel):
    coordinates: List[Coordinates] = Field(
        ...,
        min_length=2,
        max_length=10,
        description="Matrix waypoints (minimum 2, maximum 10)"
    )
    mode: RouteModeEnum = "driving"
    city_id: Optional[str] = "pondicherry"

class RouteMatrixResponse(BaseModel):
    durations_minutes: List[List[float]]
    distances_km: List[List[float]]
    cell_tiers: Optional[List[List[RoutingTier]]] = None
    tier_summary: Dict[str, int] = {}
    is_mixed_tier: bool = False
    is_approximate: bool = False
    approximate_label: str = "(Approximate travel time)"
    tier_used: Optional[RoutingTier] = None
    walking_source: Optional[WalkingSource] = None

# -----------------------------------------------------------------------------
# Phase 4 Task 4: Time-Constrained TSP Optimization Schemas
# -----------------------------------------------------------------------------
class OpeningHoursSpec(BaseModel):
    is_verified: bool = False
    weekday_open: Optional[str] = None
    weekday_close: Optional[str] = None
    evening_open: Optional[str] = None
    evening_close: Optional[str] = None

class DayOptimizationSlot(BaseModel):
    slot_id: str
    place_id: Optional[str] = None
    place_name: str
    coordinates: Coordinates
    time_anchor: Optional[Literal["morning", "afternoon", "evening", "sunset", "pooja", "lunch", "dinner"]] = None
    fixed_time_window: Optional[Dict[str, str]] = None  # e.g., {"start": "17:00", "end": "19:00"}
    is_locked: bool = False
    visit_duration_minutes: int = 60
    opening_hours: Optional[OpeningHoursSpec] = None

class TransitLeg(BaseModel):
    from_place: str
    to_place: str
    distance_km: float
    duration_minutes: float
    tier_used: RoutingTier
    walking_source: Optional[WalkingSource] = None
    is_approximate: bool
    departure_time: str
    arrival_time: str
    closure_affected: bool = False
    closure_warning: Optional[str] = None
    polyline_geojson: Optional[Dict[str, Any]] = None

class OptimizedDaySlot(BaseModel):
    order: int
    slot_id: str
    place_name: str
    place_id: Optional[str] = None
    coordinates: Coordinates
    start_time: str
    end_time: str
    visit_duration_minutes: int
    is_locked: bool
    time_anchor: Optional[str] = None
    hours_warning: Optional[str] = None

class DayOptimizationRequest(BaseModel):
    day_number: int = 1
    city_id: str = "pondicherry"
    mode: RouteModeEnum = "driving"
    travel_date: Optional[str] = None
    day_start_time: str = "09:00"
    slots: List[DayOptimizationSlot] = Field(..., min_length=1, max_length=10)

class DayOptimizationResponse(BaseModel):
    day_number: int
    city_id: str
    mode: RouteModeEnum
    optimized_slots: List[OptimizedDaySlot]
    transit_legs: List[TransitLeg]
    total_travel_time_minutes: float
    total_travel_distance_km: float
    total_visit_time_minutes: float
    tier_summary: Dict[str, int]
    is_approximate: bool
