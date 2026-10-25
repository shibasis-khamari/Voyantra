import sys
from pathlib import Path
sys.path.insert(0, str(Path('backend').resolve()))

from app.services.gemini_service import gemini_service
from app.services.places_service import places_service
from app.schemas.place import AgeGroupEnum, DietaryOptionEnum

# Save original key
original_key = gemini_service.api_key

try:
    # Set invalid key
    gemini_service.api_key = "AIzaSyInvalidKeyTest123456789"
    places = places_service.get_all_places("pondicherry")
    
    res = gemini_service.generate_rag_itinerary(
        query_text="2-day trip to Pondicherry",
        retrieved_places=places[:6],
        user_age=AgeGroupEnum.YOUNG_ADULT,
        user_diet=DietaryOptionEnum.ALL,
        duration_days=2,
        city_name="Pondicherry"
    )
    print("Invalid key response type:", type(res))
    print("Itinerary title:", res.get("itinerary_title"))
    print("Days generated:", len(res.get("days", [])))
    print("Feasibility status:", res.get("feasibility_status"))
    print("Graceful fallback worked?:", res.get("itinerary_title") is not None and len(res.get("days", [])) == 2)
finally:
    gemini_service.api_key = original_key
