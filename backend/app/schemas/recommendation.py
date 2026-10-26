from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union, Literal, Dict
from .place import Place, AgeGroupEnum, DietaryOptionEnum, BudgetTierEnum

class ItinerarySlot(BaseModel):
    place_name: str
    activity_note: str = ""
    est_time: str = ""

class ItineraryDay(BaseModel):
    day_number: int
    theme: str
    morning: Optional[ItinerarySlot] = None
    afternoon: Optional[ItinerarySlot] = None
    evening: Optional[ItinerarySlot] = None

class ItineraryResponse(BaseModel):
    itinerary_title: str
    feasibility_status: str = "100% Feasible"
    has_unavailability_warning: bool = False
    unavailability_notice: Optional[str] = None
    summary: str
    days: List[ItineraryDay]
    total_estimated_budget_inr: int
    belief_and_etiquette_advisory: Optional[str] = None
    travel_tips: List[str] = Field(default_factory=list)
    source: Literal["gemini", "fallback"] = "gemini"
    fallback_reason: Optional[str] = None

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

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[str] = None

class ConversationalChatRequest(BaseModel):
    city_id: Optional[str] = "pondicherry"
    city: Optional[str] = None
    message: str = Field(..., min_length=1)
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    current_itinerary: Optional[Dict[str, Any]] = None
    age_group: Optional[Any] = AgeGroupEnum.YOUNG_ADULT
    dietary_preference: Optional[Any] = DietaryOptionEnum.ALL
    duration_days: Optional[int] = 2

class RecommendedPlacePreview(BaseModel):
    id: str
    name: str
    category: str
    sub_category: Optional[str] = None
    estimated_cost_inr: int = 0
    duration_minutes: int = 60
    highlights: List[str] = Field(default_factory=list)
    dietary_options: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None

class ConversationalChatResponse(BaseModel):
    city_id: str
    reply_message: str
    intent: Literal["chat", "place_info", "itinerary"]
    recommended_places: List[RecommendedPlacePreview] = Field(default_factory=list)
    itinerary: Optional[ItineraryResponse] = None
    suggested_followups: List[str] = Field(default_factory=list)
    source: Literal["gemini", "fallback"] = "gemini"
    fallback_reason: Optional[str] = None

