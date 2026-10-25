import time
import re
from collections import defaultdict
from fastapi import APIRouter, Query, Body, HTTPException, Request, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from ...schemas.recommendation import RecommendationRequest, RecommendationResponse
from ...schemas.place import AgeGroupEnum, DietaryOptionEnum, BudgetTierEnum, Place
from ...services.ranking_service import ranking_service
from ...services.gemini_service import gemini_service
from ...services.vector_store_service import vector_store_service
from ...services.places_service import places_service

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# Sliding window in-memory rate limiter (10 requests per minute per IP)
_rate_limit_history = defaultdict(list)
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW = 60

# Cache last generated itinerary per client IP for refinement state preservation
_last_generated_itinerary = {}

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
            "title": "Vintage Polaroid Yellow Walls Walk (Niche)",
            "prompt": "Where can I take aesthetic vintage polaroid photos with mustard yellow French walls and bougainvillea streets?",
            "category": "heritage",
            "icon": "📸"
        },
        {
            "id": "sugg-7",
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

@router.post("/generate-itinerary")
def generate_ai_itinerary(req: ItineraryRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    apply_rate_limit(client_ip)

    resolved_city = (req.city_id or req.city or "pondicherry").strip().lower()

    # 1. Geographic Boundary Validation
    if resolved_city not in ["pondicherry", "chennai"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"City '{resolved_city}' is outside Voyantra's operating boundaries. Please select Pondicherry or Chennai."
        )

    # Check for out-of-scope cities in query text
    out_of_scope_cities = ["bangalore", "bengaluru", "delhi", "mumbai", "kolkata", "hyderabad", "goa", "kodaikanal", "ooty", "kerala", "jaipur"]
    q_words = set(re.findall(r'\b[a-z]+\b', req.query_text.lower()))
    has_target_city = any(tc in q_words for tc in ["pondicherry", "chennai", "pondy", "madras"])
    found_out = [c for c in out_of_scope_cities if c in q_words]
    if found_out and not has_target_city:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Voyantra's trip planning pilot currently only covers Pondicherry and Chennai. Destination '{found_out[0].title()}' is outside our geographical boundaries."
        )

    all_city_places = places_service.get_all_places(resolved_city)
    
    # 2. RAG Vector Search
    vector_results = vector_store_service.search_semantic_places(req.query_text, city_id=resolved_city, top_k=12)
    retrieved_places = [item[0] for item in vector_results]

    if not retrieved_places:
        retrieved_places = all_city_places[:12]

    # Hard Constraint Dietary Filter
    q_lower = req.query_text.lower()
    is_strict_jain = "jain" in q_lower or "zero-onion" in q_lower or req.dietary_preference == DietaryOptionEnum.PURE_VEG_JAIN
    is_halal = "halal" in q_lower or req.dietary_preference == DietaryOptionEnum.HALAL
    is_vegan = "vegan" in q_lower or req.dietary_preference == DietaryOptionEnum.VEGAN

    filtered_places: List[Place] = []
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

    cities = places_service.get_cities()
    city_name = next((c["name"] for c in cities if c["id"] == resolved_city), resolved_city.title())

    # Check for previous existing_days from request or server-side cache
    prev_days = req.existing_days
    if not prev_days and client_ip in _last_generated_itinerary:
        prev_days = _last_generated_itinerary[client_ip].get("days")

    # 3. Synthesize with Gemini API
    itinerary = gemini_service.generate_rag_itinerary(
        query_text=req.query_text,
        retrieved_places=filtered_places[:8],
        user_age=req.age_group or AgeGroupEnum.YOUNG_ADULT,
        user_diet=DietaryOptionEnum.PURE_VEG_JAIN if is_strict_jain else (req.dietary_preference or DietaryOptionEnum.ALL),
        duration_days=req.duration_days,
        city_name=city_name,
        existing_days=prev_days
    )

    # Cache this itinerary for subsequent refinement calls
    _last_generated_itinerary[client_ip] = itinerary

    available_alternatives = [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category.value,
            "sub_category": p.sub_category,
            "estimated_cost_inr": p.estimated_cost_inr,
            "duration_minutes": p.duration_minutes
        }
        for p in (filtered_places + [p for p in all_city_places if p.id not in [x.id for x in filtered_places]])
    ]

    return {
        "city_id": resolved_city,
        "query_text": req.query_text,
        "retrieved_places_count": len(filtered_places),
        "available_alternatives": available_alternatives,
        "itinerary": itinerary
    }
