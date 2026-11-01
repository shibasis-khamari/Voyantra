"""
Voyantra Entity Normalizer
Standardizes names, transliterations, coordinates, and categories across disparate data sources.
"""
import re
import unicodedata
from typing import Dict, Any, Optional
from ....schemas.knowledge import KnowledgeEntity

# Common prefixes and suffixes to strip during name canonicalization
HONORIFIC_PREFIXES = [
    r"^(sri|shri|sree|arulmigu|saint|st\.|the)\s+",
]

CATEGORY_ALIASES = {
    "temple": "spiritual",
    "church": "spiritual",
    "basilica": "spiritual",
    "mosque": "spiritual",
    "ashram": "spiritual",
    "shrine": "spiritual",
    "beach": "beach",
    "seashore": "beach",
    "promenade": "beach",
    "park": "nature",
    "garden": "nature",
    "botanical": "nature",
    "sanctuary": "nature",
    "lake": "nature",
    "museum": "heritage",
    "monument": "heritage",
    "fort": "heritage",
    "memorial": "heritage",
    "palace": "heritage",
    "historic": "heritage",
    "ruins": "heritage",
    "cafe": "cafe",
    "restaurant": "dining",
    "dining": "dining",
    "food": "dining",
}


class EntityNormalizer:
    @staticmethod
    def strip_accents(text: str) -> str:
        """Removes diacritics and unicode marks (e.g., Kāpālīśvarar -> Kapaleeshwarar)."""
        nfkd = unicodedata.normalize("NFKD", text)
        return "".join([c for c in nfkd if not unicodedata.combining(c)])

    @classmethod
    def canonical_name(cls, name: str) -> str:
        """Produces a simplified lowercase string for robust fuzzy & duplicate matching."""
        if not name:
            return ""
        s = cls.strip_accents(name.lower().strip())
        # Replace hyphens and underscores with spaces
        s = re.sub(r"[-_]+", " ", s)
        # Strip honorific prefixes
        for p in HONORIFIC_PREFIXES:
            s = re.sub(p, "", s)
        # Strip punctuation
        s = re.sub(r"[^\w\s]", "", s)
        # Collapse multiple whitespace
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @staticmethod
    def normalize_coordinates(coords: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if not coords or "lat" not in coords or "lng" not in coords:
            return None
        try:
            lat = round(float(coords["lat"]), 5)
            lng = round(float(coords["lng"]), 5)
            # Basic sanity range check for coordinates in southern India
            if 8.0 <= lat <= 35.0 and 68.0 <= lng <= 97.0:
                return {"lat": lat, "lng": lng}
            return {"lat": lat, "lng": lng}
        except (ValueError, TypeError):
            return None

    @staticmethod
    def normalize_category(category: Optional[str]) -> str:
        if not category:
            return "heritage"
        clean = category.lower().strip()
        for alias, mapped in CATEGORY_ALIASES.items():
            if alias in clean:
                return mapped
        return clean

    def normalize(self, entity: KnowledgeEntity) -> KnowledgeEntity:
        """Normalizes an entity in-place and returns it."""
        entity.name = entity.name.strip()
        if entity.coordinates:
            entity.coordinates = self.normalize_coordinates(entity.coordinates)
        if entity.category:
            entity.category = self.normalize_category(entity.category)
        if entity.city_id:
            entity.city_id = entity.city_id.lower().strip()
        return entity
