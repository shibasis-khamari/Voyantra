import json
import math
from typing import List, Optional
from pathlib import Path

from ..schemas.hotel import Hotel, HotelFilter
from ..schemas.place import DietaryOptionEnum
from ..core.geo import haversine_km

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class HotelsService:
    def __init__(self):
        self._hotels_cache: dict[str, List[Hotel]] = {}
        self._load_all_data()

    def _load_all_data(self):
        for file in DATA_DIR.glob("*_hotels.json"):
            city_prefix = file.stem.replace("_hotels", "")
            try:
                with open(file, "r", encoding="utf-8") as f:
                    raw_items = json.load(f)
                    self._hotels_cache[city_prefix] = [Hotel(**item) for item in raw_items]
            except Exception as e:
                print(f"[HotelsService] Warning: Failed to load {file.name}: {e}")

    def get_all_hotels(self, city_id: str = "pondicherry") -> List[Hotel]:
        return self._hotels_cache.get(city_id, [])

    def filter_hotels(self, filters: HotelFilter) -> List[Hotel]:
        city_id = filters.city_id or "pondicherry"
        hotels = self.get_all_hotels(city_id)
        filtered: List[Hotel] = []

        for h in hotels:
            # 1. Budget Tier
            if filters.budget_tiers and len(filters.budget_tiers) > 0:
                if h.budget_tier not in filters.budget_tiers:
                    continue

            # 2. Max Price
            if filters.max_price_inr is not None:
                if h.price_per_night_inr > filters.max_price_inr:
                    continue

            # 3. Dietary
            if filters.dietary_preference and filters.dietary_preference != DietaryOptionEnum.ALL:
                if (DietaryOptionEnum.ALL not in h.dietary_options and 
                    filters.dietary_preference not in h.dietary_options):
                    continue

            # 4. Distance proximity
            if (filters.near_lat is not None and 
                filters.near_lng is not None and 
                filters.max_distance_km is not None):
                dist = haversine_km(filters.near_lat, filters.near_lng, h.coordinates.lat, h.coordinates.lng)
                if dist > filters.max_distance_km:
                    continue

            filtered.append(h)

        return filtered

hotels_service = HotelsService()
