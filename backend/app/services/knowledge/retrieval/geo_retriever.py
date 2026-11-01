"""
Voyantra Geospatial Radius Retriever
Filters and ranks knowledge entities based on great-circle distance from a target GPS coordinate.
"""
import math
from typing import List, Tuple, Optional
from ....schemas.knowledge import KnowledgeEntity
from ..storage.knowledge_repository import KnowledgeRepository, knowledge_repository


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * (math.sin(dlambda / 2.0) ** 2)
    return 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


class GeoRetriever:
    def __init__(self, repository: Optional[KnowledgeRepository] = None):
        self.repo = repository or knowledge_repository

    def search_radius(
        self,
        lat: float,
        lng: float,
        radius_km: float = 5.0,
        city_id: Optional[str] = None,
        category: Optional[str] = None,
        top_k: int = 20,
    ) -> List[Tuple[KnowledgeEntity, float]]:
        """Finds entities within radius_km sorted by distance ascending."""
        entities = self.repo.find_entities(city_id=city_id, category=category, limit=300)
        results: List[Tuple[KnowledgeEntity, float]] = []

        for ent in entities:
            if not ent.coordinates:
                continue
            e_lat = ent.coordinates.get("lat")
            e_lng = ent.coordinates.get("lng")
            if e_lat is None or e_lng is None:
                continue

            dist = haversine_km(lat, lng, e_lat, e_lng)
            if dist <= radius_km:
                results.append((ent, dist))

        results.sort(key=lambda x: x[1])
        return results[:top_k]
