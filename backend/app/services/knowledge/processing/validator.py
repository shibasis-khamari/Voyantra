"""
Voyantra Knowledge Entity Validator
Enforces data integrity, conservative missing-data fallbacks, and verification boundaries.
Never invents coordinates, prices, opening hours, or operating statuses.
"""
from typing import Dict, Any, List, Tuple
from ....schemas.knowledge import KnowledgeEntity, VerificationStatusEnum, PriceStatusEnum

CATEGORY_DEFAULT_DURATIONS = {
    "spiritual": 60,
    "beach": 90,
    "heritage": 90,
    "nature": 90,
    "cafe": 60,
    "dining": 60,
    "culture": 75,
}


class EntityValidator:
    def validate(self, entity: KnowledgeEntity) -> Tuple[KnowledgeEntity, List[str]]:
        """
        Validates entity fields, applies conservative fallback rules, and collects validation issues.
        Returns (validated_entity, issue_codes).
        """
        issues: List[str] = []

        # 1. Coordinates check
        if not entity.coordinates or "lat" not in entity.coordinates or "lng" not in entity.coordinates:
            issues.append("missing_coordinates")
            # We do NOT invent coordinates! Leave as None.
            entity.coordinates = None

        # 2. Price accuracy check
        if entity.estimated_cost_inr is None or entity.estimated_cost_inr <= 0:
            entity.estimated_cost_inr = 0
            entity.price_status = PriceStatusEnum.UNKNOWN
        else:
            # If price is provided but not verified, mark as estimated
            if entity.verification_status != VerificationStatusEnum.VERIFIED:
                entity.price_status = PriceStatusEnum.ESTIMATED

        # 3. Duration estimate check
        if entity.duration_minutes is None or entity.duration_minutes <= 0:
            cat = (entity.category or "").lower()
            default_dur = CATEGORY_DEFAULT_DURATIONS.get(cat, 60)
            entity.duration_minutes = default_dur
            entity.duration_estimated = True
            issues.append("duration_estimated")

        # 4. Opening hours verification check
        if not entity.opening_hours:
            entity.opening_hours_verified = False
            entity.opening_hours = None
        elif not entity.opening_hours_verified:
            entity.opening_hours_verified = False

        # 5. Name sanity check
        if not entity.name or len(entity.name.strip()) < 2:
            issues.append("invalid_name")

        return entity, issues
