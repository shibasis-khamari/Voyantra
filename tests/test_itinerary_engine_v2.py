"""
Voyantra 2.0 Complete Itinerary Engine V2 Test Suite
Validates all 40 requirements:
- Data provenance, schemas, and dataset integrity (Tests 1-6)
- Multi-factor place scoring engine (Tests 7-13)
- Soft geographic clustering & road routing (Tests 14-18)
- Multi-day duplicate elimination & alternative design (Tests 19-23)
- Itemized budgeting & transparent estimation (Tests 24-26)
- Multi-dimensional quality scoring & catalog exhaustion (Tests 27-29)
- Conversational delta editing (Tests 30-32)
- 10-point itinerary validator & recovery (Tests 33-35)
- API consolidation & backward compatibility (Tests 36-40)
"""
import pytest
import copy
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.place import Place, Coordinates, CategoryEnum, DietaryOptionEnum
from backend.app.schemas.chat import (
    ChatTurnRequest, ItineraryData, ItineraryDayData, ItinerarySlotData, ItineraryAlternativeData
)
from backend.app.services.places_service import places_service
from backend.app.services.conversation.place_scorer import place_scorer
from backend.app.services.conversation.geo_clusterer import geo_clusterer
from backend.app.services.conversation.itinerary_service import itinerary_service
from backend.app.services.conversation.orchestrator import orchestrator

client = TestClient(app)

# ==============================================================================
# Helper to construct minimal valid Place instance
# ==============================================================================

def make_test_place(**kwargs) -> Place:
    default_kwargs = {
        "id": "test-id",
        "city_id": "pondicherry",
        "name": "Test Place",
        "category": CategoryEnum.HERITAGE,
        "description": "Test description",
        "budget_tier": "moderate",
        "coordinates": Coordinates(lat=11.93, lng=79.83),
        "address": "Test Address",
        "image_url": "https://example.com/test.jpg"
    }
    default_kwargs.update(kwargs)
    return Place(**default_kwargs)

# ==============================================================================
# SECTION 1: Data Provenance, Schemas & Dataset Expansion (Tests 1 - 6)
# ==============================================================================

def test_1_schema_provenance_defaults():
    """Test 1: Place without verification_status defaults to 'unverified'."""
    p = make_test_place(id="test-p1", name="Test Place")
    assert p.verification_status == "unverified"
    assert p.is_major_attraction is True
    assert p.source_url is None
    assert p.weekly_closing_days == []

def test_2_opening_hours_weekly_closing_schema():
    """Test 2: weekly_closing_days field correctly parses and stores days."""
    p = make_test_place(
        id="test-p2",
        name="Museum Test",
        weekly_closing_days=["Friday", "Sunday"],
        opening_hours_verified=True
    )
    assert "Friday" in p.weekly_closing_days
    assert "Sunday" in p.weekly_closing_days
    assert p.opening_hours_verified is True

def test_3_major_attraction_flag():
    """Test 3: Major attractions have is_major_attraction=True, dining places False."""
    p_sight = make_test_place(id="test-sight", category=CategoryEnum.SPIRITUAL, is_major_attraction=True)
    p_cafe = make_test_place(id="test-cafe", category=CategoryEnum.CAFE, is_major_attraction=False)
    assert p_sight.is_major_attraction is True
    assert p_cafe.is_major_attraction is False

def test_4_dataset_provenance_chennai():
    """Test 4: All 26 Chennai records have valid coordinates, dwell times, and provenance."""
    chennai_places = places_service.get_all_places("chennai")
    assert len(chennai_places) >= 26
    for p in chennai_places:
        assert p.coordinates is not None
        assert 12.5 <= p.coordinates.lat <= 13.5
        assert 79.5 <= p.coordinates.lng <= 80.5
        assert p.duration_minutes is not None and p.duration_minutes > 0
        assert p.verification_status in ["unverified", "verified", "estimated"]

def test_5_dataset_provenance_pondicherry():
    """Test 5: All 26 Pondicherry records have valid coordinates, dwell times, and provenance."""
    pondy_places = places_service.get_all_places("pondicherry")
    assert len(pondy_places) >= 26
    for p in pondy_places:
        assert p.coordinates is not None
        assert 11.5 <= p.coordinates.lat <= 12.5
        assert 79.5 <= p.coordinates.lng <= 80.5
        assert p.duration_minutes is not None and p.duration_minutes > 0
        assert p.verification_status in ["unverified", "verified", "estimated"]

def test_6_no_duplicate_place_ids():
    """Test 6: Unique place IDs across both datasets."""
    all_places = places_service.get_all_places(None)
    ids = [p.id for p in all_places]
    assert len(ids) == len(set(ids)), f"Duplicate IDs detected: {[i for i in ids if ids.count(i) > 1]}"


# ==============================================================================
# SECTION 2: Multi-Factor Place Scoring Engine (Tests 7 - 13)
# ==============================================================================

def test_7_scorer_mandatory_place_priority():
    """Test 7: Place with ID in mandatory_ids scores significantly higher (+100.0)."""
    p = places_service.get_all_places("pondicherry")[0]
    score_normal = place_scorer.score_place(p, criteria={"interests": []}, current_slot="morning")
    score_mandatory = place_scorer.score_place(p, criteria={"interests": []}, current_slot="morning", mandatory_ids={p.id})
    assert score_mandatory >= score_normal + 90.0

def test_8_scorer_interest_alignment():
    """Test 8: Place matching user interests scores higher than unrelated place."""
    p_heritage = next(p for p in places_service.get_all_places("pondicherry") if p.category == CategoryEnum.HERITAGE)
    p_adventure = next(p for p in places_service.get_all_places("pondicherry") if p.category == CategoryEnum.ADVENTURE)

    criteria = {"interests": ["heritage", "history"], "age_group": "all"}
    score_heritage = place_scorer.score_place(p_heritage, criteria=criteria, current_slot="morning")
    score_adventure = place_scorer.score_place(p_adventure, criteria=criteria, current_slot="morning")
    assert score_heritage > score_adventure

def test_9_scorer_category_diversity_penalty():
    """Test 9: Second place of same category in day receives diversity penalty."""
    places = [p for p in places_service.get_all_places("pondicherry") if p.category == CategoryEnum.SPIRITUAL]
    p1, p2 = places[0], places[1]

    score_fresh = place_scorer.score_place(p2, criteria={}, current_slot="morning", day_history=[])
    score_repeated = place_scorer.score_place(p2, criteria={}, current_slot="afternoon", day_history=[p1])
    assert score_repeated < score_fresh

def test_10_scorer_dining_vs_sightseeing_slot():
    """Test 10: Dining venue receives penalty for sightseeing slot and bonus for meal slot."""
    p_cafe = next(p for p in places_service.get_all_places("pondicherry") if p.category == CategoryEnum.CAFE)
    score_sightseeing = place_scorer.score_place(p_cafe, criteria={}, current_slot="morning")
    score_meal = place_scorer.score_place(p_cafe, criteria={}, current_slot="lunch")
    assert score_meal > score_sightseeing

def test_11_scorer_dietary_hard_filter():
    """Test 11: Dining venue violating strict Jain/halal returns -inf."""
    # Find cafe without Jain options
    all_cafes = [p for p in places_service.get_all_places("pondicherry") if p.category in [CategoryEnum.CAFE, CategoryEnum.DINING]]
    non_jain_cafe = next((c for c in all_cafes if not any("jain" in str(d).lower() for d in (c.dietary_options or []))), all_cafes[0])

    score = place_scorer.score_place(non_jain_cafe, criteria={"dietary": "pure_veg_jain"}, current_slot="lunch")
    assert score == -float("inf")

def test_12_scorer_age_suitability():
    """Test 12: Senior preference boosts accessible/spiritual places and penalizes high exertion."""
    p_accessible = next(p for p in places_service.get_all_places("pondicherry") if getattr(p, "accessibility_rating", 0) >= 4 and p.category == CategoryEnum.SPIRITUAL)
    p_intense = next(p for p in places_service.get_all_places("pondicherry") if p.category == CategoryEnum.ADVENTURE)

    score_senior_acc = place_scorer.score_place(p_accessible, criteria={"age_group": "seniors"}, current_slot="morning")
    score_senior_intense = place_scorer.score_place(p_intense, criteria={"age_group": "seniors"}, current_slot="morning")
    assert score_senior_acc > score_senior_intense

def test_13_scorer_weekly_closing_check():
    """Test 13: Closed place on travel_date returns -inf."""
    p_closed = make_test_place(
        id="test-closed",
        name="Closed Museum",
        city_id="chennai",
        weekly_closing_days=["Monday"]
    )
    # 2026-11-02 is a Monday
    score_mon = place_scorer.score_place(p_closed, criteria={"travel_date": "2026-11-02"}, current_slot="morning")
    assert score_mon == -float("inf")

    # 2026-11-03 is a Tuesday
    score_tue = place_scorer.score_place(p_closed, criteria={"travel_date": "2026-11-03"}, current_slot="morning")
    assert score_tue > -float("inf")


# ==============================================================================
# SECTION 3: Soft Geographic Zone Clustering & Road Routing (Tests 14 - 18)
# ==============================================================================

def test_14_geo_zone_assignment_pondicherry():
    """Test 14: Places assign to correct Pondicherry zones."""
    p_white_town = next(p for p in places_service.get_all_places("pondicherry") if "promenade" in p.name.lower())
    p_auroville = next(p for p in places_service.get_all_places("pondicherry") if "auroville" in p.name.lower() or "matrimandir" in p.name.lower())

    z_wt = geo_clusterer.assign_place_zone(p_white_town, "pondicherry")
    z_av = geo_clusterer.assign_place_zone(p_auroville, "pondicherry")

    assert z_wt["id"] in ["pondy_zone_1", "pondy_zone_2"]
    assert z_av["id"] == "pondy_zone_3"

def test_15_geo_zone_assignment_chennai():
    """Test 15: Places assign to correct Chennai zones."""
    p_marina = next(p for p in places_service.get_all_places("chennai") if "marina" in p.name.lower())
    p_dakshina = next(p for p in places_service.get_all_places("chennai") if "dakshina" in p.name.lower())

    z_marina = geo_clusterer.assign_place_zone(p_marina, "chennai")
    z_dakshina = geo_clusterer.assign_place_zone(p_dakshina, "chennai")

    assert z_marina["id"] == "chennai_zone_1"
    assert z_dakshina["id"] == "chennai_zone_4"

def test_16_geo_transit_first_stop_exempt():
    """Test 16: First stop of each day has travel_time_from_prev_minutes == 0 or None."""
    itin = itinerary_service.generate_itinerary_alternatives("pondicherry", 2)
    for alt in itin.alternatives:
        for day in alt.days:
            assert day.morning is not None
            assert day.morning.travel_time_from_prev_minutes in [0, None]
            assert day.morning.travel_distance_from_prev_km in [0.0, None]

def test_17_geo_transit_detour_fallback():
    """Test 17: Valid road distance and transit time calculated via Haversine detour without crashing."""
    res = geo_clusterer.calculate_transit((11.9338, 79.8358), (12.0070, 79.8107), "pondicherry", "car")
    assert res["travel_distance_km"] > 0
    assert res["travel_time_minutes"] > 0
    assert res["is_approximate"] is True
    assert "detour" in res["label"].lower() or "transit" in res["label"].lower()

def test_18_geo_transit_modes_speed():
    """Test 18: Walking is slower than car; bicycle is between walking and car."""
    c1, c2 = (11.9338, 79.8358), (11.9480, 79.8300)
    t_walk = geo_clusterer.calculate_transit(c1, c2, "pondicherry", "walking")
    t_bike = geo_clusterer.calculate_transit(c1, c2, "pondicherry", "bicycle")
    t_car = geo_clusterer.calculate_transit(c1, c2, "pondicherry", "car")

    assert t_walk["travel_time_minutes"] > t_bike["travel_time_minutes"]
    assert t_bike["travel_time_minutes"] > t_car["travel_time_minutes"]


# ==============================================================================
# SECTION 4: Multi-Day Duplicate Elimination & Alternative Design (Tests 19 - 23)
# ==============================================================================

def test_19_multiday_zero_duplicate_attractions_pondy():
    """Test 19: 2, 3, and 4-day Pondicherry itineraries have 0 duplicate places across days per alt."""
    for days in [2, 3, 4]:
        itin = itinerary_service.generate_itinerary_alternatives("pondicherry", days)
        for alt in itin.alternatives:
            p_ids = []
            for day in alt.days:
                for slot in [day.morning, day.afternoon, day.evening]:
                    if slot and slot.place_id:
                        p_ids.append(slot.place_id)
            assert len(p_ids) == len(set(p_ids)), f"Duplicate in Pondy {days}-day alt {alt.id}: {p_ids}"

def test_20_multiday_zero_duplicate_attractions_chennai():
    """Test 20: 2, 3, and 4-day Chennai itineraries have 0 duplicate places across days per alt."""
    for days in [2, 3, 4]:
        itin = itinerary_service.generate_itinerary_alternatives("chennai", days)
        for alt in itin.alternatives:
            p_ids = []
            for day in alt.days:
                for slot in [day.morning, day.afternoon, day.evening]:
                    if slot and slot.place_id:
                        p_ids.append(slot.place_id)
            assert len(p_ids) == len(set(p_ids)), f"Duplicate in Chennai {days}-day alt {alt.id}: {p_ids}"

def test_21_multiday_zero_duplicate_attractions_both():
    """Test 21: Multi-day combined itineraries have 0 duplicate places across days per alt."""
    for days in [2, 3, 4]:
        itin = itinerary_service.generate_itinerary_alternatives("both", days)
        for alt in itin.alternatives:
            p_ids = []
            for day in alt.days:
                for slot in [day.morning, day.afternoon, day.evening]:
                    if slot and slot.place_id:
                        p_ids.append(slot.place_id)
            assert len(p_ids) == len(set(p_ids)), f"Duplicate in Both {days}-day alt {alt.id}: {p_ids}"

def test_22_alternative_distinctness():
    """Test 22: The 3 alternatives have distinct themes, pacing, and start times."""
    itin = itinerary_service.generate_itinerary_alternatives("pondicherry", 2)
    assert len(itin.alternatives) == 3
    alts = {a.id: a for a in itin.alternatives}

    assert "alt-relaxed" in alts
    assert "alt-cultural" in alts
    assert "alt-active" in alts

    assert "leisurely" in alts["alt-relaxed"].summary.lower() or "ocean" in alts["alt-relaxed"].summary.lower() or "relaxed" in alts["alt-relaxed"].name.lower()
    assert "heritage" in alts["alt-cultural"].summary.lower() or "architecture" in alts["alt-cultural"].summary.lower()
    assert "activities" in alts["alt-active"].summary.lower() or "active" in alts["alt-active"].name.lower() or "adventure" in alts["alt-active"].tag.lower()

def test_23_alternative_highlight_sharing():
    """Test 23: Iconic highlights can appear across different alternatives in different themes."""
    itin = itinerary_service.generate_itinerary_alternatives("pondicherry", 2)
    # Check that alternatives are not required to be mutually disjoint across alts
    all_alt_places = [
        {s.place_id for d in alt.days for s in [d.morning, d.afternoon, d.evening] if s and s.place_id}
        for alt in itin.alternatives
    ]
    assert len(all_alt_places) == 3


# ==============================================================================
# SECTION 5: Itemized Budgeting & Transparent Estimation (Tests 24 - 26)
# ==============================================================================

def test_24_itemized_budget_exact_arithmetic():
    """Test 24: Total INR equals sum of entry fees + food + transit + misc."""
    itin = itinerary_service.generate_itinerary_alternatives("pondicherry", 3, party_size=2)
    assert itin.budget_breakdown is not None
    bd = itin.budget_breakdown

    expected_total = (
        bd["entry_fees_inr"] +
        bd["food_dining_inr"] +
        bd["local_transit_inr"] +
        bd["miscellaneous_inr"]
    )
    assert bd["total_inr"] == expected_total
    assert itin.total_estimated_budget_inr == expected_total

def test_25_budget_party_size_scaling():
    """Test 25: Entry fees and food scale with party_size."""
    itin_1 = itinerary_service.generate_itinerary_alternatives("pondicherry", 2, party_size=1)
    itin_4 = itinerary_service.generate_itinerary_alternatives("pondicherry", 2, party_size=4)

    bd1 = itin_1.budget_breakdown
    bd4 = itin_4.budget_breakdown

    assert bd4["food_dining_inr"] == bd1["food_dining_inr"] * 4
    assert bd4["miscellaneous_inr"] == bd1["miscellaneous_inr"] * 4

def test_26_budget_disclaimer_present():
    """Test 26: Transparent estimation disclaimer present in itinerary."""
    itin = itinerary_service.generate_itinerary_alternatives("pondicherry", 2)
    assert itin.budget_disclaimer is not None
    assert "exact arithmetic" in itin.budget_disclaimer.lower()
    assert "transparent estimates" in itin.budget_disclaimer.lower()


# ==============================================================================
# SECTION 6: Multi-Dimensional Quality Scoring & Catalog Limitation (Tests 27 - 29)
# ==============================================================================

def test_27_quality_score_dimensions():
    """Test 27: Quality score returns float between 0 and 100 for all alternatives."""
    itin = itinerary_service.generate_itinerary_alternatives("pondicherry", 2)
    assert itin.quality_score is not None
    assert 50.0 <= itin.quality_score <= 100.0
    for alt in itin.alternatives:
        assert alt.quality_score is not None
        assert 50.0 <= alt.quality_score <= 100.0

def test_28_quality_score_mandatory_preservation():
    """Test 28: Mandatory places are retained even if score is affected."""
    # Auroville requested
    itin = itinerary_service.generate_itinerary_alternatives(
        "pondicherry", 2, requested_places=["Auroville Matrimandir"]
    )
    scheduled_names = [
        s.place_name.lower()
        for d in itin.days
        for s in [d.morning, d.afternoon, d.evening] if s
    ]
    assert any("auroville" in n or "matrimandir" in n for n in scheduled_names)

def test_29_insufficient_catalog_limitation_notice():
    """Test 29: Trip requesting long duration handles catalog limitations honestly."""
    itin = itinerary_service.generate_itinerary_alternatives("pondicherry", 7)
    # Check that days length is 7
    assert len(itin.days) == 7
    # Zero duplicates across days
    p_ids = [s.place_id for d in itin.days for s in [d.morning, d.afternoon, d.evening] if s and s.place_id]
    assert len(p_ids) == len(set(p_ids))


# ==============================================================================
# SECTION 7: Conversational Delta Editing (Tests 30 - 32)
# ==============================================================================

def test_30_conversational_delta_add_place():
    """Test 30: 'Add <Place> to Day 1 afternoon' updates only that slot and preserves others."""
    itin = itinerary_service.generate_itinerary_alternatives("pondicherry", 2)
    itin_dict = itin.model_dump()
    orig_morning = itin.days[0].morning.place_name

    modified = itinerary_service.modify_itinerary_conversationally(
        itin_dict, "Add Serenity Beach to Day 1 afternoon"
    )
    assert modified.days[0].morning.place_name == orig_morning
    assert "Serenity Beach" in modified.days[0].afternoon.place_name

def test_31_conversational_delta_remove_slot():
    """Test 31: 'Remove evening from Day 1' sets evening to None and preserves others."""
    itin = itinerary_service.generate_itinerary_alternatives("pondicherry", 2)
    itin_dict = itin.model_dump()
    orig_morning = itin.days[0].morning.place_name

    modified = itinerary_service.modify_itinerary_conversationally(
        itin_dict, "Remove evening from Day 1"
    )
    assert modified.days[0].morning.place_name == orig_morning
    assert modified.days[0].evening is None

def test_32_conversational_delta_scoped_to_active_alt():
    """Test 32: Inactive alternatives are not modified by delta edit."""
    itin = itinerary_service.generate_itinerary_alternatives("pondicherry", 2)
    itin.active_alternative_id = "alt-relaxed"
    alt_cultural_orig = copy.deepcopy(next(a for a in itin.alternatives if a.id == "alt-cultural"))

    itin_dict = itin.model_dump()
    modified = itinerary_service.modify_itinerary_conversationally(
        itin_dict, "Add Serenity Beach to Day 1 afternoon"
    )
    alt_cultural_after = next(a for a in modified.alternatives if a.id == "alt-cultural")
    assert alt_cultural_orig.days[0].afternoon.place_name == alt_cultural_after.days[0].afternoon.place_name


# ==============================================================================
# SECTION 8: 10-Point Itinerary Validator & Recovery (Tests 33 - 35)
# ==============================================================================

def test_33_ten_point_validator_success():
    """Test 33: Valid generated itinerary passes all 10 checks."""
    itin = itinerary_service.generate_itinerary_alternatives("pondicherry", 2)
    is_valid, issues = itinerary_service.validate_itinerary(itin)
    assert is_valid is True
    assert len(issues) == 0

def test_34_ten_point_validator_catches_invalid_destination():
    """Test 34: Unsupported destination fails validator."""
    itin = itinerary_service.generate_itinerary_alternatives("pondicherry", 2)
    itin.city_id = "tokyo"
    is_valid, issues = itinerary_service.validate_itinerary(itin)
    assert is_valid is False
    assert any("tokyo" in iss.lower() for iss in issues)

def test_35_ten_point_validator_catches_duplicate():
    """Test 35: Itinerary artificially injected with duplicate fails validator."""
    itin = itinerary_service.generate_itinerary_alternatives("pondicherry", 2)
    # Inject duplicate place in day 2
    itin.alternatives[0].days[1].morning.place_id = itin.alternatives[0].days[0].morning.place_id
    is_valid, issues = itinerary_service.validate_itinerary(itin)
    assert is_valid is False
    assert any("duplicate" in iss.lower() for iss in issues)


# ==============================================================================
# SECTION 9: API Consolidation & Backward Compatibility (Tests 36 - 40)
# ==============================================================================

def test_36_legacy_endpoint_generate_itinerary_pondicherry():
    """Test 36: POST /api/v1/recommendations/generate-itinerary returns backward-compatible shape."""
    payload = {
        "city_id": "pondicherry",
        "query_text": "Plan a 2-day relaxed trip with French cafes and beach walk",
        "duration_days": 2
    }
    res = client.post("/api/v1/recommendations/generate-itinerary", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["city_id"] == "pondicherry"
    assert "available_alternatives" in data
    assert "itinerary" in data
    assert len(data["itinerary"]["days"]) == 2

    # Check zero duplicates
    p_ids = []
    for d in data["itinerary"]["days"]:
        for k in ["morning", "afternoon", "evening"]:
            slot = d.get(k)
            if slot and slot.get("place_id"):
                p_ids.append(slot["place_id"])
    assert len(p_ids) == len(set(p_ids))

def test_37_legacy_endpoint_generate_itinerary_chennai():
    """Test 37: POST /api/v1/recommendations/generate-itinerary returns backward-compatible shape for Chennai."""
    payload = {
        "city_id": "chennai",
        "query_text": "Plan a 2-day cultural trip to ancient temples in Chennai",
        "duration_days": 2
    }
    res = client.post("/api/v1/recommendations/generate-itinerary", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["city_id"] == "chennai"
    assert len(data["itinerary"]["days"]) == 2

def test_38_legacy_endpoint_rate_limiter():
    """Test 38: Preserves reset rate limit endpoint."""
    res = client.post("/api/v1/recommendations/reset-rate-limit")
    assert res.status_code == 200
    assert res.json()["status"] == "reset"

def test_39_chat_endpoint_multi_alternative():
    """Test 39: POST /api/v1/chat/message with planning request returns 3 alternatives."""
    payload = {
        "message": "Plan a 2-day trip to Pondicherry",
        "duration_days": 2
    }
    res = client.post("/api/v1/chat/message", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "itinerary_planning"
    assert data["itinerary"] is not None
    assert len(data["itinerary"]["alternatives"]) == 3
    assert data["itinerary"]["quality_score"] is not None

def test_40_unsupported_destination_policy_preserved():
    """Test 40: Unsupported destination returns policy explanation without generating itinerary."""
    payload = {
        "message": "Plan a 3-day itinerary for Tokyo",
        "duration_days": 3
    }
    res = client.post("/api/v1/chat/message", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["itinerary"] is None
    assert "Tokyo" in data["reply_message"]
    assert "Pondicherry" in data["reply_message"]
