import sys
import os
import codecs
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")

backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import requests
from pymongo import MongoClient

from app.core.database import MONGODB_URL, DB_NAME
from app.services.crowd_service import REPORTS_COLLECTION, SNAPSHOTS_COLLECTION

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_phase5():
    print("=" * 70)
    print("VOYANTRA PHASE 5: CROWDSOURCING, GEOFENCE, SNAPSHOTS & BLENDING")
    print("=" * 70)

    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=500)
    db = client[DB_NAME]

    # Find a heritage / museum place in Pondicherry where baseline is moderate (~50-60%)
    r_places = requests.get(f"{BASE_URL}/places?city_id=pondicherry").json()
    assert len(r_places) > 0, "No places found in Pondicherry"
    test_place = next((p for p in r_places if p.get("category") in ["museum", "heritage"] and p.get("category") != "spiritual"), r_places[1])
    p_id = test_place["id"]
    p_name = test_place["name"]
    p_lat = test_place["coordinates"]["lat"]
    p_lng = test_place["coordinates"]["lng"]

    print(f"Testing with Destination: {p_name} (ID: {p_id}, Coords: {p_lat}, {p_lng})")

    # Clean existing reports for clean test
    db[REPORTS_COLLECTION].delete_many({"place_id": p_id})
    db[SNAPSHOTS_COLLECTION].delete_many({"place_id": p_id})

    # -------------------------------------------------------------------------
    # TEST 5.1: Geofence Rejection (> 200m away -> 403 Forbidden)
    # -------------------------------------------------------------------------
    print("\n--- TEST 5.1: Geofence Guard (> 200m away) ---")
    far_lat = p_lat + 0.05  # ~5.5 km away
    far_lng = p_lng + 0.05
    payload_far = {
        "place_id": p_id,
        "city_id": "pondicherry",
        "crowd_level": "bustling",
        "user_lat": far_lat,
        "user_lng": far_lng
    }
    r_far = requests.post(f"{BASE_URL}/crowd/report", json=payload_far)
    print(f"Far submission response: HTTP {r_far.status_code}")
    assert r_far.status_code == 403, f"Expected 403 Forbidden for distant submission, got: {r_far.status_code}"
    assert "Geofence verification failed" in r_far.json()["detail"]
    print("-> PASS: Distant submission strictly blocked by 200m geofence guard.")

    # -------------------------------------------------------------------------
    # TEST 5.2: Valid Geofenced Submission (<= 200m -> 200 OK)
    # -------------------------------------------------------------------------
    print("\n--- TEST 5.2: Valid Geofenced Submission (<= 200m on-site) ---")
    near_lat = p_lat + 0.0005  # ~55 meters away
    near_lng = p_lng + 0.0005
    payload_valid = {
        "place_id": p_id,
        "city_id": "pondicherry",
        "crowd_level": "bustling",
        "user_lat": near_lat,
        "user_lng": near_lng
    }
    r_valid = requests.post(f"{BASE_URL}/crowd/report", json=payload_valid)
    print(f"Valid on-site submission: HTTP {r_valid.status_code}")
    assert r_valid.status_code == 200, f"Expected 200 OK, got: {r_valid.text}"
    data_valid = r_valid.json()
    assert data_valid["reported_density_pct"] == 75  # Bustling = 75%
    assert data_valid["active_reports_count"] >= 1
    print(f"-> PASS: Report submitted successfully! Reported: {data_valid['reported_density_pct']}%, Blended: {data_valid['blended_density_pct']}%")

    # -------------------------------------------------------------------------
    # TEST 5.3: Cooldown Rate Limiting (15 min cooldown -> 429) & No Bypass
    # -------------------------------------------------------------------------
    print("\n--- TEST 5.3: Cooldown Rate Limiting & Bypass Defense (15-min cooldown) ---")
    r_repeat = requests.post(f"{BASE_URL}/crowd/report", json=payload_valid)
    print(f"Immediate repeat submission: HTTP {r_repeat.status_code}")
    assert r_repeat.status_code == 429, f"Expected 429 for rapid re-submission, got: {r_repeat.status_code}"
    assert "Cooldown active" in r_repeat.json()["detail"]

    # Verify public client CANNOT bypass cooldown with is_simulated in request body
    payload_bypass = {**payload_valid, "is_simulated": True}
    r_bypass = requests.post(f"{BASE_URL}/crowd/report", json=payload_bypass)
    assert r_bypass.status_code == 429, f"Cooldown bypass attempt failed to return 429: {r_bypass.status_code}"
    print("-> PASS: Rapid duplicate submission correctly throttled with HTTP 429, even with simulated flag in payload.")

    # -------------------------------------------------------------------------
    # TEST 5.4: Privacy Protection (No raw GPS stored in DB)
    # -------------------------------------------------------------------------
    print("\n--- TEST 5.4: Privacy & Anonymized Reporter Hash ---")
    stored_rep = db[REPORTS_COLLECTION].find_one({"place_id": p_id})
    assert stored_rep is not None
    assert "user_lat" not in stored_rep, "Raw user_lat found in database!"
    assert "user_lng" not in stored_rep, "Raw user_lng found in database!"
    assert "reporter_hash" in stored_rep, "Missing anonymized reporter hash!"
    assert stored_rep["verification_distance_m"] <= 200.0
    print(f"-> PASS: Privacy verified. Reporter hash: {stored_rep['reporter_hash']}, Verification dist: {stored_rep['verification_distance_m']}m.")

    # -------------------------------------------------------------------------
    # TEST 5.5: Feature Snapshot Logging (IST timezone & rule baseline)
    # -------------------------------------------------------------------------
    print("\n--- TEST 5.5: Feature Snapshot Logging & IST Timezone Consistency ---")
    from zoneinfo import ZoneInfo
    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
    stored_snap = db[SNAPSHOTS_COLLECTION].find_one({"place_id": p_id})
    assert stored_snap is not None
    assert stored_snap["hour_of_day"] == now_ist.hour, f"Snapshot hour {stored_snap['hour_of_day']} != IST hour {now_ist.hour}"
    assert stored_snap["day_of_week"] == now_ist.weekday()
    assert stored_snap["month"] == now_ist.month
    assert stored_snap["is_simulated"] is False
    assert "temperature_c" in stored_snap
    assert "precipitation_mm" in stored_snap
    assert "has_active_festival" in stored_snap
    assert stored_snap["rule_baseline_density_pct"] > 0
    print(f"-> PASS: Snapshot verified with IST features (hour: {stored_snap['hour_of_day']}, temp: {stored_snap['temperature_c']}°C, rain: {stored_snap['precipitation_mm']}mm, baseline: {stored_snap['rule_baseline_density_pct']}%).")

    # -------------------------------------------------------------------------
    # TEST 5.6: Exponential Decay Blending (Half-life = 30 min) & Confidence Level
    # -------------------------------------------------------------------------
    print("\n--- TEST 5.6: Exponential Decay Blending Engine & Confidence Level ---")
    now_utc = datetime.now(timezone.utc)
    # Insert older report from 30 mins ago (weight = 0.5)
    db[REPORTS_COLLECTION].insert_one({
        "place_id": p_id,
        "city_id": "pondicherry",
        "crowd_level": "overcrowded",
        "reported_density_pct": 95,
        "reporter_hash": "hash_user_2",
        "is_simulated": False,
        "verification_distance_m": 50.0,
        "created_at": now_utc - timedelta(minutes=30)
    })
    # Query live crowd status
    r_live = requests.get(f"{BASE_URL}/crowd/place/{p_id}/live?city_id=pondicherry")
    assert r_live.status_code == 200
    live_data = r_live.json()
    print(f"Live status: Baseline: {live_data['rule_baseline_density_pct']}%, Blended: {live_data['blended_density_pct']}%, Active: {live_data['active_reports_count']}, Conf: {live_data.get('confidence_level')}, Last: {live_data.get('last_reported_time')}")
    assert live_data["active_reports_count"] >= 2
    assert live_data["confidence_level"] in ["HIGH", "MEDIUM", "LOW"]
    assert live_data["last_reported_time"] is not None
    assert "IST" in live_data["last_reported_time"]
    # Blended density must shift towards the reports
    assert min(75, live_data["rule_baseline_density_pct"]) <= live_data["blended_density_pct"] <= max(95, live_data["rule_baseline_density_pct"])
    print("-> PASS: Exponential decay blending and confidence level verified.")

    # -------------------------------------------------------------------------
    # TEST 5.7: Surge Anomaly Detection (3+ DISTINCT reporters)
    # -------------------------------------------------------------------------
    print("\n--- TEST 5.7: Live Surge Anomaly Detection (3+ Distinct Reporters) ---")
    # Insert 2 more fresh overcrowded reports from distinct hashes
    for idx in [3, 4]:
        db[REPORTS_COLLECTION].insert_one({
            "place_id": p_id,
            "city_id": "pondicherry",
            "crowd_level": "overcrowded",
            "reported_density_pct": 95,
            "reporter_hash": f"hash_user_{idx}",
            "is_simulated": False,
            "verification_distance_m": 80.0,
            "created_at": now_utc - timedelta(minutes=5)
        })

    r_surge = requests.get(f"{BASE_URL}/crowd/place/{p_id}/live?city_id=pondicherry")
    surge_data = r_surge.json()
    print(f"Surge check: is_surge={surge_data['is_surge']}, alert={surge_data['anomaly_alert']}, badge={surge_data['status_badge']}, conf_level={surge_data['confidence_level']}")
    assert surge_data["is_surge"] is True, "Expected surge flag to trigger for 3+ high reports"
    assert surge_data["anomaly_alert"] is not None
    assert surge_data["confidence_level"] == "HIGH"
    print("-> PASS: Surge anomaly and HIGH confidence successfully detected and flagged.")

    # -------------------------------------------------------------------------
    # TEST 5.8: TTL Index Verification
    # -------------------------------------------------------------------------
    print("\n--- TEST 5.8: MongoDB TTL Index Verification ---")
    indexes = db[REPORTS_COLLECTION].index_information()
    assert "created_at_1" in indexes
    assert indexes["created_at_1"].get("expireAfterSeconds") == 86400
    print("-> PASS: 24-hour TTL index confirmed on crowd_reports (expireAfterSeconds=86400).")

    print("\n" + "=" * 70)
    print("ALL PHASE 5 BACKEND TESTS PASSED (8/8)")
    print("=" * 70)

if __name__ == "__main__":
    test_phase5()
