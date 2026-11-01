"""
Voyantra Multi-Signal Entity Deduplicator
Implements multi-signal duplicate resolution using source identifiers, canonical names,
and category-dependent geographic proximity thresholds, routing ambiguous matches to review_required.
"""
import math
from typing import Dict, Any, List, Optional, Tuple
from ....schemas.knowledge import KnowledgeEntity, VerificationStatusEnum
from .normalizer import EntityNormalizer

# Category-dependent geographic proximity thresholds in meters
CATEGORY_DISTANCE_THRESHOLDS_METERS = {
    "spiritual": 35.0,     # Temples & shrines: small threshold to avoid merging adjacent shrines
    "cafe": 50.0,          # Cafes / dining: prevents merging adjacent cafes
    "dining": 50.0,
    "heritage": 100.0,     # Monuments & heritage structures
    "culture": 100.0,
    "nature": 250.0,       # Parks & nature areas
    "beach": 500.0,        # Coastal stretches & promenades
}
DEFAULT_DISTANCE_THRESHOLD_METERS = 100.0


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two GPS coordinates in meters."""
    r = 6371000.0  # Earth's radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def name_similarity(name1: str, name2: str) -> float:
    """Computes similarity using token Jaccard combined with token containment."""
    c1 = EntityNormalizer.canonical_name(name1)
    c2 = EntityNormalizer.canonical_name(name2)
    if not c1 or not c2:
        return 0.0
    if c1 == c2:
        return 1.0

    t1 = set(c1.split())
    t2 = set(c2.split())
    if not t1 or not t2:
        return 0.0

    intersection = len(t1 & t2)
    union = len(t1 | t2)
    jaccard = intersection / float(union)
    containment = max(intersection / float(len(t1)), intersection / float(len(t2)))
    return max(jaccard, containment * 0.90)


class EntityDeduplicator:
    def __init__(self, repository: Any):
        self.repo = repository

    def get_threshold_for_category(self, category: Optional[str]) -> float:
        cat_key = (category or "").lower()
        return CATEGORY_DISTANCE_THRESHOLDS_METERS.get(cat_key, DEFAULT_DISTANCE_THRESHOLD_METERS)

    def resolve_or_merge(self, new_entity: KnowledgeEntity) -> Tuple[KnowledgeEntity, str]:
        """
        Evaluates new_entity against existing entities in the repository for the same city.
        Returns (resolved_entity, action), where action is 'inserted' or 'merged'.
        """
        existing_entities = self.repo.find_entities(city_id=new_entity.city_id, limit=300)
        
        best_match: Optional[KnowledgeEntity] = None
        ambiguous = False

        for existing in existing_entities:
            # 1. Exact Source Identifier Match
            if new_entity.primary_source_url and existing.primary_source_url:
                if new_entity.primary_source_url == existing.primary_source_url:
                    best_match = existing
                    break

            # 2. Canonical Name Similarity
            sim = name_similarity(new_entity.name, existing.name)

            # 3. Geographic Proximity
            dist_meters = None
            if new_entity.coordinates and existing.coordinates:
                dist_meters = haversine_distance_meters(
                    new_entity.coordinates["lat"],
                    new_entity.coordinates["lng"],
                    existing.coordinates["lat"],
                    existing.coordinates["lng"],
                )

            threshold = self.get_threshold_for_category(new_entity.category or existing.category)

            # 4. Multi-Signal Decision Rules
            if sim >= 0.85 and (dist_meters is None or dist_meters <= threshold):
                best_match = existing
                break
            elif sim >= 0.70 and dist_meters is not None and (threshold < dist_meters <= threshold * 2.5):
                # Strong name match but distance is borderline
                ambiguous = True
            elif 0.50 <= sim < 0.85 and dist_meters is not None and dist_meters <= threshold:
                # Moderate name overlap and close proximity
                ambiguous = True

        if ambiguous and not best_match:
            # Route ambiguous matches to review_required
            new_entity.verification_status = VerificationStatusEnum.REVIEW_REQUIRED
            return new_entity, "inserted"

        if best_match:
            # Merge fields non-destructively
            merged = self._merge_entities(best_match, new_entity)
            return merged, "merged"

        return new_entity, "inserted"

    def _merge_entities(self, target: KnowledgeEntity, source: KnowledgeEntity) -> KnowledgeEntity:
        """Merges source entity into target, preserving verified facts and higher-confidence data."""
        # Verification status: verified takes precedence over unverified
        if source.verification_status == VerificationStatusEnum.VERIFIED:
            target.verification_status = VerificationStatusEnum.VERIFIED
        
        # Add alternate names
        alt_set = set(target.alternate_names)
        if source.name != target.name:
            alt_set.add(source.name)
        alt_set.update(source.alternate_names)
        target.alternate_names = list(alt_set)

        # Merge highlights
        hl_set = set(target.highlights)
        hl_set.update(source.highlights)
        target.highlights = list(hl_set)

        # Merge tags
        tag_set = set(target.tags)
        tag_set.update(source.tags)
        target.tags = list(tag_set)

        # Merge provenance
        for f_name, prov in source.provenance.items():
            if f_name not in target.provenance:
                target.provenance[f_name] = prov
            elif prov.confidence > target.provenance[f_name].confidence:
                target.provenance[f_name] = prov

        # Description: Keep longer or richer description
        if len(source.description) > len(target.description):
            target.description = source.description

        # Opening hours: Keep verified opening hours
        if source.opening_hours_verified and not target.opening_hours_verified:
            target.opening_hours = source.opening_hours
            target.opening_hours_verified = True
            target.weekly_closing_days = source.weekly_closing_days

        return target
