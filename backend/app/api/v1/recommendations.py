import time
import re
from collections import defaultdict
from fastapi import APIRouter, Query, Body, HTTPException, Request, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from ...schemas.recommendation import RecommendationRequest, RecommendationResponse, ConversationalChatRequest, ConversationalChatResponse
from ...schemas.place import AgeGroupEnum, DietaryOptionEnum, BudgetTierEnum, Place
from ...services.ranking_service import ranking_service
from ...services.gemini_service import gemini_service
from ...services.vector_store_service import vector_store_service
from ...services.places_service import places_service
from ...services.conversation.itinerary_service import itinerary_service

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# Sliding window in-memory rate limiter (10 requests per minute per IP)
_rate_limit_history = defaultdict(list)
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW = 60

def apply_rate_limit(client_ip: str):
    now = time.time()
    recent = [t for t in _rate_limit_history[client_ip] if now - t < RATE_LIMIT_WINDOW]
    _rate_limit_history[client_ip] = recent
    if len(recent) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 10 itinerary requests per minute allowed."
        )
    _rate_limit_history[client_ip].append(now)

@router.post("/reset-rate-limit")
def reset_rate_limit():
    """Reset rate limiter state for automated testing isolation."""
    _rate_limit_history.clear()
    return {"status": "reset", "message": "Recommendation rate limiter history cleared"}

class ItineraryRequest(BaseModel):
    city_id: Optional[str] = "pondicherry"
    city: Optional[str] = None
    query_text: str = Field(..., min_length=1, description="Natural language prompt")
    age_group: Optional[Any] = AgeGroupEnum.YOUNG_ADULT
    dietary_preference: Optional[Any] = DietaryOptionEnum.ALL
    duration_days: int = Field(2, ge=1, le=7)
    existing_days: Optional[List[Dict[str, Any]]] = None
    refinement_target_day: Optional[int] = None

    @field_validator("query_text")
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("query_text cannot be empty or blank")
        return v.strip()

@router.post("", response_model=RecommendationResponse)
def get_personalized_recommendations(req: RecommendationRequest):
    return ranking_service.rank_places(req)

@router.get("/preset-suggestions")
def get_preset_suggestions():
    return [
        {
            "id": "sugg-1",
            "title": "Relaxed French Quarter & Beach Walk",
            "prompt": "2-day relaxed weekend with French colonial cafes, Promenade sunset walk, and crepes",
            "category": "heritage",
            "icon": "☕"
        },
        {
            "id": "sugg-2",
            "title": "Spiritual & Ashram Meditation Retreat",
            "prompt": "Quiet 2-day spiritual retreat with meditation at Auroville Matrimandir and Sri Aurobindo Ashram",
            "category": "spiritual",
            "icon": "🧘"
        },
        {
            "id": "sugg-3",
            "title": "Youth Surfing & Cafe Hopping",
            "prompt": "Vibrant weekend with Serenity Beach surfing lessons, yellow wall photos, and iced coffees for 18-25s",
            "category": "adventure",
            "icon": "🏄"
        },
        {
            "id": "sugg-4",
            "title": "Family Nature & Garden Tour",
            "prompt": "Family-friendly 2-day trip with Botanical Gardens, toy train, accessible heritage sights, and beach walk",
            "category": "nature",
            "icon": "🌴"
        },
        {
            "id": "sugg-5",
            "title": "Strict Jain & Ganesha Temple Trail",
            "prompt": "Strict Jain zero-onion zero-garlic South Indian breakfast, ancient Ganesha temple, and heritage walk",
            "category": "dining",
            "icon": "🍲"
        },
        {
            "id": "sugg-6",
            "title": "Chennai Heritage, Mylapore & Marina Trail",
            "prompt": "2-day Chennai itinerary featuring Marina Beach sunrise, Kapaleeshwarar Temple Dravidian architecture, and filter coffee in Mylapore",
            "category": "heritage",
            "icon": "🏛️"
        },
        {
            "id": "sugg-7",
            "title": "Pondicherry & Chennai Coastal Grand Tour",
            "prompt": "3-day coastal tour exploring best destinations across both Pondicherry and Chennai: French Quarter, Promenade, Marina Beach, and ancient temples",
            "category": "coastal",
            "icon": "🌊"
        },
        {
            "id": "sugg-8",
            "title": "Vintage Polaroid Yellow Walls Walk (Niche)",
            "prompt": "Where can I take aesthetic vintage polaroid photos with mustard yellow French walls and bougainvillea streets?",
            "category": "heritage",
            "icon": "📸"
        },
        {
            "id": "sugg-9",
            "title": "Silent 4 AM Meditation & Reflection (Unusual)",
            "prompt": "Where can I sit in total silence for early morning meditation without any crowds or mobile phones?",
            "category": "spiritual",
            "icon": "🌌"
        }
    ]

@router.post("/parse-query")
def parse_query(query_text: str = Body(..., embed=True)):
    if not query_text or not query_text.strip():
        raise HTTPException(status_code=422, detail="query_text cannot be empty")
    return gemini_service.parse_natural_language_query(query_text)

COMMON_WORLD_DESTINATIONS = [
    # Top Indian Destinations
    "mumbai", "delhi", "new delhi", "bengaluru", "bangalore", "jaipur", "goa", "kerala",
    "himachal pradesh", "himachal", "manali", "shimla", "kashmir", "ladakh", "leh",
    "kolkata", "hyderabad", "agra", "varanasi", "udaipur", "jodhpur", "amritsar",
    "rishikesh", "pondicherry", "puducherry", "pondy", "chennai", "madras", "mysore",
    "ooty", "kodaikanal", "munnar", "hampi", "andaman", "sikkim", "darjeeling", "pune",
    "ahmedabad", "chandigarh", "lucknow", "coorg", "wayanad", "alleppey", "kochi",
    # Top Global Destinations
    "tokyo", "kyoto", "osaka", "japan", "paris", "france", "bali", "indonesia",
    "dubai", "uae", "abu dhabi", "singapore", "bangkok", "phuket", "thailand",
    "london", "uk", "england", "new york", "nyc", "usa", "san francisco", "los angeles",
    "rome", "italy", "florence", "venice", "barcelona", "madrid", "spain",
    "amsterdam", "netherlands", "switzerland", "zurich", "geneva", "interlaken",
    "vietnam", "hanoi", "da nang", "ho chi minh", "maldives", "sri lanka", "colombo",
    "nepal", "kathmandu", "turkey", "istanbul", "cairo", "egypt", "sydney", "australia",
    "melbourne", "seoul", "south korea", "berlin", "germany", "greece", "athens", "santorini"
]

def detect_target_destination(
    message: str,
    history: Optional[List[Any]] = None,
    default_city: Optional[str] = None
) -> tuple[str, str]:
    """
    Detects the user's intended travel destination dynamically from the message,
    recent conversation history, or request parameters.
    Returns (city_slug, display_name).
    """
    msg_clean = (message or "").strip()
    msg_lower = msg_clean.lower()

    # Check for both Pondicherry and Chennai in the query
    has_chennai = bool(re.search(r"\b(chennai|madras)\b", msg_lower))
    has_pondy = bool(re.search(r"\b(pondy|puducherry|pondicherry)\b", msg_lower))

    if has_chennai and has_pondy:
        return "both", "Pondicherry & Chennai"
    if has_chennai and not has_pondy:
        return "chennai", "Chennai"
    if has_pondy and not has_chennai:
        return "pondicherry", "Pondicherry"

    # 1. Direct match in dictionary of common world & Indian destinations
    for dest in COMMON_WORLD_DESTINATIONS:
        pattern = rf"\b{re.escape(dest)}\b"
        if re.search(pattern, msg_lower):
            if dest in ["bangalore", "bengaluru"]:
                return "bengaluru", "Bengaluru"
            if dest in ["pondy", "puducherry", "pondicherry"]:
                return "pondicherry", "Pondicherry"
            if dest in ["madras", "chennai"]:
                return "chennai", "Chennai"
            if dest in ["himachal", "himachal pradesh"]:
                return "himachal-pradesh", "Himachal Pradesh"
            if dest == "new delhi":
                return "delhi", "Delhi"
            if dest == "nyc":
                return "new-york", "New York"
            return dest.replace(" ", "-"), dest.title()

    # 2. Check prepositional patterns: "in <Destination>", "to <Destination>", "visit <Destination>"
    match = re.search(
        r'\b(?:in|to|around|for|visit|visiting|explore|exploring|near|trip to|travel to|vacation in|holiday in|tour of)\s+([A-Z][a-zA-Z\s]{1,25})(?:[?!.,]|$|\s+(?:this|next|for|with)\b)',
        msg_clean
    )
    if match:
        extracted = match.group(1).strip()
        stop_words = {
            "breakfast", "lunch", "dinner", "evening", "morning", "afternoon",
            "summer", "winter", "weekend", "a day", "two days", "family",
            "friends", "couple", "budget", "luxury", "tomorrow", "tonight"
        }
        if extracted.lower() not in stop_words and len(extracted) > 2:
            return extracted.lower().replace(" ", "-"), extracted.title()

    # 3. Check recent conversation history for established destination
    if history:
        for turn in reversed(history[-4:]):
            content = turn.get("content", "") if isinstance(turn, dict) else getattr(turn, "content", "")
            c_lower = (content or "").lower()
            for dest in COMMON_WORLD_DESTINATIONS:
                if re.search(rf"\b{re.escape(dest)}\b", c_lower):
                    if dest in ["bangalore", "bengaluru"]:
                        return "bengaluru", "Bengaluru"
                    if dest in ["pondy", "puducherry", "pondicherry"]:
                        return "pondicherry", "Pondicherry"
                    if dest in ["madras", "chennai"]:
                        return "chennai", "Chennai"
                    if dest in ["himachal", "himachal pradesh"]:
                        return "himachal-pradesh", "Himachal Pradesh"
                    return dest.replace(" ", "-"), dest.title()

    # 4. Fallback to passed default city or both
    fallback = (default_city or "both").strip().lower()
    if fallback in ["all", "both", "any"]:
        return "both", "Pondicherry & Chennai"
    return fallback.replace(" ", "-"), fallback.replace("-", " ").title()

@router.post("/chat", response_model=ConversationalChatResponse)
def chat_with_concierge(req: ConversationalChatRequest, request: Request):
    """
    Conversational AI Concierge for worldwide rational dialogue, hotel/dining advice,
    and flexible itinerary planning for destinations across India and globally.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    apply_rate_limit(client_ip)

    history_dicts = [{"role": m.role, "content": m.content} for m in req.conversation_history]

    # Dynamically detect destination from message, history, or request payload
    resolved_slug, resolved_name = detect_target_destination(
        message=req.message,
        history=history_dicts,
        default_city=req.city_id or req.city
    )

    # Check for local catalog destinations (e.g. pondicherry, chennai)
    all_city_places = places_service.get_all_places(resolved_slug)
    catalog_places = []
    if all_city_places:
        vector_results = vector_store_service.search_semantic_places(req.message, city_id=resolved_slug, top_k=12)
        ranked_places = [item[0] for item in vector_results] if vector_results else all_city_places[:12]
        catalog_places = ranked_places + [p for p in all_city_places if p.id not in [x.id for x in ranked_places]]

    res = gemini_service.chat_conversational(
        message=req.message,
        city_name=resolved_name,
        retrieved_places=catalog_places,
        conversation_history=history_dicts,
        current_itinerary=req.current_itinerary,
        user_age=req.age_group,
        user_diet=req.dietary_preference,
        duration_days=req.duration_days or 2
    )
    return res

@router.post("/generate-itinerary")
def generate_ai_itinerary(req: ItineraryRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    apply_rate_limit(client_ip)

    # Dynamically detect destination from natural language query or request
    resolved_slug, resolved_name = detect_target_destination(
        message=req.query_text,
        history=None,
        default_city=req.city_id or req.city
    )

    all_city_places = places_service.get_all_places(resolved_slug)
    
    # 2. RAG Vector Search (if local catalog exists)
    filtered_places: List[Place] = []
    if all_city_places:
        vector_results = vector_store_service.search_semantic_places(req.query_text, city_id=resolved_slug, top_k=12)
        retrieved_places = [item[0] for item in vector_results] if vector_results else all_city_places[:12]

        # Hard Constraint Dietary Filter
        q_lower = req.query_text.lower()
        is_strict_jain = "jain" in q_lower or "zero-onion" in q_lower or req.dietary_preference == DietaryOptionEnum.PURE_VEG_JAIN
        is_halal = "halal" in q_lower or req.dietary_preference == DietaryOptionEnum.HALAL
        is_vegan = "vegan" in q_lower or req.dietary_preference == DietaryOptionEnum.VEGAN

        for p in retrieved_places:
            if p.category not in ["cafe", "dining"]:
                filtered_places.append(p)
                continue
            
            opts = [d.value for d in p.dietary_options]
            if is_strict_jain:
                if DietaryOptionEnum.PURE_VEG_JAIN.value in opts or "pure_veg_jain" in opts:
                    filtered_places.append(p)
            elif is_halal:
                if DietaryOptionEnum.HALAL.value in opts or "halal" in opts:
                    filtered_places.append(p)
            elif is_vegan:
                if DietaryOptionEnum.VEGAN.value in opts or "vegan" in opts:
                    filtered_places.append(p)
            else:
                filtered_places.append(p)

        if len(filtered_places) < 4:
            for p in all_city_places:
                if p.id not in [x.id for x in filtered_places]:
                    if p.category not in ["cafe", "dining"]:
                        filtered_places.append(p)
                    elif is_strict_jain and DietaryOptionEnum.PURE_VEG_JAIN.value in [d.value for d in p.dietary_options]:
                        filtered_places.append(p)

    q_lower = req.query_text.lower()
    is_strict_jain = "jain" in q_lower or "zero-onion" in q_lower or req.dietary_preference == DietaryOptionEnum.PURE_VEG_JAIN
    is_day2_refinement = "day 2" in q_lower or "day2" in q_lower
    prev_days = req.existing_days if (is_day2_refinement and req.existing_days) else None

    catalog_places = filtered_places + [p for p in all_city_places if p.id not in [x.id for x in filtered_places]]

    available_alternatives = [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category.value if hasattr(p.category, "value") else str(p.category),
            "sub_category": p.sub_category,
            "estimated_cost_inr": p.estimated_cost_inr,
            "duration_minutes": p.duration_minutes
        }
        for p in catalog_places
    ]

    # Use unified V2 engine for supported destinations (Pondicherry, Chennai, Both)
    if resolved_slug in ["pondicherry", "chennai", "both"]:
        age_str = req.age_group.value if hasattr(req.age_group, "value") else str(req.age_group or "young_adult")
        diet_str = req.dietary_preference.value if hasattr(req.dietary_preference, "value") else str(req.dietary_preference or "all")

        if req.existing_days:
            cur_itin = {
                "itinerary_title": f"{resolved_name} Curated Tour",
                "summary": "Existing itinerary",
                "city_id": resolved_slug,
                "days": req.existing_days,
                "total_estimated_budget_inr": sum(d.get("day_budget_inr", 0) for d in req.existing_days)
            }
            itin_data = itinerary_service.modify_itinerary_conversationally(cur_itin, req.query_text)
        else:
            itin_data = itinerary_service.generate_itinerary_alternatives(
                city_slug=resolved_slug,
                duration_days=req.duration_days,
                age_group=age_str,
                dietary=diet_str,
                requested_places=[req.query_text]
            )

        itin_dict = itin_data.model_dump()
        return {
            "city_id": resolved_slug,
            "query_text": req.query_text,
            "retrieved_places_count": len(filtered_places),
            "available_alternatives": available_alternatives,
            "itinerary": itin_dict
        }

    # 3. Fallback Synthesize with Gemini API for outside destinations
    itinerary = gemini_service.generate_rag_itinerary(
        query_text=req.query_text,
        retrieved_places=catalog_places,
        user_age=req.age_group or AgeGroupEnum.YOUNG_ADULT,
        user_diet=DietaryOptionEnum.PURE_VEG_JAIN if is_strict_jain else (req.dietary_preference or DietaryOptionEnum.ALL),
        duration_days=req.duration_days,
        city_name=resolved_name,
        existing_days=prev_days
    )

    return {
        "city_id": resolved_slug,
        "query_text": req.query_text,
        "retrieved_places_count": len(filtered_places),
        "available_alternatives": available_alternatives,
        "itinerary": itinerary
    }
