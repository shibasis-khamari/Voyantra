import os
import json
import re
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

from ..core.config import settings
from ..schemas.place import Place, CategoryEnum, BudgetTierEnum, AgeGroupEnum, DietaryOptionEnum, BeliefAffiliationEnum

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY or ""

    def parse_natural_language_query(self, query_text: str) -> Dict[str, Any]:
        """
        Uses Gemini API to parse free-text input into structured JSON filters.
        """
        if self.api_key and len(self.api_key) > 5:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={self.api_key}"
            prompt = f"""
            You are an AI travel query parser for the Voyantra tourist platform.
            Parse the following user travel request into structured JSON filters:
            User Request: "{query_text}"

            Return ONLY valid JSON matching this exact schema:
            {{
                "categories": ["heritage", "beach", "spiritual", "cafe", "dining", "nature", "adventure"],
                "budget_tier": "budget" | "moderate" | "luxury",
                "belief_affiliation": "secular" | "interfaith_spiritual" | "hindu" | "christian_catholic" | "muslim" | "jain",
                "pace": "relaxed" | "balanced" | "fast_paced",
                "crowd_tolerance": "low" | "medium" | "high",
                "duration_days": 1 or 2 or 3,
                "niche_interests": ["keyword1", "keyword2"]
            }}
            Do not include markdown code block formatting (```json). Output raw valid JSON only.
            """

            try:
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}
                }
                res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=8)
                if res.ok:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text_response = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        clean_text = text_response.replace("```json", "").replace("```", "").strip()
                        return json.loads(clean_text)
            except Exception as e:
                print(f"[GeminiService] Error calling Gemini API for query parsing: {e}")

        # Fallback Heuristic Parser
        q = query_text.lower()
        categories = []
        if any(w in q for w in ["beach", "sea", "ocean", "surf"]): categories.append("beach")
        if any(w in q for w in ["french", "heritage", "history", "fort", "architecture"]): categories.append("heritage")
        if any(w in q for w in ["ashram", "temple", "spiritual", "meditation", "quiet", "peace"]): categories.append("spiritual")
        if any(w in q for w in ["cafe", "coffee", "crepe", "bakery"]): categories.append("cafe")
        if any(w in q for w in ["food", "dining", "veg", "jain", "south indian", "halal"]): categories.append("dining")

        budget = "moderate"
        if any(w in q for w in ["cheap", "low budget", "budget", "affordable"]): budget = "budget"
        elif any(w in q for w in ["luxury", "expensive", "fine dining", "resort"]): budget = "luxury"

        belief = "secular"
        if any(w in q for w in ["temple", "hindu", "ganesha", "shiva"]): belief = "hindu"
        elif any(w in q for w in ["ashram", "auroville", "matrimandir", "meditate"]): belief = "interfaith_spiritual"
        elif any(w in q for w in ["church", "cathedral", "catholic", "basilica"]): belief = "christian_catholic"
        elif any(w in q for w in ["jain", "no onion"]): belief = "jain"

        return {
            "categories": categories or ["heritage", "beach"],
            "budget_tier": budget,
            "belief_affiliation": belief,
            "pace": "relaxed" if "relax" in q or "quiet" in q else "balanced",
            "crowd_tolerance": "low" if "quiet" in q or "peaceful" in q else "medium",
            "duration_days": 2 if "2" in q or "weekend" in q else 1,
            "niche_interests": [w for w in ["beach", "cafe", "temple", "heritage", "walk", "sunset", "photo", "meditation"] if w in q]
        }

    def _check_feasibility_warnings(self, query_text: str, city_name: str) -> tuple[bool, Optional[str]]:
        q = query_text.lower()
        
        # 1. Snow / Skiing check
        if "snow" in q or "ski" in q or "skiing" in q:
            return True, f"Clarity Notice: Snow skiing is not possible in coastal {city_name}. We have customized your itinerary to feature scenic coastal beaches, ocean walks, and seaside cafes instead."

        # 2. Himalayan / mountain lake check
        if ("himalayan" in q or "himalaya" in q) and ("lake" in q or "scuba" in q or "chennai" in q or "pondicherry" in q):
            return True, f"Clarity Notice: Himalayan lakes are located in the far north of India. For coastal {city_name}, we have substituted premier coastal shores, marina walks, and local watersports."

        # 3. Foreign landmarks (Paris / Eiffel Tower / Pyramids)
        if "eiffel" in q or "paris" in q or "pyramid" in q or "taj mahal" in q:
            return True, f"Clarity Notice: The requested foreign or distant landmark (e.g., Eiffel Tower / Paris) is outside {city_name}'s geographical boundaries. We have curated authentic French Quarter colonial architecture and seaside heritage walks instead."

        return False, None

    def generate_rag_itinerary(
        self,
        query_text: str,
        retrieved_places: List[Place],
        user_age: AgeGroupEnum,
        user_diet: DietaryOptionEnum,
        duration_days: int = 2,
        city_name: str = "Pondicherry",
        existing_days: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Uses Gemini API with Real-time Feasibility & Ground-Truth Context.
        Strictly prevents duplicates and hallucinated places.
        """
        has_warning, warning_msg = self._check_feasibility_warnings(query_text, city_name)

        places_summary = []
        for p in retrieved_places[:10]:
            belief = getattr(p, 'belief_affiliation', 'secular')
            etiquette = getattr(p, 'etiquette_rules', {})
            etiquette_str = f"Dress: {getattr(etiquette, 'dress_code', 'Casual')}, Footwear: {getattr(etiquette, 'footwear', 'Allowed')}"
            
            places_summary.append({
                "name": p.name,
                "category": p.category.value,
                "sub_category": p.sub_category,
                "belief_affiliation": str(belief),
                "etiquette": etiquette_str,
                "dietary_options": [d.value for d in p.dietary_options],
                "cost_inr": p.estimated_cost_inr,
                "duration_mins": p.duration_minutes,
                "best_time": p.best_time_to_visit,
                "highlights": p.highlights,
                "description": p.description[:140]
            })

        q_lower = query_text.lower()
        is_day2_refinement = "day 2" in q_lower or "day2" in q_lower

        age_val = user_age.value if hasattr(user_age, 'value') else str(user_age)
        diet_val = user_diet.value if hasattr(user_diet, 'value') else str(user_diet)

        if self.api_key and len(self.api_key) > 5:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={self.api_key}"
            
            existing_days_context = ""
            if existing_days and is_day2_refinement:
                existing_days_context = f"""
                CRITICAL IMMUTABILITY RULE:
                The user is specifically refining DAY 2.
                You MUST keep Day 1 EXACTLY identical to the existing Day 1 below:
                DAY 1 (IMMUTABLE): {json.dumps(existing_days[0])}
                Only modify Day 2 to fulfill: "{query_text}".
                """

            prompt = f"""
            You are Voyantra's AI Travel Decision Engine.
            Synthesize a DYNAMIC, REAL-TIME {duration_days}-day travel itinerary for {city_name}.

            USER REQUEST: "{query_text}"
            USER PROFILE: Age Group: {age_val}, Dietary Preference: {diet_val}

            AVAILABLE REAL DESTINATIONS IN {city_name.upper()} (Use ONLY these exact place names as ground truth):
            {json.dumps(places_summary, indent=2)}

            {existing_days_context}

            DYNAMIC DECISION INSTRUCTIONS:
            1. READ THE PROMPT INTENT CAREFULLY:
               - If the prompt asks for "Strict Jain / Pure Veg breakfast", place the verified Pure Veg restaurant (e.g. Hotel Surguru Pure Veg) in the Morning slot!
               - If the prompt asks for "ancient Ganesha temple", place the temple (e.g. Manakula Vinayagar Temple) in the Morning/Afternoon slot!
               - If the prompt asks for "French Quarter heritage walk", place White Town in the Evening/Afternoon slot!
               - DO NOT schedule the same place twice across days.
               - DO NOT hallucinate places outside the provided catalog.

            2. FEASIBILITY AUDIT:
               - If something requested is impossible in {city_name}, set "has_unavailability_warning": true and explain in "unavailability_notice".

            Return ONLY raw valid JSON matching this exact structure:
            {{
                "itinerary_title": "Custom Real-Time Title for Query",
                "feasibility_status": "100% Feasible" | "Adjusted for Location Realities",
                "has_unavailability_warning": boolean,
                "unavailability_notice": "Clear explanation or null",
                "summary": "Custom 2-sentence context summary.",
                "days": [
                    {{
                        "day_number": 1,
                        "theme": "Day 1 Theme",
                        "morning": {{ "place_name": "...", "activity_note": "...", "est_time": "8:30 AM - 11:00 AM" }},
                        "afternoon": {{ "place_name": "...", "activity_note": "...", "est_time": "12:00 PM - 3:00 PM" }},
                        "evening": {{ "place_name": "...", "activity_note": "...", "est_time": "4:30 PM - 7:30 PM" }}
                    }}
                ],
                "total_estimated_budget_inr": 800,
                "belief_and_etiquette_advisory": "Specific dress code, footwear, or decorum rules for this itinerary",
                "travel_tips": ["Tip 1", "Tip 2"]
            }}
            Do not wrap in ```json markdown codeblock. Output valid JSON only.
            """

            try:
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "temperature": 0.2,
                        "maxOutputTokens": 2048
                    }
                }
                res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=35)
                if res.ok:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text_resp = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        clean_text = text_resp.replace("```json", "").replace("```", "").strip()
                        parsed = json.loads(clean_text)
                        
                        # Apply deterministic reality warning override if needed
                        if has_warning:
                            parsed["has_unavailability_warning"] = True
                            parsed["unavailability_notice"] = warning_msg
                            parsed["feasibility_status"] = "Adjusted for Location Realities"

                        # Preserve Day 1 if Day 2 refinement requested
                        if existing_days and is_day2_refinement and len(existing_days) > 0 and len(parsed.get("days", [])) > 0:
                            parsed["days"][0] = existing_days[0]

                        return parsed
                else:
                    print(f"[GeminiService] Gemini API call returned status {res.status_code}: {res.text[:200]}")
            except Exception as e:
                print(f"[GeminiService] Error calling Gemini API for decision itinerary: {e}")

        # Dynamic Fallback Engine
        used_places = set()

        def pick_next(pred):
            for p in retrieved_places:
                if p.name not in used_places and pred(p):
                    used_places.add(p.name)
                    return p.name
            # Fallback to any unused
            for p in retrieved_places:
                if p.name not in used_places:
                    used_places.add(p.name)
                    return p.name
            return retrieved_places[0].name if retrieved_places else "Scenic Attraction"

        # Food preference mapping
        if "breakfast" in q_lower or "jain" in q_lower or "cafe" in q_lower or "food" in q_lower:
            morning_place = pick_next(lambda p: p.category in [CategoryEnum.DINING, CategoryEnum.CAFE])
            afternoon_place = pick_next(lambda p: p.category in [CategoryEnum.SPIRITUAL, CategoryEnum.HERITAGE])
            evening_place = pick_next(lambda p: p.category in [CategoryEnum.BEACH, CategoryEnum.HERITAGE])
        else:
            morning_place = pick_next(lambda p: p.category in [CategoryEnum.HERITAGE, CategoryEnum.BEACH])
            afternoon_place = pick_next(lambda p: p.category in [CategoryEnum.SPIRITUAL, CategoryEnum.CULTURE, CategoryEnum.DINING])
            evening_place = pick_next(lambda p: p.category in [CategoryEnum.BEACH, CategoryEnum.CAFE])

        total_cost = sum(p.estimated_cost_inr for p in retrieved_places[:5])

        day1_obj = {
            "day_number": 1,
            "theme": f"Tailored {city_name} Exploration",
            "morning": {
                "place_name": morning_place,
                "activity_note": f"Enjoy early morning visit and local experience at {morning_place}.",
                "est_time": "8:30 AM - 11:00 AM"
            },
            "afternoon": {
                "place_name": afternoon_place,
                "activity_note": f"Mid-day exploration and cultural highlights at {afternoon_place}.",
                "est_time": "12:30 PM - 3:30 PM"
            },
            "evening": {
                "place_name": evening_place,
                "activity_note": f"Evening sunset stroll and relaxation at {evening_place}.",
                "est_time": "5:00 PM - 8:00 PM"
            }
        }

        # If existing_days passed and refining Day 2, lock Day 1
        if existing_days and is_day2_refinement and len(existing_days) > 0:
            day1_obj = existing_days[0]
            # Add Day 1 places to used_places to prevent duplicate scheduling in Day 2
            for slot in ["morning", "afternoon", "evening"]:
                if slot in day1_obj and "place_name" in day1_obj[slot]:
                    used_places.add(day1_obj[slot]["place_name"])

        days = [day1_obj]

        if duration_days > 1:
            is_relaxed = "relaxed" in q_lower or "light" in q_lower
            day2_p1 = pick_next(lambda p: p.category in [CategoryEnum.SPIRITUAL, CategoryEnum.NATURE])
            day2_p2 = pick_next(lambda p: p.category in [CategoryEnum.HERITAGE, CategoryEnum.CAFE])
            day2_p3 = pick_next(lambda p: p.category in [CategoryEnum.BEACH, CategoryEnum.NATURE])

            days.append({
                "day_number": 2,
                "theme": "Relaxed Coastal & Serene Day" if is_relaxed else "Spiritual Harmony & Scenic Coast",
                "morning": {
                    "place_name": day2_p1,
                    "activity_note": f"{'Gentle leisure morning' if is_relaxed else 'Morning exploration'} at {day2_p1}.",
                    "est_time": "9:30 AM - 11:30 AM" if is_relaxed else "9:00 AM - 11:30 AM"
                },
                "afternoon": {
                    "place_name": day2_p2 if not is_relaxed else "Free Leisure & French Cafe Rest",
                    "activity_note": f"{'Unrushed downtime and quiet shade' if is_relaxed else 'Afternoon sightseeing'} at {day2_p2}.",
                    "est_time": "1:30 PM - 3:30 PM" if is_relaxed else "1:00 PM - 3:30 PM"
                },
                "evening": {
                    "place_name": day2_p3,
                    "activity_note": f"Tranquil sunset ocean breeze at {day2_p3}.",
                    "est_time": "5:00 PM - 7:30 PM"
                }
            })

        return {
            "itinerary_title": f"Custom Plan: {query_text[:35]}...",
            "feasibility_status": "Adjusted for Location Realities" if has_warning else "100% Feasible",
            "has_unavailability_warning": has_warning,
            "unavailability_notice": warning_msg,
            "summary": f"Real-time custom plan generated for {city_name} matching your profile.",
            "days": days,
            "total_estimated_budget_inr": total_cost,
            "belief_and_etiquette_advisory": "Observe local dress code and footwear decorum at spiritual & heritage sites.",
            "travel_tips": [
                "Observe local decorum and timings at sacred and heritage sites.",
                "Check weather and crowd indicators before evening ocean walks."
            ]
        }

gemini_service = GeminiService()
