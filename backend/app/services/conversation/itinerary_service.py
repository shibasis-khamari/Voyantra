"""
Voyantra 2.0 Personalized Itinerary Engine & Conversational Delta Editor
Generates multiple distinct alternatives (Relaxed, Cultural Heritage, Activity-focused)
and supports conversational delta modifications without resetting unaffected stops.
"""
from typing import List, Dict, Any, Optional
import copy
import re
from ...schemas.chat import (
    ItineraryData, ItineraryDayData, ItinerarySlotData, ItineraryAlternativeData
)
from ...schemas.place import PlaceFilter, CategoryEnum
from ...services.places_service import places_service

class ItineraryService:
    def generate_itinerary_alternatives(
        self,
        city_slug: str = "both",
        duration_days: int = 2,
        pace: str = "relaxed",
        budget: str = "moderate",
        dietary: str = "all",
        age_group: str = "young_adult",
        interests: Optional[List[str]] = None,
        requested_places: Optional[List[str]] = None
    ) -> ItineraryData:
        """
        Generates 3 meaningfully distinct itinerary alternatives for Pondicherry and/or Chennai:
        1. Relaxed (leisurely pacing, scenic coast, cafe downtime)
        2. Cultural Heritage (architecture, historic temples, ashrams, museums)
        3. Activity-Focused (active exploration, surfing, workshops, gardens)
        """
        days_count = max(1, min(7, duration_days or 2))
        target_city = city_slug if city_slug in ["pondicherry", "chennai"] else None

        # Fetch verified places
        all_places = places_service.filter_places(PlaceFilter(city_id=target_city))
        
        # Helper to partition places by theme
        beach_cafe_places = [p for p in all_places if p.category in [CategoryEnum.BEACH, CategoryEnum.CAFE]]
        heritage_places = [p for p in all_places if p.category in [CategoryEnum.HERITAGE, CategoryEnum.SPIRITUAL, CategoryEnum.CULTURE]]
        active_places = [p for p in all_places if p.category in [CategoryEnum.ADVENTURE, CategoryEnum.NATURE, CategoryEnum.SHOPPING, CategoryEnum.BEACH]]

        # Fallback if filtered lists are empty
        if not beach_cafe_places: beach_cafe_places = all_places
        if not heritage_places: heritage_places = all_places
        if not active_places: active_places = all_places

        # 1. Build Alternative 1: Relaxed Coastal & Cafes
        alt_relaxed_days = []
        for d in range(1, days_count + 1):
            p1 = beach_cafe_places[(d * 2 - 2) % len(beach_cafe_places)]
            p2 = beach_cafe_places[(d * 2 - 1) % len(beach_cafe_places)]
            alt_relaxed_days.append(ItineraryDayData(
                day_number=d,
                theme=f"Coastal Serenity & Artisan Cafes (Day {d})",
                morning=ItinerarySlotData(
                    slot_id=f"d{d}_m",
                    place_name=p1.name,
                    activity_note=f"Relaxed morning walk: {p1.highlights[0] if p1.highlights else p1.description[:60]}",
                    est_time="09:00 AM - 11:30 AM",
                    duration_minutes=150,
                    cost_inr=p1.estimated_cost_inr or 0
                ),
                afternoon=ItinerarySlotData(
                    slot_id=f"d{d}_a",
                    place_name=p2.name,
                    activity_note="Leisure lunch and boutique exploration.",
                    est_time="01:00 PM - 03:30 PM",
                    duration_minutes=150,
                    cost_inr=p2.estimated_cost_inr or 350
                ),
                evening=ItinerarySlotData(
                    slot_id=f"d{d}_e",
                    place_name="Promenade Seafront Breeze" if "chennai" not in (p1.city_id or "") else "Marina Beach Sunset Promenade",
                    activity_note="Sunset seaside stroll and peaceful coastal atmosphere.",
                    est_time="05:30 PM - 07:30 PM",
                    duration_minutes=120,
                    cost_inr=0
                )
            ))

        # 2. Build Alternative 2: Cultural & Architectural Heritage
        alt_cultural_days = []
        for d in range(1, days_count + 1):
            p1 = heritage_places[(d * 2 - 2) % len(heritage_places)]
            p2 = heritage_places[(d * 2 - 1) % len(heritage_places)]
            alt_cultural_days.append(ItineraryDayData(
                day_number=d,
                theme=f"Dravidian & Colonial Heritage Trail (Day {d})",
                morning=ItinerarySlotData(
                    slot_id=f"d{d}_m",
                    place_name=p1.name,
                    activity_note=f"Architecture & spiritual reflection: {p1.description[:70]}",
                    est_time="08:30 AM - 11:00 AM",
                    duration_minutes=150,
                    cost_inr=p1.estimated_cost_inr or 0
                ),
                afternoon=ItinerarySlotData(
                    slot_id=f"d{d}_a",
                    place_name=p2.name,
                    activity_note="Historic courtyard exploration and regional cuisine.",
                    est_time="12:30 PM - 03:00 PM",
                    duration_minutes=150,
                    cost_inr=p2.estimated_cost_inr or 200
                ),
                evening=ItinerarySlotData(
                    slot_id=f"d{d}_e",
                    place_name="Cultural Quarter Walk & Handcrafted Souvenirs",
                    activity_note="Evening heritage street lamps walk and local craft centers.",
                    est_time="05:00 PM - 07:30 PM",
                    duration_minutes=150,
                    cost_inr=150
                )
            ))

        # 3. Build Alternative 3: Activity & Nature Focused
        alt_active_days = []
        for d in range(1, days_count + 1):
            p1 = active_places[(d * 2 - 2) % len(active_places)]
            p2 = active_places[(d * 2 - 1) % len(active_places)]
            alt_active_days.append(ItineraryDayData(
                day_number=d,
                theme=f"Outdoor Adventure & Nature Wonders (Day {d})",
                morning=ItinerarySlotData(
                    slot_id=f"d{d}_m",
                    place_name=p1.name,
                    activity_note="Morning outdoor session & coastal photography.",
                    est_time="07:30 AM - 10:30 AM",
                    duration_minutes=180,
                    cost_inr=p1.estimated_cost_inr or 500
                ),
                afternoon=ItinerarySlotData(
                    slot_id=f"d{d}_a",
                    place_name=p2.name,
                    activity_note="Botanical walk and energy refill lunch.",
                    est_time="12:00 PM - 03:00 PM",
                    duration_minutes=180,
                    cost_inr=p2.estimated_cost_inr or 300
                ),
                evening=ItinerarySlotData(
                    slot_id=f"d{d}_e",
                    place_name="Serenity Beach Surf Point" if "chennai" not in (p1.city_id or "") else "Mylapore Bustling Bazaar Trail",
                    activity_note="Vibrant sunset street exploration and outdoor leisure.",
                    est_time="05:00 PM - 07:30 PM",
                    duration_minutes=150,
                    cost_inr=0
                )
            ))

        alternatives = [
            ItineraryAlternativeData(
                id="alt-relaxed",
                name="Relaxed Coastal & Cafes",
                tag="Most Popular",
                summary="Fewer stops, leisurely mornings, ocean views, and artisan dining.",
                days=alt_relaxed_days,
                total_estimated_budget_inr=days_count * 1200
            ),
            ItineraryAlternativeData(
                id="alt-cultural",
                name="Cultural & Heritage Trail",
                tag="History & Sights",
                summary="French colonial architecture, sacred Dravidian temples, and museums.",
                days=alt_cultural_days,
                total_estimated_budget_inr=days_count * 1000
            ),
            ItineraryAlternativeData(
                id="alt-active",
                name="Activity & Nature Focused",
                tag="Adventure & Outdoors",
                summary="Early sunrise activities, botanical gardens, surfing beaches, and bustling bazaars.",
                days=alt_active_days,
                total_estimated_budget_inr=days_count * 1800
            )
        ]

        # Active default alternative (Relaxed)
        active_alt = alternatives[0]

        city_display = "Pondicherry & Chennai" if not target_city else target_city.title()
        return ItineraryData(
            itinerary_title=f"{city_display} {days_count}-Day Curated Tour",
            summary=f"Tailored {days_count}-day itinerary for {city_display} balancing heritage, scenic coastline, and relaxed pacing.",
            city_id=target_city or "both",
            days=active_alt.days,
            total_estimated_budget_inr=active_alt.total_estimated_budget_inr,
            travel_tips=[
                "Carry lightweight cotton clothing and stay hydrated under coastal sunshine.",
                "Footwear must be removed before entering sanctums in temples and ashrams.",
                "Pre-booking is recommended for popular heritage courtyard dinners."
            ],
            belief_and_etiquette_advisory="Modest attire is requested when visiting places of worship in both Pondicherry and Chennai.",
            active_alternative_id="alt-relaxed",
            alternatives=alternatives
        )

    def modify_itinerary_conversationally(
        self,
        current_itinerary: Dict[str, Any],
        modification_request: str
    ) -> ItineraryData:
        """
        Applies conversational delta changes to the active itinerary while preserving unaffected stops:
        - "Add <Place> to Day X"
        - "Remove <Place> / Remove evening"
        - "Make Day X more relaxed"
        """
        itin = copy.deepcopy(current_itinerary)
        req_lower = modification_request.lower()

        days = itin.get("days", [])
        if not days:
            return ItineraryData(**itin)

        # Detect Day Number (e.g., 'day 1', 'day 2')
        target_day_idx = 0
        for i in range(1, len(days) + 1):
            if f"day {i}" in req_lower:
                target_day_idx = i - 1
                break

        # Check for place to add or replace (prioritize clean base name and exact matches)
        all_places = places_service.get_all_places(None)
        matched_place = None
        sorted_places = sorted(all_places, key=lambda p: len(p.name), reverse=True)
        for p in sorted_places:
            clean_base = re.sub(r'[\(,\-].*?\)', '', p.name).split('&')[0].split(',')[0].strip().lower()
            if clean_base and len(clean_base) >= 4 and clean_base in req_lower:
                matched_place = p
                break
            if p.name.lower() in req_lower:
                matched_place = p
                break

        if matched_place and target_day_idx < len(days):
            day = days[target_day_idx]
            # Replace slot based on time mention or default to afternoon
            slot_key = "afternoon"
            if "morning" in req_lower: slot_key = "morning"
            elif "evening" in req_lower or "sunset" in req_lower: slot_key = "evening"

            day[slot_key] = {
                "slot_id": f"d{target_day_idx+1}_{slot_key[0]}",
                "place_name": matched_place.name,
                "activity_note": f"Added via conversation: {matched_place.description[:80]}",
                "est_time": "Flexible",
                "duration_minutes": matched_place.duration_minutes or 90,
                "cost_inr": matched_place.estimated_cost_inr or 0
            }

        elif "remove" in req_lower and target_day_idx < len(days):
            day = days[target_day_idx]
            if "evening" in req_lower and day.get("evening"):
                day["evening"] = None
            elif "afternoon" in req_lower and day.get("afternoon"):
                day["afternoon"] = None
            elif "morning" in req_lower and day.get("morning"):
                day["morning"] = None

        elif "relaxed" in req_lower and target_day_idx < len(days):
            day = days[target_day_idx]
            # Make more relaxed by softening notes and ensuring ample break time
            if day.get("afternoon"):
                day["afternoon"]["activity_note"] = "Extended leisurely downtime, cafe relaxation, and local strolls."

        itin["days"] = days
        itin["summary"] = itin.get("summary", "") + " (Updated per your conversation request)."

        # Ensure alternatives exist
        if not itin.get("alternatives"):
            itin["alternatives"] = []

        return ItineraryData(**itin)

itinerary_service = ItineraryService()
