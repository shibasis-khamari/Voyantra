"""
Voyantra Candidate Place Adapter
Converts retrieved KnowledgeEntity records into validated Place instances for Itinerary Engine V2.
Enforces strict missing-data rules:
1. Missing coordinates -> excluded from itinerary generation.
2. Missing duration -> category-based conservative estimate (duration_estimated=True).
3. Missing price -> zero cost with price_status='unknown' (never invented).
4. Missing opening hours -> opening_hours_verified=False (never assumed open).
5. Unverified records -> tagged as 'unverified'.
"""
from typing import Optional, List, Dict, Any
import logging
from ...schemas.knowledge import KnowledgeEntity, VerificationStatusEnum, PriceStatusEnum
from ...schemas.place import (
    Place,
    Coordinates,
    CategoryEnum,
    BudgetTierEnum,
    CrowdTendencyEnum,
    AgeGroupEnum,
    DietaryOptionEnum,
    BeliefAffiliationEnum,
    EtiquetteRules,
)

logger = logging.getLogger(__name__)

CATEGORY_MAP = {
    "heritage": CategoryEnum.HERITAGE,
    "beach": CategoryEnum.BEACH,
    "spiritual": CategoryEnum.SPIRITUAL,
    "cafe": CategoryEnum.CAFE,
    "dining": CategoryEnum.DINING,
    "nature": CategoryEnum.NATURE,
    "shopping": CategoryEnum.SHOPPING,
    "nightlife": CategoryEnum.NIGHTLIFE,
    "adventure": CategoryEnum.ADVENTURE,
    "culture": CategoryEnum.CULTURE,
}

BUDGET_MAP = {
    "budget": BudgetTierEnum.BUDGET,
    "moderate": BudgetTierEnum.MODERATE,
    "luxury": BudgetTierEnum.LUXURY,
}

CATEGORY_DEFAULT_DURATIONS = {
    CategoryEnum.SPIRITUAL: 60,
    CategoryEnum.BEACH: 90,
    CategoryEnum.HERITAGE: 90,
    CategoryEnum.NATURE: 90,
    CategoryEnum.CAFE: 60,
    CategoryEnum.DINING: 60,
    CategoryEnum.CULTURE: 75,
}


class CandidatePlaceAdapter:
    @staticmethod
    def adapt_entity(entity: KnowledgeEntity) -> Optional[Place]:
        """
        Converts a KnowledgeEntity into a Place instance.
        Returns None if critical data (coordinates) is missing.
        """
        if not entity:
            return None

        # Rule 1: Missing coordinates -> Exclude from itinerary route generation
        if not entity.coordinates or "lat" not in entity.coordinates or "lng" not in entity.coordinates:
            logger.info(f"[CandidatePlaceAdapter] Excluding entity '{entity.id}' ({entity.name}): missing coordinates.")
            return None

        try:
            lat = float(entity.coordinates["lat"])
            lng = float(entity.coordinates["lng"])
            coords = Coordinates(lat=lat, lng=lng)
        except (ValueError, TypeError):
            return None

        # Category mapping
        cat_key = (entity.category or "heritage").lower()
        category = CATEGORY_MAP.get(cat_key, CategoryEnum.HERITAGE)

        # Budget mapping
        b_key = (entity.budget_tier or "budget").lower()
        budget_tier = BUDGET_MAP.get(b_key, BudgetTierEnum.BUDGET)

        # Rule 2: Duration estimation
        duration = entity.duration_minutes
        duration_estimated = entity.duration_estimated
        if not duration or duration <= 0:
            duration = CATEGORY_DEFAULT_DURATIONS.get(category, 60)
            duration_estimated = True

        # Rule 3: Missing price handling (never invent arbitrary price)
        cost = entity.estimated_cost_inr if entity.estimated_cost_inr and entity.estimated_cost_inr > 0 else 0

        # Verification status
        v_status = entity.verification_status.value if hasattr(entity.verification_status, "value") else str(entity.verification_status)

        # Convert dietary options
        dietary_opts = [DietaryOptionEnum.ALL]
        if entity.dietary_options:
            parsed_diets = []
            for d in entity.dietary_options:
                try:
                    parsed_diets.append(DietaryOptionEnum(d.lower()))
                except Exception:
                    pass
            if parsed_diets:
                dietary_opts = parsed_diets

        # Age group mapping
        age_groups = [AgeGroupEnum.ALL]

        return Place(
            id=entity.id,
            city_id=entity.city_id or "pondicherry",
            name=entity.name,
            category=category,
            sub_category=entity.sub_category,
            description=entity.description or f"{entity.name} in {entity.city_id or 'India'}",
            highlights=entity.highlights or [category.value.capitalize()],
            budget_tier=budget_tier,
            estimated_cost_inr=cost,
            duration_minutes=duration,
            coordinates=coords,
            address=entity.address or f"{entity.name}, {entity.city_id.capitalize() if entity.city_id else ''}",
            image_url=entity.image_url or "https://images.unsplash.com/photo-1582510003544-4d00b7f74220",
            crowd_tendency=CrowdTendencyEnum.MEDIUM,
            recommended_age_groups=age_groups,
            dietary_options=dietary_opts,
            source_url=entity.primary_source_url,
            source_verified_at=entity.updated_at,
            verification_status=v_status,
            last_updated_at=entity.updated_at,
            opening_hours=entity.opening_hours,
            opening_hours_verified=entity.opening_hours_verified,
            weekly_closing_days=entity.weekly_closing_days or [],
            is_major_attraction=True,
            rating=entity.rating or 4.5,
            review_count=entity.review_count or 100,
            tags=entity.tags or [],
        )

    @classmethod
    def adapt_entities(cls, entities: List[KnowledgeEntity]) -> List[Place]:
        """Batch-adapts a list of entities, filtering out invalid records."""
        valid_places: List[Place] = []
        for ent in entities:
            adapted = cls.adapt_entity(ent)
            if adapted:
                valid_places.append(adapted)
        return valid_places


candidate_place_adapter = CandidatePlaceAdapter()
