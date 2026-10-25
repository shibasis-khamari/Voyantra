import json
import os
from typing import List, Optional
from pathlib import Path

from ..schemas.place import Place, PlaceFilter, CategoryEnum, BudgetTierEnum, AgeGroupEnum, DietaryOptionEnum

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

class PlacesService:
    def __init__(self):
        self._places_cache: dict[str, List[Place]] = {}
        self._load_all_data()

    def _load_all_data(self):
        """Loads all city places from JSON files. Can easily be hooked into Supabase / Postgres."""
        for file in DATA_DIR.glob("*_places.json"):
            city_prefix = file.stem.replace("_places", "")
            try:
                with open(file, "r", encoding="utf-8") as f:
                    raw_items = json.load(f)
                    self._places_cache[city_prefix] = [Place(**item) for item in raw_items]
            except Exception as e:
                print(f"[PlacesService] Warning: Failed to load {file.name}: {e}")

    def reload_data(self):
        """Reloads all datasets from disk or live DB."""
        self._places_cache.clear()
        self._load_all_data()

    def get_cities(self) -> List[dict]:
        cities_file = DATA_DIR / "cities.json"
        try:
            with open(cities_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return [{"id": "pondicherry", "name": "Pondicherry", "country": "India"}]

    def get_all_places(self, city_id: str = "pondicherry") -> List[Place]:
        if city_id not in self._places_cache:
            self._load_all_data()
        return self._places_cache.get(city_id, [])

    def get_place_by_id(self, place_id: str, city_id: str = "pondicherry") -> Optional[Place]:
        places = self.get_all_places(city_id)
        for p in places:
            if p.id == place_id:
                return p
        return None

    def filter_places(self, filters: PlaceFilter) -> List[Place]:
        city_id = filters.city_id or "pondicherry"
        places = self.get_all_places(city_id)
        filtered: List[Place] = []

        for p in places:
            # 1. Category Filter
            if filters.categories and len(filters.categories) > 0:
                if p.category not in filters.categories:
                    continue

            # 2. Budget Tier Filter
            if filters.budget_tiers and len(filters.budget_tiers) > 0:
                if p.budget_tier not in filters.budget_tiers:
                    continue

            # 3. Max Cost
            if filters.max_cost_inr is not None:
                if p.estimated_cost_inr > filters.max_cost_inr:
                    continue

            # 4. Age Group Filter (if strict)
            if filters.age_group and filters.age_group != AgeGroupEnum.ALL:
                # If place specifically lists age groups and doesn't have 'all' or the user's age group
                if AgeGroupEnum.ALL not in p.recommended_age_groups and filters.age_group not in p.recommended_age_groups:
                    continue

            # 5. Dietary Preference Filter
            if filters.dietary_preference and filters.dietary_preference != DietaryOptionEnum.ALL:
                # If it's a food place (dining/cafe), ensure dietary compatibility
                if p.category in [CategoryEnum.CAFE, CategoryEnum.DINING]:
                    # Strict diets must be explicitly listed in place's dietary_options
                    if filters.dietary_preference in [DietaryOptionEnum.PURE_VEG_JAIN, DietaryOptionEnum.HALAL, DietaryOptionEnum.VEGAN]:
                        if filters.dietary_preference not in p.dietary_options:
                            continue
                    elif filters.dietary_preference == DietaryOptionEnum.VEGETARIAN:
                        # Any pure_veg, jain, or vegan place is inherently vegetarian-compliant
                        if not any(opt in p.dietary_options for opt in [DietaryOptionEnum.VEGETARIAN, DietaryOptionEnum.PURE_VEG_JAIN, DietaryOptionEnum.VEGAN]):
                            continue
                    else:
                        if filters.dietary_preference not in p.dietary_options:
                            continue

            # 6. Accessibility
            if filters.min_accessibility is not None:
                if p.accessibility_rating < filters.min_accessibility:
                    continue

            # 7. Search Query
            if filters.search_query:
                q = filters.search_query.lower()
                text_to_search = f"{p.name} {p.description} {p.category} {p.sub_category or ''} {' '.join(p.tags)}".lower()
                if q not in text_to_search:
                    continue

            filtered.append(p)

        return filtered

places_service = PlacesService()
