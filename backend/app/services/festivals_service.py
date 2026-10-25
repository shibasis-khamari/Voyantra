import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..core.database import db

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

class FestivalsService:
    def __init__(self):
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        self._load_initial_festivals()

    def _normalize_festival(self, item: Dict[str, Any], city_id: str = "pondicherry") -> Dict[str, Any]:
        res = dict(item)
        if "id" not in res or not res["id"]:
            res["id"] = f"fest-{uuid.uuid4().hex[:6]}"
        res["city_id"] = res.get("city_id", city_id).lower()
        if "_id" in res:
            res["_id"] = str(res["_id"])
        
        affected = res.get("affected_areas", [])
        if "affected_streets" not in res or not res["affected_streets"]:
            res["affected_streets"] = affected[:]
        if "procession_routes" not in res or not res["procession_routes"]:
            res["procession_routes"] = [f"{area} Main Route" for area in affected]
        if "closure_alerts" not in res or not res["closure_alerts"]:
            res["closure_alerts"] = [res.get("advisory_level", "Moderate Traffic Advisory")]
        return res

    def _load_initial_festivals(self):
        # Check MongoDB first
        col = db.get_collection("festivals")
        if col is not None and col.count_documents({}) > 0:
            for doc in col.find():
                cid = doc.get("city_id", "pondicherry").lower()
                norm = self._normalize_festival(doc, cid)
                if cid not in self._cache:
                    self._cache[cid] = []
                # Avoid duplicate IDs in cache
                if not any(f["id"] == norm["id"] for f in self._cache[cid]):
                    self._cache[cid].append(norm)

        # Ensure all JSON file datasets are also present
        for file in DATA_DIR.glob("*_festivals.json"):
            cid = file.stem.replace("_festivals", "").lower()
            try:
                with open(file, "r", encoding="utf-8") as f:
                    raw_items = json.load(f)
                    if cid not in self._cache:
                        self._cache[cid] = []
                    for raw in raw_items:
                        norm = self._normalize_festival(raw, cid)
                        if not any(f["id"] == norm["id"] for f in self._cache[cid]):
                            self._cache[cid].append(norm)
            except Exception as e:
                print(f"[FestivalsService] Error loading {file.name}: {e}")

    def get_city_festivals(self, city_id: str = "pondicherry") -> List[Dict[str, Any]]:
        cid = city_id.lower()
        if cid not in self._cache:
            self._load_initial_festivals()
        return self._cache.get(cid, [])

    def get_active_festivals_for_date(self, city_id: str, target_date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        festivals = self.get_city_festivals(city_id)
        if not target_date_str:
            target_date_str = datetime.now().strftime("%Y-%m-%d")

        try:
            dt = datetime.strptime(target_date_str, "%Y-%m-%d")
            md = dt.strftime("%m-%d")
        except ValueError:
            dt = datetime.now()
            md = dt.strftime("%m-%d")

        active = []
        for fest in festivals:
            start = fest.get("month_day_start", "01-01")
            end = fest.get("month_day_end", "12-31")

            # Handle cross-year (e.g. 12-24 to 01-02)
            if start <= end:
                if start <= md <= end:
                    active.append(fest)
            else:
                if md >= start or md <= end:
                    active.append(fest)

        return active

    def check_festival_collision_for_place(self, city_id: str, place_name: str, target_date_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
        active_fests = self.get_active_festivals_for_date(city_id, target_date_str)
        p_name_lower = place_name.lower()

        for fest in active_fests:
            areas = fest.get("affected_areas", [])
            for area in areas:
                if area.lower() in p_name_lower or p_name_lower in area.lower():
                    return fest
        return None

    def create_festival(self, fest_data: Dict[str, Any]) -> Dict[str, Any]:
        cid = fest_data.get("city_id", "pondicherry").lower()
        norm = self._normalize_festival(fest_data, cid)
        
        # Insert into MongoDB
        col = db.get_collection("festivals")
        if col is not None:
            col.insert_one(dict(norm))
        
        if cid not in self._cache:
            self._cache[cid] = []
        self._cache[cid].append(norm)
        return norm

    def update_festival(self, festival_id: str, update_fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        col = db.get_collection("festivals")
        if col is not None:
            col.update_one({"id": festival_id}, {"$set": update_fields})

        for cid, f_list in self._cache.items():
            for i, f in enumerate(f_list):
                if f["id"] == festival_id:
                    f.update({k: v for k, v in update_fields.items() if v is not None})
                    self._cache[cid][i] = self._normalize_festival(f, cid)
                    return self._cache[cid][i]
        return None

festivals_service = FestivalsService()
