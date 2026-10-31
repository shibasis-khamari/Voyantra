"""
Automated Test Suite for Voyantra 2.0 Conversational AI Architecture
Validates:
1. Destination Policy & Geographic Scope Service
2. Multilingual Service (English, Hindi, Tamil)
3. Context Service & Pronoun Reference Resolution
4. Consented Memory Service & Sensitive Preferences
5. Discovery Service (Places, Hotels, Restaurants)
6. Itinerary Service (Alternatives & Delta Editing)
7. Unified Orchestrator & General Q&A (No forced itinerary)
8. Unified FastAPI Endpoints (/api/v1/chat/...)
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.conversation.destination_service import destination_service
from backend.app.services.conversation.language_service import language_service
from backend.app.services.conversation.context_service import context_service
from backend.app.services.conversation.memory_service import memory_service
from backend.app.services.conversation.discovery_service import discovery_service
from backend.app.services.conversation.itinerary_service import itinerary_service
from backend.app.services.conversation.orchestrator import orchestrator
from backend.app.schemas.chat import ChatTurnRequest

client = TestClient(app)

# ---------------------------------------------------------------------------
# 1. Geographic Scope & Destination Service
# ---------------------------------------------------------------------------
def test_destination_detection():
    # Pondicherry
    slug, name = destination_service.detect_destination("What can I do in Pondicherry?")
    assert slug == "pondicherry"
    assert name == "Pondicherry"

    # Chennai
    slug, name = destination_service.detect_destination("Tell me about temples in Chennai")
    assert slug == "chennai"
    assert name == "Chennai"

    # Both
    slug, name = destination_service.detect_destination("Suggest a roadtrip across Pondicherry and Chennai")
    assert slug == "both"
    assert name == "Pondicherry & Chennai"

def test_unsupported_destination_policy():
    assert destination_service.supports_full_planning("pondicherry") is True
    assert destination_service.supports_full_planning("chennai") is True
    assert destination_service.supports_full_planning("both") is True
    assert destination_service.supports_full_planning("tokyo") is False

    msg_en = destination_service.get_unsupported_destination_message("Tokyo", "en")
    assert "Tokyo" in msg_en
    assert "Pondicherry" in msg_en and "Chennai" in msg_en

    msg_hi = destination_service.get_unsupported_destination_message("Tokyo", "hi")
    assert "पुडुचेरी" in msg_hi and "चेन्नई" in msg_hi

    msg_ta = destination_service.get_unsupported_destination_message("Tokyo", "ta")
    assert "பாண்டிச்சேரி" in msg_ta and "சென்னை" in msg_ta

# ---------------------------------------------------------------------------
# 2. Multilingual Service (English, Hindi, Tamil)
# ---------------------------------------------------------------------------
def test_language_detection():
    # English
    assert language_service.detect_language("Tell me about the best beach") == "en"

    # Hindi
    assert language_service.detect_language("पुडुचेरी के सबसे अच्छे समुद्र तट कौन से हैं?") == "hi"

    # Tamil
    assert language_service.detect_language("பாண்டிச்சேரியில் பார்க்க வேண்டிய இடங்கள் என்ன?") == "ta"

def test_language_normalization():
    assert language_service.normalize_language_code("HINDI") == "hi"
    assert language_service.normalize_language_code("ta") == "ta"
    assert language_service.normalize_language_code("invalid", default="en") == "en"

# ---------------------------------------------------------------------------
# 3. Context & Reference Resolution
# ---------------------------------------------------------------------------
def test_context_reference_resolution():
    history = [
        {"role": "user", "content": "Tell me about Promenade Beach"},
        {"role": "assistant", "content": "Here is information about **Promenade Beach (Rock Beach)**."}
    ]
    res = context_service.resolve_references("Is it good for children?", history)
    assert res["has_reference"] is True
    assert res["resolved_entity"] == "Promenade Beach (Rock Beach)"
    assert "Promenade Beach" in res["augmented_query"]

def test_no_false_reference_resolution():
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "How can I help you today?"}
    ]
    res = context_service.resolve_references("What is French colonial architecture?", history)
    assert res["has_reference"] is False
    assert res["resolved_entity"] is None

# ---------------------------------------------------------------------------
# 4. Consented Memory Service
# ---------------------------------------------------------------------------
def test_memory_preferences_and_consent():
    user_id = "test_traveler_01"
    memory_service.clear_user_memory(user_id)

    # Initial profile
    profile = memory_service.get_user_memory(user_id)
    assert profile.is_memory_enabled is True
    assert profile.sensitive_cultural_opt_in is False

    # Attempt to save sensitive preference without explicit opt-in
    updated = memory_service.update_user_memory(user_id, {
        "budget_tier": "luxury",
        "sensitive_cultural_preferences": "Hindu temple puja daily"
    })
    # Sensitive preference must NOT be saved without opt-in flag
    assert updated.budget_tier == "luxury"
    assert updated.sensitive_cultural_preferences is None

    # Save with explicit opt-in
    updated_with_consent = memory_service.update_user_memory(user_id, {
        "sensitive_cultural_opt_in": True,
        "sensitive_cultural_preferences": "Hindu temple puja daily"
    })
    assert updated_with_consent.sensitive_cultural_preferences == "Hindu temple puja daily"

    # Clear memory
    memory_service.clear_user_memory(user_id)
    cleared = memory_service.get_user_memory(user_id)
    assert cleared.budget_tier == "moderate"  # Reset to default

# ---------------------------------------------------------------------------
# 5. Travel Discovery Service
# ---------------------------------------------------------------------------
def test_places_discovery():
    places = discovery_service.search_places("beach", city_id="pondicherry")
    assert len(places) > 0
    assert any("Beach" in p.name for p in places)

def test_hotels_discovery_both_cities():
    pondy_hotels = discovery_service.search_hotels(city_id="pondicherry")
    assert len(pondy_hotels) > 0
    assert any(h.city_id == "pondicherry" for h in pondy_hotels)

    chennai_hotels = discovery_service.search_hotels(city_id="chennai")
    assert len(chennai_hotels) > 0
    assert any(h.city_id == "chennai" for h in chennai_hotels)

def test_restaurants_discovery_dietary():
    jain_places = discovery_service.search_restaurants(dietary="pure_veg_jain")
    assert len(jain_places) > 0

# ---------------------------------------------------------------------------
# 6. Itinerary Service (Alternatives & Conversational Editing)
# ---------------------------------------------------------------------------
def test_itinerary_alternatives():
    itin = itinerary_service.generate_itinerary_alternatives(
        city_slug="pondicherry",
        duration_days=2
    )
    assert len(itin.alternatives) == 3
    assert itin.alternatives[0].id == "alt-relaxed"
    assert itin.alternatives[1].id == "alt-cultural"
    assert itin.alternatives[2].id == "alt-active"
    assert len(itin.days) == 2

def test_conversational_itinerary_editing():
    itin = itinerary_service.generate_itinerary_alternatives(
        city_slug="pondicherry",
        duration_days=2
    )
    itin_dict = itin.model_dump()
    modified = itinerary_service.modify_itinerary_conversationally(
        itin_dict,
        "Add Serenity Beach to Day 1 afternoon"
    )
    assert modified.days[0].afternoon is not None
    assert "Serenity Beach" in modified.days[0].afternoon.place_name

# ---------------------------------------------------------------------------
# 7. Orchestrator Intent & General Q&A (No forced itinerary)
# ---------------------------------------------------------------------------
def test_general_qa_intent_no_itinerary():
    # General question must NOT trigger itinerary planning
    intent = orchestrator.classify_intent("Why is Pondicherry famous?")
    assert intent == "general_qa"

    turn_req = ChatTurnRequest(message="Why is Pondicherry famous?")
    res = orchestrator.process_turn(turn_req)
    assert res.intent == "general_qa"
    assert res.itinerary is None  # Must NOT force an itinerary
    assert "Pondicherry" in res.reply_message

def test_planning_intent_triggers_itinerary():
    intent = orchestrator.classify_intent("Plan a 2-day trip to Pondicherry and Chennai")
    assert intent == "itinerary_planning"

    turn_req = ChatTurnRequest(message="Plan a 2-day trip to Pondicherry and Chennai", duration_days=2)
    res = orchestrator.process_turn(turn_req)
    assert res.intent == "itinerary_planning"
    assert res.itinerary is not None
    assert len(res.itinerary.alternatives) == 3

def test_unsupported_itinerary_destination():
    turn_req = ChatTurnRequest(message="Plan a 3-day itinerary for Tokyo", duration_days=3)
    res = orchestrator.process_turn(turn_req)
    assert res.itinerary is None
    assert "Tokyo" in res.reply_message
    assert "Pondicherry" in res.reply_message

# ---------------------------------------------------------------------------
# 8. Unified FastAPI Endpoints
# ---------------------------------------------------------------------------
def test_chat_message_endpoint():
    payload = {
        "message": "What is the difference between a beach and a lagoon?",
        "language": "en"
    }
    res = client.post("/api/v1/chat/message", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "conversation_id" in data
    assert data["intent"] == "general_qa"
    assert data["itinerary"] is None
    assert "beach" in data["reply_message"].lower()

def test_conversations_listing_and_deletion():
    # Send a message to generate a conversation
    payload = {"message": "Tell me about White Town Pondicherry"}
    post_res = client.post("/api/v1/chat/message", json=payload)
    assert post_res.status_code == 200
    conv_id = post_res.json()["conversation_id"]

    # List conversations
    list_res = client.get("/api/v1/chat/conversations")
    assert list_res.status_code == 200

    # Get conversation turns
    get_res = client.get(f"/api/v1/chat/conversations/{conv_id}")
    assert get_res.status_code == 200

    # Delete conversation
    del_res = client.delete(f"/api/v1/chat/conversations/{conv_id}")
    assert del_res.status_code == 200

def test_memory_endpoints():
    get_res = client.get("/api/v1/chat/memory")
    assert get_res.status_code == 200

    update_payload = {"budget_tier": "luxury", "travel_pace": "relaxed"}
    put_res = client.put("/api/v1/chat/memory", json=update_payload)
    assert put_res.status_code == 200
    assert put_res.json()["budget_tier"] == "luxury"

    del_res = client.delete("/api/v1/chat/memory")
    assert del_res.status_code == 200
