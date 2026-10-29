import json
import time
import logging
import urllib.request
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Coordinates for target destinations
CITY_COORDINATES = {
    "pondicherry": (11.9416, 79.8083),
    "chennai": (13.0827, 80.2707),
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.6139, 77.2090),
    "new-delhi": (28.6139, 77.2090),
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "jaipur": (26.9124, 75.7873),
    "goa": (15.2993, 74.1240),
    "kerala": (10.8505, 76.2711),
    "himachal-pradesh": (31.1048, 77.1734),
    "himachal": (31.1048, 77.1734),
    "manali": (32.2432, 77.1892),
    "shimla": (31.1048, 77.1734),
    "agra": (27.1767, 78.0081),
    "kolkata": (22.5726, 88.3639),
    "hyderabad": (17.3850, 78.4867),
    "tokyo": (35.6762, 139.6503),
    "paris": (48.8566, 2.3522),
    "bali": (-8.4095, 115.1889),
    "dubai": (25.2048, 55.2708),
    "london": (51.5074, -0.1278),
    "new-york": (40.7128, -74.0060),
    "singapore": (1.3521, 103.8198),
    "bangkok": (13.7563, 100.5018),
    "rome": (41.9028, 12.4964),
}

# In-memory weather cache (15-minute TTL)
_weather_cache: Dict[str, Dict[str, Any]] = {}
WEATHER_CACHE_TTL = 900.0  # 15 minutes


class WeatherService:
    def _resolve_coordinates(self, city_key: str) -> tuple[float, float]:
        norm = city_key.replace(" ", "-")
        if norm in CITY_COORDINATES:
            return CITY_COORDINATES[norm]

        # Dynamic Geocoding via Open-Meteo free geocoding API
        try:
            geo_query = city_key.replace("-", "+")
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={geo_query}&count=1"
            req = urllib.request.Request(
                geo_url,
                headers={"User-Agent": "Voyantra-Trip-Planner/1.0"}
            )
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    geo_data = json.loads(resp.read().decode("utf-8"))
                    results = geo_data.get("results")
                    if results and len(results) > 0:
                        lat = float(results[0]["latitude"])
                        lon = float(results[0]["longitude"])
                        CITY_COORDINATES[norm] = (lat, lon)
                        return lat, lon
        except Exception:
            pass

        return CITY_COORDINATES.get("pondicherry")

    def get_current_weather(self, city_id: str) -> Dict[str, Any]:
        """
        Fetches real-time weather from keyless Open-Meteo API.
        Returns temperature (°C), precipitation (mm), and WMO weather code.
        Caches results for 15 minutes.
        """
        city_key = city_id.lower().strip()
        now = time.time()

        if city_key in _weather_cache:
            cached = _weather_cache[city_key]
            if now - cached["timestamp"] < WEATHER_CACHE_TTL:
                return cached["data"]

        lat, lon = self._resolve_coordinates(city_key)
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,weather_code"

        default_data = {
            "temperature_c": 28.5,
            "precipitation_mm": 0.0,
            "weather_condition_code": 1,  # Mainly clear
            "is_live_weather": False
        }

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Voyantra-Trip-Planner/1.0 (Academic Research; contact: admin@voyantra.com)"}
            )
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    current = data.get("current", {})
                    weather_res = {
                        "temperature_c": float(current.get("temperature_2m", 28.5)),
                        "precipitation_mm": float(current.get("precipitation", 0.0)),
                        "weather_code": int(current.get("weather_code", 1)),
                        "is_live_weather": True
                    }
                    _weather_cache[city_key] = {
                        "timestamp": now,
                        "data": weather_res
                    }
                    return weather_res
        except Exception as e:
            logger.debug(f"[WeatherService] Open-Meteo notice ({e}). Using seasonal default weather.")

        _weather_cache[city_key] = {
            "timestamp": now,
            "data": default_data
        }
        return default_data


weather_service = WeatherService()
