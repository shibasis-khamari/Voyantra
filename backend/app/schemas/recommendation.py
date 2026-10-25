from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union
from .place import Place, AgeGroupEnum, DietaryOptionEnum, BudgetTierEnum

class ComponentScores(BaseModel):
    w_category: float
    c_budget: float
    f_dietary: float
    a_accessibility: float

class RecommendationRequest(BaseModel):
    city_id: Optional[str] = "pondicherry"
    city: Optional[str] = None
    age: Optional[int] = None
    age_group: Optional[Any] = None
    dietary_preference: Optional[Any] = DietaryOptionEnum.ALL
    budget_tier: Optional[Any] = BudgetTierEnum.MODERATE
    interests: Optional[List[str]] = None
    travel_dates: Optional[List[str]] = None
    query_text: Optional[str] = None

class RankedPlaceItem(BaseModel):
    place: Place
    match_score: float  # 0 to 100 percentage
    component_scores: Optional[ComponentScores] = None
    match_reasons: List[str] = Field(default_factory=list)
    crowd_status: str = "medium"  # low, medium, high
    advisory: Optional[str] = None

class RecommendationResponse(BaseModel):
    city_id: str
    total_results: int
    ranked_places: List[RankedPlaceItem]
    applied_preferences: dict
