"""
Voyantra 2.0 Conversational Chat Schemas
Defines request and response structures for text, Push-to-Talk, and Live Conversation.
"""
from typing import List, Optional, Any, Dict, Literal
from pydantic import BaseModel, Field

IntentType = Literal[
    "general_qa",
    "place_discovery",
    "hotel_discovery",
    "restaurant_discovery",
    "itinerary_planning",
    "itinerary_edit"
]

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    language: Optional[str] = "en"
    timestamp: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

class PlaceCardData(BaseModel):
    id: str
    name: str
    city_id: str
    category: str
    sub_category: Optional[str] = None
    estimated_cost_inr: int = 0
    duration_minutes: int = 60
    rating: float = 4.5
    address: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None

class HotelCardData(BaseModel):
    id: str
    name: str
    city_id: str
    budget_tier: str
    price_per_night_inr: int
    rating: float = 4.5
    address: Optional[str] = None
    amenities: List[str] = Field(default_factory=list)
    proximity_tag: Optional[str] = None
    image_url: Optional[str] = None
    booking_notice: str = "Rates & availability subject to direct property verification."

class RestaurantCardData(BaseModel):
    id: str
    name: str
    city_id: str
    category: str
    budget_tier: str
    dietary_options: List[str] = Field(default_factory=list)
    estimated_cost_inr: int = 0
    address: Optional[str] = None
    image_url: Optional[str] = None

class ItinerarySlotData(BaseModel):
    slot_id: Optional[str] = None
    place_id: Optional[str] = None
    place_name: str
    category: Optional[str] = None
    activity_note: Optional[str] = ""
    est_time: Optional[str] = ""
    duration_minutes: Optional[int] = 60
    cost_inr: Optional[int] = 0
    travel_time_from_prev_minutes: Optional[int] = None
    travel_distance_from_prev_km: Optional[float] = None
    hours_confirmation_required: bool = False

class ItineraryDayData(BaseModel):
    day_number: int
    theme: str
    city_id: Optional[str] = None
    morning: Optional[ItinerarySlotData] = None
    afternoon: Optional[ItinerarySlotData] = None
    evening: Optional[ItinerarySlotData] = None
    custom_stops: Optional[List[ItinerarySlotData]] = None
    day_budget_inr: Optional[int] = None
    estimated_travel_time_minutes: Optional[int] = None

class ItineraryAlternativeData(BaseModel):
    id: str
    name: str
    tag: str
    summary: str
    days: List[ItineraryDayData]
    total_estimated_budget_inr: int
    quality_score: Optional[float] = None

class ItineraryData(BaseModel):
    itinerary_title: str
    summary: str
    city_id: str
    days: List[ItineraryDayData]
    total_estimated_budget_inr: int
    budget_breakdown: Optional[Dict[str, Any]] = None
    budget_disclaimer: Optional[str] = None
    quality_score: Optional[float] = None
    validation_passed: bool = True
    unavailability_notice: Optional[str] = None
    travel_tips: List[str] = Field(default_factory=list)
    belief_and_etiquette_advisory: Optional[str] = None
    active_alternative_id: Optional[str] = "alt-relaxed"
    alternatives: List[ItineraryAlternativeData] = Field(default_factory=list)

class ChatTurnRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    language: Optional[str] = None  # en, hi, ta or None for auto-detect
    voice_mode: Optional[Literal["text", "push_to_talk", "live_voice"]] = "text"
    current_itinerary: Optional[Dict[str, Any]] = None
    user_preferences: Optional[Dict[str, Any]] = None
    duration_days: Optional[int] = 2
    travel_date: Optional[str] = None
    transport_mode: Optional[str] = None
    starting_location: Optional[str] = None
    ending_location: Optional[str] = None
    party_size: Optional[int] = 1

class ChatTurnResponse(BaseModel):
    conversation_id: str
    reply_message: str
    language: str
    intent: IntentType
    places: List[PlaceCardData] = Field(default_factory=list)
    hotels: List[HotelCardData] = Field(default_factory=list)
    restaurants: List[RestaurantCardData] = Field(default_factory=list)
    itinerary: Optional[ItineraryData] = None
    suggested_followups: List[str] = Field(default_factory=list)
    audio_url: Optional[str] = None
    source: Literal["gemini", "verified_catalog", "fallback"] = "gemini"

class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    preview: str
    language: str

class UserMemoryProfile(BaseModel):
    is_memory_enabled: bool = True
    preferred_language: str = "en"
    travel_pace: Optional[str] = "balanced"  # relaxed, balanced, packed
    budget_tier: Optional[str] = "moderate"
    dietary_preference: Optional[str] = "all"
    favorite_activity_types: List[str] = Field(default_factory=list)
    accessibility_needs: Optional[str] = None
    sensitive_cultural_opt_in: bool = False
    sensitive_cultural_preferences: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
