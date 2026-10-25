import sys
import os
import json
import urllib.request
import urllib.error

sys.path.insert(0, "backend")
sys.path.insert(0, os.path.abspath("backend"))

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_routes():
    print("==================================================================")
    print("VOYANTRA PHASE 4 - ROUTING & CASCADE VERIFICATION TEST SUITE")
    print("==================================================================")

    # -------------------------------------------------------------------------
    # TEST 1: Driving Route between Pondicherry Promenade & French Quarter
    # -------------------------------------------------------------------------
    print("\n--- TEST 1: POST /api/v1/routes/plan (Driving Mode) ---")
    req_body = {
        "origin_lat": 11.934,
        "origin_lng": 79.832,
        "dest_lat": 11.938,
        "dest_lng": 79.834,
        "mode": "driving",
        "city_id": "pondicherry",
        "traffic_multiplier": 1.0
    }
    req = urllib.request.Request(
        f"{BASE_URL}/routes/plan",
        data=json.dumps(req_body).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        data = json.loads(resp.read().decode("utf-8"))
        print(f"Status: {resp.status} OK")
        print(f"Distance: {data['distance_km']} km")
        print(f"Estimated Travel Time: {data['estimated_travel_time_minutes']} min")
        print(f"Tier Used: {data['tier_used']}")
        print(f"Is Approximate: {data['is_approximate']}")
        print(f"Approximate Label: '{data['approximate_label']}'")
        print(f"Polyline Points Count: {len(data['polyline_geojson']['coordinates'])}")
        print(f"Turn Steps Count: {len(data['turn_by_turn_steps'])}")
        
        assert "tier_used" in data, "Missing tier_used"
        assert data["tier_used"] in ["local_osrm", "public_demo", "haversine_detour"]
        assert data["distance_km"] > 0, "Distance must be > 0"
        assert data["estimated_travel_time_minutes"] > 0, "Duration must be > 0"
        assert len(data['polyline_geojson']['coordinates']) >= 2, "Polyline must have >= 2 points"
        print("-> PASS: Driving route plan conforms to contract.")

    # -------------------------------------------------------------------------
    # TEST 2: Walking Route & Walking Speed Calculation Audit
    # -------------------------------------------------------------------------
    print("\n--- TEST 2: POST /api/v1/routes/plan (Walking Mode & Speed Fix) ---")
    req_body_walk = {
        "origin_lat": 11.934,
        "origin_lng": 79.832,
        "dest_lat": 11.938,
        "dest_lng": 79.834,
        "mode": "walking",
        "city_id": "pondicherry"
    }
    req_walk = urllib.request.Request(
        f"{BASE_URL}/routes/plan",
        data=json.dumps(req_body_walk).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_walk) as resp:
        assert resp.status == 200
        data_walk = json.loads(resp.read().decode("utf-8"))
        dist_km = data_walk['distance_km']
        time_min = data_walk['estimated_travel_time_minutes']
        print(f"Status: {resp.status} OK")
        print(f"Distance: {dist_km} km")
        print(f"Estimated Walking Time: {time_min} min")
        print(f"Tier Used: {data_walk['tier_used']}")
        print(f"Approximate Label: '{data_walk['approximate_label']}'")
        
        # Calculate implied speed: (km / (min / 60))
        implied_speed = dist_km / (time_min / 60.0) if time_min > 0 else 0
        print(f"Implied Pedestrian Speed: {implied_speed:.2f} km/h")
        
        # Assert pedestrian speed is around 4.5 km/h (tolerance: 4.0 - 5.0 km/h)
        # Definitely NOT the 23.4 km/h car speed that the public demo originally returned!
        assert 4.0 <= implied_speed <= 5.5, f"Walking speed {implied_speed} km/h is unrealistic (expected ~4.5 km/h)"
        assert time_min > data["estimated_travel_time_minutes"], "Walking must take longer than driving!"
        print(f"-> PASS: Walking time correctly calibrated to human pedestrian speed ({implied_speed:.2f} km/h vs driving {data['estimated_travel_time_minutes']} min).")

    # -------------------------------------------------------------------------
    # TEST 3: Route Matrix Endpoint
    # -------------------------------------------------------------------------
    print("\n--- TEST 3: POST /api/v1/routes/matrix (3 Pondicherry Waypoints) ---")
    req_body_matrix = {
        "coordinates": [
            {"lat": 11.934, "lng": 79.832}, # Promenade Beach
            {"lat": 11.938, "lng": 79.834}, # French Quarter
            {"lat": 11.931, "lng": 79.825}  # Botanical Gardens area
        ],
        "mode": "driving",
        "city_id": "pondicherry"
    }
    req_matrix = urllib.request.Request(
        f"{BASE_URL}/routes/matrix",
        data=json.dumps(req_body_matrix).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_matrix) as resp:
        assert resp.status == 200
        matrix_data = json.loads(resp.read().decode("utf-8"))
        print(f"Status: {resp.status} OK")
        print(f"Tier Used: {matrix_data['tier_used']}")
        print(f"Is Approximate: {matrix_data['is_approximate']}")
        print(f"Approximate Label: '{matrix_data['approximate_label']}'")
        print(f"Durations Matrix (3x3 min): {matrix_data['durations_minutes']}")
        print(f"Distances Matrix (3x3 km): {matrix_data['distances_km']}")
        
        assert len(matrix_data['durations_minutes']) == 3
        assert len(matrix_data['distances_km']) == 3
        # Check diagonal is 0.0
        for i in range(3):
            assert matrix_data['durations_minutes'][i][i] == 0.0
            assert matrix_data['distances_km'][i][i] == 0.0
        print("-> PASS: NxN distance and duration matrix generated correctly with zero diagonals.")

    # -------------------------------------------------------------------------
    # TEST 4: Tier 3 Fallback Verification (Forced Offline Simulation)
    # -------------------------------------------------------------------------
    print("\n--- TEST 4: Tier 3 In-Memory Haversine Detour Fallback Simulation ---")
    from app.services.routing_service import RoutingService
    from app.core.config import settings
    
    # Instantiate service pointing to unreachable ports
    fallback_svc = RoutingService()
    fallback_svc.local_driving_url = "http://127.0.0.1:59999"
    fallback_svc.local_walking_url = "http://127.0.0.1:59999"
    fallback_svc.public_demo_url = "http://127.0.0.1:59999"
    
    fallback_route = fallback_svc.get_route(
        origin_lat=11.934888, origin_lng=79.832888,
        dest_lat=11.938888, dest_lng=79.834888,
        mode="driving",
        city_id="pondicherry"
    )
    print(f"Tier Used: {fallback_route.tier_used}")
    print(f"Is Approximate: {fallback_route.is_approximate}")
    print(f"Approximate Label: '{fallback_route.approximate_label}'")
    print(f"Warning: '{fallback_route.warning}'")
    print(f"Distance: {fallback_route.distance_km} km")
    print(f"Estimated Travel Time: {fallback_route.estimated_travel_time_minutes} min")
    
    assert fallback_route.tier_used == "haversine_detour"
    assert fallback_route.is_approximate is True
    assert "Approximate travel time" in fallback_route.approximate_label
    assert fallback_route.warning is not None
    print("-> PASS: Graceful cascade to Tier 3 verified under complete network outage.")

    # -------------------------------------------------------------------------
    # TEST 5: Edge Case - Identical Origin & Destination
    # -------------------------------------------------------------------------
    print("\n--- TEST 5: Edge Case - Identical Origin & Destination ---")
    zero_route = fallback_svc.get_route(
        origin_lat=11.934, origin_lng=79.832,
        dest_lat=11.934, dest_lng=79.832,
        mode="driving",
        city_id="pondicherry"
    )
    print(f"Distance: {zero_route.distance_km} km")
    print(f"Estimated Travel Time: {zero_route.estimated_travel_time_minutes} min")
    print(f"Instruction: {zero_route.turn_by_turn_steps[0].instruction}")
    assert zero_route.distance_km == 0.0
    assert zero_route.estimated_travel_time_minutes == 0.0
    print("-> PASS: Identical waypoint handled immediately without network overhead.")

    print("\n==================================================================")
    print("ALL PHASE 4 (P4-T1 & P4-T2) ROUTING TESTS PASSED (5/5)")
    print("==================================================================")

if __name__ == "__main__":
    test_routes()
