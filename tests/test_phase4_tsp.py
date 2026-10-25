import sys
import codecs
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")

backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_tsp():
    print("=" * 70)
    print("TESTING P4-T4 & P4-T5: CONSTRAINED TSP SOLVER & FESTIVAL CLOSURES")
    print("=" * 70)

    # 4 stops in Pondicherry:
    # Stop 1: Aayi Mandapam (White Town) - flexible, unverified hours
    # Stop 2: Promenade Beach - sunset anchor (17:00 - 19:00)
    # Stop 3: French War Memorial - morning anchor
    # Stop 4: Sacred Heart Basilica - locked at index 0 (start of day)
    payload = {
        "day_number": 1,
        "city_id": "pondicherry",
        "mode": "driving",
        "travel_date": "2026-11-15",
        "day_start_time": "09:00",
        "slots": [
            {
                "slot_id": "s1",
                "place_name": "Sacred Heart Basilica",
                "coordinates": {"lat": 11.9287, "lng": 79.8276},
                "is_locked": True,
                "visit_duration_minutes": 45,
                "opening_hours": {"is_verified": True, "weekday_open": "07:00", "weekday_close": "19:00"}
            },
            {
                "slot_id": "s2",
                "place_name": "Promenade Beach",
                "coordinates": {"lat": 11.9338, "lng": 79.8358},
                "time_anchor": "sunset",
                "visit_duration_minutes": 60,
                "opening_hours": {"is_verified": True, "weekday_open": "05:00", "weekday_close": "22:00"}
            },
            {
                "slot_id": "s3",
                "place_name": "Aayi Mandapam",
                "coordinates": {"lat": 11.9344, "lng": 79.8306},
                "visit_duration_minutes": 45,
                "opening_hours": {"is_verified": False}
            },
            {
                "slot_id": "s4",
                "place_name": "French War Memorial",
                "coordinates": {"lat": 11.9325, "lng": 79.8351},
                "time_anchor": "morning",
                "visit_duration_minutes": 30,
                "opening_hours": {"is_verified": True, "weekday_open": "08:00", "weekday_close": "18:00"}
            }
        ]
    }

    r = requests.post(f"{BASE_URL}/routes/optimize-day", json=payload, timeout=20)
    print(f"Status Code: {r.status_code}")
    assert r.status_code == 200, f"Error: {r.text}"

    data = r.json()
    opt_slots = data["optimized_slots"]
    transit_legs = data["transit_legs"]

    print("\n--- Optimized Schedule ---")
    for s in opt_slots:
        print(f"[{s['order']}] {s['start_time']} - {s['end_time']}: {s['place_name']} (anchor: {s.get('time_anchor')}, locked: {s['is_locked']})")
        if s.get("hours_warning"):
            print(f"    WARNING: {s['hours_warning']}")

    print("\n--- Transit Legs ---")
    for leg in transit_legs:
        print(f"🚗 {leg['from_place']} -> {leg['to_place']}: {leg['distance_km']} km, {leg['duration_minutes']} min (Depart: {leg['departure_time']}, Arrive: {leg['arrival_time']})")
        print(f"   Tier: {leg['tier_used']}, Approx: {leg['is_approximate']}")
        if leg.get("closure_affected"):
            print(f"   CLOSURE ALERT: {leg.get('closure_warning')}")

    # Assertions
    # 1. Stop 1 (Sacred Heart Basilica) was locked at order 1
    assert opt_slots[0]["place_name"] == "Sacred Heart Basilica", "Locked stop was moved!"
    # 2. Promenade Beach (sunset anchor) should be late in the day (start >= 17:00)
    sunset_slot = next(s for s in opt_slots if s["place_name"] == "Promenade Beach")
    start_hour = int(sunset_slot["start_time"].split(":")[0])
    assert start_hour >= 17, f"Sunset slot was scheduled too early: {sunset_slot['start_time']}"
    # 3. Aayi Mandapam had unverified hours -> must have hours_warning
    aayi_slot = next(s for s in opt_slots if s["place_name"] == "Aayi Mandapam")
    assert aayi_slot.get("hours_warning") is not None, "Missing unverified hours warning"
    # 4. Total travel time and distance
    assert data["total_travel_time_minutes"] > 0
    assert data["total_travel_distance_km"] > 0
    assert len(transit_legs) == 3

    print("\n" + "=" * 70)
    print("ALL TSP TESTS PASSED (P4-T4 & P4-T5 VERIFIED)")
    print("=" * 70)

if __name__ == "__main__":
    test_tsp()
