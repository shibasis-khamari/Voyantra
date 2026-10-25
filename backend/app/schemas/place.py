from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class CategoryEnum(str, Enum):
    HERITAGE = "heritage"
    BEACH = "beach"
    SPIRITUAL = "spiritual"
    CAFE = "cafe"
    DINING = "dining"
    NATURE = "nature"
    SHOPPING = "shopping"
    NIGHTLIFE = "nightlife"
    ADVENTURE = "adventure"
    CULTURE = "culture"

class BudgetTierEnum(str, Enum):
    BUDGET = "budget"        # ₹ (Free - Low cost)
    MODERATE = "moderate"    # ₹₹ (Mid-range)
    LUXURY = "luxury"        # ₹₹₹ (Premium/Fine dining/Resort)

class CrowdTendencyEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AgeGroupEnum(str, Enum):
    ALL = "all"
    YOUNG_ADULT = "young_adult"  # 18-25: Adventure, cafes, vibrant nightlife
    ADULT = "adult"              # 26-40: Heritage, boutique cafes, relaxed spots
    FAMILY = "family"            # 41-60: Family-friendly, clean amenities, safe pacing
    SENIOR = "senior"            # 60+: Accessible, tranquil, spiritual, low walking fatigue

class DietaryOptionEnum(str, Enum):
    ALL = "all"
    VEGETARIAN = "vegetarian"
    PURE_VEG_JAIN = "pure_veg_jain"
    HALAL = "halal"
    VEGAN = "vegan"
    KOSHER = "kosher"
    NON_VEG = "non_veg"

class BeliefAffiliationEnum(str, Enum):
    SECULAR = "secular"
    INTERFAITH_SPIRITUAL = "interfaith_spiritual"
    HINDU = "hindu"
    CHRISTIAN_CATHOLIC = "christian_catholic"
    CHRISTIAN_PROTESTANT = "christian_protestant"
    MUSLIM = "muslim"
    JAIN = "jain"
    BUDDHIST = "buddhist"
    CULTURAL_AGNOSTIC = "cultural_agnostic"

class EtiquetteRules(BaseModel):
    dress_code: Optional[str] = "Casual comfortable clothing"
    footwear: Optional[str] = "Footwear allowed"
    silence_policy: Optional[str] = "Normal noise levels permitted"
    photography: Optional[str] = "Photography allowed"
    gender_rules: Optional[str] = "All welcome together"

class Coordinates(BaseModel):
    lat: float
    lng: float

class PlaceBase(BaseModel):
    id: str
    city_id: str
    name: str
    category: CategoryEnum
    sub_category: Optional[str] = None
    description: str
    highlights: List[str] = []
    budget_tier: BudgetTierEnum
    estimated_cost_inr: int = 0
    duration_minutes: int = 60
    coordinates: Coordinates
    address: str
    image_url: str
    best_time_to_visit: Optional[str] = "Morning/Evening"
    crowd_tendency: CrowdTendencyEnum = CrowdTendencyEnum.MEDIUM
    recommended_age_groups: List[AgeGroupEnum] = [AgeGroupEnum.ALL]
    dietary_options: List[DietaryOptionEnum] = [DietaryOptionEnum.ALL]

    # Enhanced Religion, Beliefs & Niche Interest Differentiation Fields
    belief_affiliation: BeliefAffiliationEnum = BeliefAffiliationEnum.SECULAR
    etiquette_rules: Optional[EtiquetteRules] = Field(default_factory=EtiquetteRules)
    niche_interests: List[str] = []
    weird_query_matches: List[str] = []

    dress_code_advisory: Optional[str] = None
    accessibility_rating: int = 3  # 1-5 scale
    tags: List[str] = []
    rating: float = 4.5
    review_count: int = 120

class Place(PlaceBase):
    pass

class PlaceFilter(BaseModel):
    city_id: Optional[str] = "pondicherry"
    categories: Optional[List[CategoryEnum]] = None
    budget_tiers: Optional[List[BudgetTierEnum]] = None
    age_group: Optional[AgeGroupEnum] = None
    dietary_preference: Optional[DietaryOptionEnum] = None
    belief_affiliation: Optional[BeliefAffiliationEnum] = None
    max_cost_inr: Optional[int] = None
    search_query: Optional[str] = None
    min_accessibility: Optional[int] = None
