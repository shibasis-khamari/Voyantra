"""
Voyantra 2.0 Unified Conversation Orchestrator
Coordinates Language, Context, Memory, Destination Policy, Travel Discovery,
and Itinerary Generation across English, Hindi, and Tamil.
"""
import os
import re
import json
import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

from ...core.config import settings
from ...core.database import db_manager
from ...schemas.chat import (
    ChatTurnRequest, ChatTurnResponse, ChatMessage,
    PlaceCardData, HotelCardData, RestaurantCardData, ItineraryData
)
from .destination_service import destination_service
from .language_service import language_service
from .context_service import context_service
from .memory_service import memory_service
from .discovery_service import discovery_service
from .itinerary_service import itinerary_service

logger = logging.getLogger(__name__)

class ConversationOrchestrator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY or ""

    def classify_intent(self, message: str, current_itinerary: Optional[Dict[str, Any]] = None) -> str:
        """
        Classifies user intent without restrictive gating:
        - general_qa
        - place_discovery
        - hotel_discovery
        - restaurant_discovery
        - itinerary_planning
        - itinerary_edit
        """
        msg = (message or "").lower().strip()

        # 1. General Knowledge Explanations & Comparisons (Direct QA)
        if any(w in msg for w in [
            "what is the difference", "difference between", "why is ", "explain ", 
            "history of ", "what does ", "how does ", "meaning of "
        ]):
            return "general_qa"

        # 2. Itinerary Edit (if an active itinerary exists and user requests modification)
        if current_itinerary and any(w in msg for w in [
            "add ", "remove ", "replace ", "make it more relaxed", "change day", "swap", "delete"
        ]):
            return "itinerary_edit"

        # 2. Explicit Itinerary Planning Request (MUST clearly ask for planning)
        planning_triggers = [
            r"\bplan a\b", r"\bplan my\b", r"\bmake an itinerary\b", r"\bcreate an itinerary\b",
            r"\bgenerate itinerary\b", r"\bday trip\b", r"\bweekend trip\b", r"\b\d+\s*-?\s*days?\s*trip\b",
            r"\b\d+\s*-?\s*days?\s*itinerary\b", r"\bplan for \d+ days\b", r"\btravel schedule\b"
        ]
        if any(re.search(p, msg) for p in planning_triggers):
            return "itinerary_planning"

        # 3. Hotel Discovery
        if any(w in msg for w in ["hotel", "resort", "stay", "accommodation", "room", "lodge"]):
            return "hotel_discovery"

        # 4. Restaurant Discovery
        if any(w in msg for w in ["restaurant", "cafe", "dining", "food", "eat", "breakfast", "lunch", "dinner", "jain food", "veg food"]):
            return "restaurant_discovery"

        # 5. Place Discovery
        if any(w in msg for w in ["tell me about", "places to visit", "tourist spot", "attractions", "sightseeing", "beach", "temple", "museum"]):
            return "place_discovery"

        # 6. Default to General Conversational Q&A
        return "general_qa"

    def process_turn(
        self,
        req: ChatTurnRequest,
        user_id: Optional[str] = "demo_user"
    ) -> ChatTurnResponse:
        """
        Unified conversation pipeline adhering to Section 10 of the functional specification.
        """
        # 1. Resolve Conversation ID
        conv_id = req.conversation_id or f"conv-{uuid4().hex[:12]}"

        # 2. Language Identification (English, Hindi, Tamil)
        detected_lang = language_service.detect_language(req.message)
        final_lang = language_service.normalize_language_code(req.language or detected_lang)

        # 3. Load Short-Term Context & Long-Term Consented Memory
        conv_history = self._load_recent_messages(conv_id)
        resolved_context = context_service.resolve_references(req.message, conv_history)
        effective_message = resolved_context.get("augmented_query", req.message)

        user_memory = memory_service.get_user_memory(user_id)
        user_pref = req.user_preferences or {}
        if user_memory.is_memory_enabled:
            # Merge consented memory profile
            if not user_pref.get("budget_tier"): user_pref["budget_tier"] = user_memory.budget_tier
            if not user_pref.get("dietary_preference"): user_pref["dietary_preference"] = user_memory.dietary_preference
            if not user_pref.get("travel_pace"): user_pref["travel_pace"] = user_memory.travel_pace

        # 4. Intent Classification
        intent = self.classify_intent(req.message, req.current_itinerary)

        # 5. Geographic Scope Detection
        city_slug, city_name = destination_service.detect_destination(effective_message)

        # State Containers
        reply_text = ""
        places_data: List[PlaceCardData] = []
        hotels_data: List[HotelCardData] = []
        restaurants_data: List[RestaurantCardData] = []
        itinerary_data: Optional[ItineraryData] = None
        followups: List[str] = []
        source = "gemini"

        # -------------------------------------------------------------------
        # INTENT EXECUTION & TOOL ORCHESTRATION
        # -------------------------------------------------------------------

        if intent == "general_qa":
            # Answer directly without itinerary questionnaires
            reply_text = self._generate_general_answer(effective_message, final_lang)
            followups = [
                "Tell me more about this",
                "What are famous places to see in Pondicherry?",
                "What can I do in Chennai this weekend?"
            ]

        elif intent == "place_discovery":
            places_data = discovery_service.search_places(effective_message, city_slug)
            reply_text = self._generate_discovery_reply(
                effective_message, "place", places_data, final_lang, city_name
            )
            followups = [
                "How do I reach here?",
                "Is it suitable for children and seniors?",
                "Suggest good cafes nearby"
            ]

        elif intent == "hotel_discovery":
            budget_val = user_pref.get("budget_tier", "moderate")
            hotels_data = discovery_service.search_hotels(
                query=effective_message,
                city_id=city_slug or "pondicherry",
                budget_tier=budget_val
            )
            reply_text = self._generate_discovery_reply(
                effective_message, "hotel", hotels_data, final_lang, city_name
            )
            followups = [
                "Which area is best to stay in Pondicherry?",
                "Show beachfront boutique hotels",
                "Are vegetarian options available?"
            ]

        elif intent == "restaurant_discovery":
            dietary_val = user_pref.get("dietary_preference", "all")
            restaurants_data = discovery_service.search_restaurants(
                query=effective_message,
                city_id=city_slug or "pondicherry",
                dietary=dietary_val
            )
            reply_text = self._generate_discovery_reply(
                effective_message, "restaurant", restaurants_data, final_lang, city_name
            )
            followups = [
                "Find pure vegetarian South Indian spots",
                "Best French cafes in White Town",
                "Places with outdoor terrace seating"
            ]

        elif intent == "itinerary_planning":
            # Check geographic policy
            # If user explicitly asked for an unsupported destination outside Pondy & Chennai
            is_unsupported = False
            unsupported_target = ""
            for word in ["tokyo", "paris", "london", "dubai", "bali", "new york", "mumbai", "delhi"]:
                if word in req.message.lower() and not city_slug:
                    is_unsupported = True
                    unsupported_target = word
                    break

            if is_unsupported:
                reply_text = destination_service.get_unsupported_destination_message(unsupported_target, final_lang)
                followups = [
                    "Plan a 2-day trip to Pondicherry",
                    "Plan a weekend in Chennai",
                    "Suggest places across Pondicherry & Chennai"
                ]
            else:
                # Generate multi-alternative itinerary
                itinerary_data = itinerary_service.generate_itinerary_alternatives(
                    city_slug=city_slug or "both",
                    duration_days=req.duration_days or 2,
                    pace=user_pref.get("travel_pace", "relaxed"),
                    budget=user_pref.get("budget_tier", "moderate"),
                    dietary=user_pref.get("dietary_preference", "all")
                )
                city_title = city_name or "Pondicherry & Chennai"
                if final_lang == "hi":
                    reply_text = (
                        f"मैंने आपके लिए **{city_title}** का एक संतुलित {req.duration_days or 2}-दिवसीय यात्रा कार्यक्रम तैयार किया है। "
                        f"दाहिनी ओर आप 3 अलग-अलग विकल्प (आरामदायक, सांस्कृतिक धरोहर, एवं साहसिक गतिविधि) देख सकते हैं। "
                        f"आप बातचीत में कोई भी बदलाव करने के लिए कह सकते हैं!"
                    )
                elif final_lang == "ta":
                    reply_text = (
                        f"**{city_title}** க்கான {req.duration_days or 2} நாள் தனிப்பயனாக்கப்பட்ட பயணத்திட்டத்தை உருவாக்கியுள்ளேன். "
                        f"வலதுபுறத்தில் நீங்கள் அமைதியான, கலாச்சார அல்லது சாகச மாற்றுத் திட்டங்களை ஆராயலாம். "
                        f"இதில் ஏதேனும் மாற்றங்கள் செய்ய விரும்பினால் என்னிடம் தாராளமாக கேட்கலாம்!"
                    )
                else:
                    reply_text = (
                        f"I have created a personalized {req.duration_days or 2}-day itinerary for **{city_title}**. "
                        f"On the right pane, you can review 3 distinct alternatives (Relaxed Coastal, Cultural Heritage, and Activity-Focused). "
                        f"Feel free to ask me to modify any day or stop!"
                    )
                followups = [
                    "Make Day 1 more relaxed",
                    "Add Kapaleeshwarar Temple to Day 2",
                    "Show budget breakdown"
                ]

        elif intent == "itinerary_edit":
            if req.current_itinerary:
                itinerary_data = itinerary_service.modify_itinerary_conversationally(
                    req.current_itinerary,
                    req.message
                )
                if final_lang == "hi":
                    reply_text = "मैंने आपके अनुरोध के अनुसार यात्रा कार्यक्रम को अद्यतन (update) कर दिया है। आप दाहिनी ओर नए बदलाव देख सकते हैं।"
                elif final_lang == "ta":
                    reply_text = "உங்கள் விருப்பப்படி பயணத்திட்டத்தில் மாற்றங்களை செய்துள்ளேன். வலதுபுறத்தில் புதுப்பிக்கப்பட்ட விவரங்களைக் காணலாம்."
                else:
                    reply_text = "I have updated your active itinerary based on your request. Unaffected stops have been preserved, and you can see the updated schedule on the right."
            else:
                reply_text = "Please generate or select an itinerary first so I can modify it for you."
            followups = [
                "View on Interactive Map",
                "Save all stops to basket",
                "Recommend a nearby lunch place"
            ]

        # 6. Save Conversation Turn to Database
        self._persist_turn(conv_id, user_id, req.message, reply_text, final_lang)

        return ChatTurnResponse(
            conversation_id=conv_id,
            reply_message=reply_text,
            language=final_lang,
            intent=intent,
            places=places_data,
            hotels=hotels_data,
            restaurants=restaurants_data,
            itinerary=itinerary_data,
            suggested_followups=followups,
            source=source
        )

    # -----------------------------------------------------------------------
    # LLM & Conversation Generation Helpers
    # -----------------------------------------------------------------------

    def _generate_general_answer(self, query: str, lang: str) -> str:
        """Generates direct conversational answer for general knowledge inquiries."""
        lang_prompt = language_service.get_system_language_instruction(lang)
        
        if self.api_key and len(self.api_key) > 5:
            model_name = getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}
            
            prompt = f"""
            You are Voyantra AI — a polite, articulate, culturally grounded travel intelligence assistant.
            The user is asking a general question:
            "{query}"

            {lang_prompt}

            RULES:
            - Answer the question directly, factually, and engagingly.
            - DO NOT ask for dates, budget, or force an itinerary.
            - Keep response under 3-4 concise paragraphs.
            """
            try:
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                res = requests.post(url, json=payload, headers=headers, timeout=12)
                if res.ok:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        return candidates[0]["content"]["parts"][0]["text"].strip()
            except Exception as e:
                logger.warning(f"[Orchestrator] Gemini general answer notice: {e}")

        # Deterministic Grounded Fallbacks
        q_lower = query.lower()
        if "pondicherry" in q_lower and ("famous" in q_lower or "why" in q_lower):
            if lang == "hi":
                return (
                    "**पुडुचेरी (Pondicherry)** अपने अनूठे फ्रांसीसी औपनिवेशिक विरासत, शांत समुद्र तटों और आध्यात्मिक वातावरण के लिए विश्व प्रसिद्ध है।\n\n"
                    "- **व्हाइट टाउन (White Town):** फ्रांसीसी स्थापत्य, सरसों-पीली दीवारें और बोगनवेलिया के फूलों से सजी सड़कें।\n"
                    "- **श्री अरबिंदो आश्रम और ऑरोविले (Auroville):** ध्यान और आंतरिक शांति का वैश्विक केंद्र।\n"
                    "- **प्रोमेनेड बीच (Promenade Beach):** शाम को गाड़ियों से मुक्त एक रमणीय तटीय पदयात्रा मार्ग।"
                )
            elif lang == "ta":
                return (
                    "**பாண்டிச்சேரி (Pondicherry)** அதன் தனித்துவமான பிரெஞ்சு பாரம்பரியம், அமைதியான கடற்கரைகள் மற்றும் ஆன்மீக மையங்களுக்காக உலகப் புகழ் பெற்றது.\n\n"
                    "- **பிரெஞ்சு குவார்ட்டர் (White Town):** வரலாற்று சிறப்புமிக்க காலனித்துவ கட்டிடக்கலை மற்றும் கலை நயமிக்க கஃபேக்கள்.\n"
                    "- **அரவிந்தர் ஆசிரமம் & ஆரோவில் (Auroville):** அமைதி மற்றும் தியானத்திற்கான உலகளாவிய மையம்.\n"
                    "- **ப்ரோமனேட் கடற்கரை:** மாலையில் வாகன நடமாட்டமின்றி கடற்காற்றை அனுபவிக்கும் நடைபாதை."
                )
            return (
                "**Pondicherry** is world-renowned for its distinct blend of French colonial heritage, tranquil beaches, and spiritual sanctuaries:\n\n"
                "- **White Town (French Quarter):** Preserved 18th-century colonial villas with mustard-yellow walls, arched gates, and chic Parisian cafes.\n"
                "- **Sri Aurobindo Ashram & Auroville:** Global hubs for meditation, reflection, and human unity around the iconic Matrimandir.\n"
                "- **Promenade Beach:** A scenic 1.5-kilometer beachfront walkway closed to motor vehicles each evening for serene ocean walks."
            )

        if "architecture" in q_lower:
            return (
                "French colonial architecture in Pondicherry features distinctive European neoclassicism adapted to the tropical Coromandel coast:\n\n"
                "- **Colonnaded Porticos & Arched Windows:** Designed with wooden shutters (louvered jalousies) that maximize sea breeze ventilation.\n"
                "- **Internal Courtyards:** Private leafy courtyards keeping interiors cool in summer heat.\n"
                "- **Contrasting Towns:** White Town (French Quarter) with gridiron streets and pastel villas stands opposite Black Town (Tamil Quarter) with verandas (thinnai) and carved wooden pillars."
            )

        if "lagoon" in q_lower:
            return (
                "A **beach** is an open shore of sand or pebbles along the ocean directly exposed to incoming waves. In contrast, a **lagoon** is a shallow, tranquil body of water separated from the deeper sea by a barrier island, coral reef, or sandbar (such as Chunnambar lagoon near Paradise Beach in Pondicherry)."
            )

        if "mahabalipuram" in q_lower:
            return (
                "**Mahabalipuram (Mamallapuram)**, located on the coast between Chennai and Pondicherry, was the historic port city of the 7th-century Pallava dynasty. It is a UNESCO World Heritage site renowned for monolithic rock-cut cave temples, the coastal Shore Temple facing Bay of Bengal waves, and the massive bas-relief *Arjuna's Penance*."
            )

        return (
            f"Here is what you should know about **{query}**:\n\n"
            "This destination offers rich regional heritage, authentic coastal hospitality, and vibrant local sights. "
            "Whether you're exploring the French boulevards of Pondicherry or the historic temples of Chennai, there is always plenty of history, local cuisine, and seaside tranquility to discover."
        )

    def _generate_discovery_reply(self, query: str, item_type: str, items: List[Any], lang: str, city_name: Optional[str]) -> str:
        """Generates contextual conversational response for discovered items."""
        city_tag = city_name or "Pondicherry & Chennai"
        count = len(items)
        if count == 0:
            return f"I couldn't find verified {item_type} records matching your criteria in {city_tag}. Would you like me to broaden the search?"

        names = [item.name for item in items]
        names_str = ", ".join(f"**{n}**" for n in names)

        if lang == "hi":
            return f"मुझे {city_tag} में आपके लिए {count} बेहतरीन स्थल मिले हैं: {names_str}। आप नीचे इनके विवरण देख सकते हैं!"
        elif lang == "ta":
            return f"{city_tag} பகுதியில் உங்களுக்காக {count} பரிந்துரைகள் கிடைத்துள்ளன: {names_str}. கூடுதல் விவரங்களை கீழே காணலாம்!"
        return f"Here are {count} verified {item_type} recommendations in **{city_tag}**: {names_str}. You can view details or add them directly to your trip below."

    def _load_recent_messages(self, conv_id: str) -> List[Dict[str, Any]]:
        """Loads recent conversation turns from MongoDB or memory cache."""
        col = db_manager.get_collection("messages")
        if col is not None:
            docs = list(col.find({"conversation_id": conv_id}).sort("timestamp", 1).limit(6))
            return [{"role": d.get("role"), "content": d.get("content")} for d in docs]
        return []

    def _persist_turn(self, conv_id: str, user_id: str, user_text: str, assistant_text: str, lang: str):
        """Persists user and assistant messages in MongoDB."""
        now = datetime.now().isoformat()
        conv_col = db_manager.get_collection("conversations")
        msg_col = db_manager.get_collection("messages")

        if conv_col is not None and msg_col is not None:
            # Update or create conversation metadata
            conv_col.update_one(
                {"id": conv_id},
                {
                    "$set": {
                        "id": conv_id,
                        "user_id": user_id,
                        "title": user_text[:35] + ("..." if len(user_text) > 35 else ""),
                        "language": lang,
                        "updated_at": now
                    },
                    "$setOnInsert": {
                        "created_at": now
                    }
                },
                upsert=True
            )
            # Insert turns
            msg_col.insert_many([
                {"conversation_id": conv_id, "role": "user", "content": user_text, "language": lang, "timestamp": now},
                {"conversation_id": conv_id, "role": "assistant", "content": assistant_text, "language": lang, "timestamp": now}
            ])

orchestrator = ConversationOrchestrator()
