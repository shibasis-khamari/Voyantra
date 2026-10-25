import json
import time
import logging
import urllib.request
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Coordinates for target destinations
CITY_COORDINATES = {
    "pondicherry": (11.9416, 79.8083),
    "chennai": (13.0827, 80.2707)
}

# In-memory weather cache (15-minute TTL)
_weather_cache: Dict[str, Dict[str, Any]] = {}
WEATHER_CACHE_TTL = 900.0  # 15 minutes


class WeatherService:
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

        lat, lon = CITY_COORDINATES.get(city_key, CITY_COORDINATES["pondicherry"])
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
