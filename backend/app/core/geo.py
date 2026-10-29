import math
from typing import Literal

# ==============================================================================
# Detour Factors & Travel Speeds
# ==============================================================================
# ASSUMPTION: 1.35 (Pondicherry) and 1.45 (Chennai) are empirical detour factors
# to be calibrated against local OSRM road network distances.
DETOUR_FACTOR_PONDICHERRY: float = 1.35
DETOUR_FACTOR_CHENNAI: float = 1.45
DETOUR_FACTOR_DEFAULT: float = 1.40

# Default urban transit speeds in km/h
DEFAULT_DRIVING_SPEED_KMH: float = 25.0  # Urban corridor average for Pondy & Chennai
DEFAULT_WALKING_SPEED_KMH: float = 4.5   # 1.25 m/s standard pedestrian velocity

# Center Coordinates & Operating Radius (Single shared constant matching GPS detection)
PONDICHERRY_CENTER = (11.9416, 79.8083)
CHENNAI_CENTER = (13.0827, 80.2707)
OPERATING_RADIUS_KM: float = 70.0


def is_valid_coordinate(lat: float, lng: float) -> bool:
    """Validate that latitude and longitude fall within legal WGS84 ranges."""
    return -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0


def is_within_operating_bounds(lat: float, lng: float) -> bool:
    """
    Assert that the coordinate is a valid geographic coordinate on Earth.
    Supports global coordinates (-90 <= lat <= 90, -180 <= lng <= 180).
    """
    return is_valid_coordinate(lat, lng)




def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees).
    """
    R = 6371.0 # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def get_detour_factor(city_id: str) -> float:
    """
    Return the assumed road network detour factor for the specified city.
    """
    city_lower = (city_id or "").strip().lower()
    if "chennai" in city_lower:
        return DETOUR_FACTOR_CHENNAI
    elif "pondicherry" in city_lower or "pondy" in city_lower or "puducherry" in city_lower:
        return DETOUR_FACTOR_PONDICHERRY
    return DETOUR_FACTOR_DEFAULT


def estimate_road_distance_km(lat1: float, lon1: float, lat2: float, lon2: float, city_id: str = "pondicherry") -> float:
    """
    Estimate actual road distance by applying the city's empirical detour multiplier
    to the Haversine as-the-crow-flies distance.
    """
    direct_dist = haversine_km(lat1, lon1, lat2, lon2)
    detour = get_detour_factor(city_id)
    return direct_dist * detour


def estimate_travel_time_minutes(
    distance_km: float,
    mode: Literal["driving", "walking"] = "driving",
    traffic_multiplier: float = 1.0
) -> float:
    """
    Compute estimated travel time in minutes based on distance and mode.
    Includes optional time-of-day traffic multiplier for congested periods.
    """
    if mode == "walking":
        speed = DEFAULT_WALKING_SPEED_KMH
        # Walking is generally unaffected by road vehicular traffic
        return round((distance_km / speed) * 60.0, 1)
    else:
        speed = DEFAULT_DRIVING_SPEED_KMH / max(traffic_multiplier, 0.1)
        return round((distance_km / speed) * 60.0, 1)
