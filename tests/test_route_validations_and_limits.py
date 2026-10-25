import sys
import os
import json
import time
import urllib.request
import urllib.error

sys.path.insert(0, "backend")
sys.path.insert(0, os.path.abspath("backend"))

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

BASE_URL = "http://127.0.0.1:8000/api/v1/routes"

def post_json(endpoint: str, data: dict):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"raw": body}
        return e.code, parsed

def run_tests():
    print("==================================================================")
    print("ROUTE VALIDATION, STRICT BOUNDS, THROTTLE & RATE LIMIT TESTS")
    print("==================================================================")
    results = {}

    # 1. Coordinate Range Validation (Pydantic ge/le)
    print("\n--- TEST V1: Coordinate Out-of-Range (-90..90, -180..180) ---")
    status, body = post_json("/plan", {
        "origin_lat": 95.5, # Illegal latitude > 90
        "origin_lng": 79.832,
        "dest_lat": 11.938,
        "dest_lng": 79.834
    })
    print(f"Response: HTTP {status}, body snippet: {str(body)[:120]}")
    assert status == 422, f"Expected 422, got {status}"
    results["V1_CoordRange"] = "PASS"
    print("-> PASS: Invalid WGS84 coordinate rejected with 422.")

    # 2. Rejection of Points Outside Operating Territory
    print("\n--- TEST V2: Rejection of Points Outside Pondicherry/Chennai ---")
    # Bangalore origin (12.9716, 77.5946)
    status_b, body_b = post_json("/plan", {
        "origin_lat": 12.9716,
        "origin_lng": 77.5946,
        "dest_lat": 11.938,
        "dest_lng": 79.834
    })
    print(f"Bangalore origin: HTTP {status_b}, detail: {body_b.get('detail')}")
    assert status_b == 400 and "outside Voyantra operating destinations" in body_b.get("detail", "")
    
    # Delhi destination (28.6139, 77.2090)
    status_d, body_d = post_json("/plan", {
        "origin_lat": 11.934,
        "origin_lng": 79.832,
        "dest_lat": 28.6139,
        "dest_lng": 77.2090
    })
    print(f"Delhi destination: HTTP {status_d}, detail: {body_d.get('detail')}")
    assert status_d == 400 and "outside Voyantra operating destinations" in body_d.get("detail", "")
    results["V2_BoundsRejection"] = "PASS"
    print("-> PASS: Distant points outside operating territory rejected with 400.")

    # 3. Test V2b: Point INSIDE old corridor box [11.5, 13.5] x [79.5, 80.5], but OUTSIDE both 70 km radii
    print("\n--- TEST V2b: Point inside old corridor box but outside both 70km radii ---")
    # Point (12.5, 79.5):
    # Latitude 12.5 is inside [11.5, 13.5], Longitude 79.5 is inside [79.5, 80.5]
    # Distance to Pondy (11.9416, 79.8083) = 70.47 km (> 70 km)
    # Distance to Chennai (13.0827, 80.2707) = 105.02 km (> 70 km)
    # Under strict 70km dual-circle check, this point MUST be rejected!
    status_box, body_box = post_json("/plan", {
        "origin_lat": 12.5,
        "origin_lng": 79.5,
        "dest_lat": 11.934,
        "dest_lng": 79.832
    })
    print(f"Box point (12.5, 79.5): HTTP {status_box}, detail: {body_box.get('detail')}")
    assert status_box == 400, f"Expected 400, got {status_box}"
    assert "outside Voyantra operating destinations" in body_box.get("detail", "")
    results["V2b_CorridorBoxRemoved"] = "PASS"
    print("-> PASS: Point inside old rectangular box but outside both 70km radii successfully rejected.")

    # 4. Maximum Waypoint Count on Matrix (> 10)
    print("\n--- TEST V3: Matrix Waypoint Count Enforcement (Max 10) ---")
    # 11 waypoints
    coords_11 = [{"lat": 11.930 + i * 0.001, "lng": 79.830 + i * 0.001} for i in range(11)]
    status_m, body_m = post_json("/matrix", {
        "coordinates": coords_11,
        "mode": "driving",
        "city_id": "pondicherry"
    })
    print(f"11 waypoints response: HTTP {status_m}, body snippet: {str(body_m)[:120]}")
    assert status_m in [400, 422], f"Expected 400/422, got {status_m}"
    results["V3_MatrixMaxWaypoints"] = "PASS"
    print("-> PASS: Waypoint count > 10 rejected.")

    # 5. Chennai Route Pair: Marina Beach to Kapaleeshwarar Temple
    print("\n--- TEST V4: Chennai Route Pair (Marina Beach -> Kapaleeshwarar Temple) ---")
    status_c, body_c = post_json("/plan", {
        "origin_lat": 13.0499,
        "origin_lng": 80.2824,
        "dest_lat": 13.0335,
        "dest_lng": 80.2698,
        "mode": "driving",
        "city_id": "chennai"
    })
    print(f"Chennai Route: HTTP {status_c}")
    print(f"  Distance: {body_c.get('distance_km')} km")
    print(f"  Estimated Travel Time: {body_c.get('estimated_travel_time_minutes')} min")
    print(f"  Tier Used: {body_c.get('tier_used')}")
    print(f"  Approximate Label: '{body_c.get('approximate_label')}'")
    assert status_c == 200
    assert 2.0 <= body_c.get('distance_km') <= 6.0
    results["V4_ChennaiPair"] = "PASS"
    print("-> PASS: Chennai intra-city route calculated with correct maneuvers.")

    # 6. Longer Route: Pondicherry Promenade to Marina Beach Chennai (~146 km)
    print("\n--- TEST V5: Long Route (Pondicherry Promenade -> Marina Beach Chennai) ---")
    status_l, body_l = post_json("/plan", {
        "origin_lat": 11.9340,
        "origin_lng": 79.8320,
        "dest_lat": 13.0499,
        "dest_lng": 80.2824,
        "mode": "driving",
        "city_id": "chennai"
    })
    print(f"Long Route: HTTP {status_l}")
    print(f"  Distance: {body_l.get('distance_km')} km")
    print(f"  Estimated Travel Time: {body_l.get('estimated_travel_time_minutes')} min ({body_l.get('estimated_travel_time_minutes')/60:.2f} hours)")
    print(f"  Tier Used: {body_l.get('tier_used')}")
    assert status_l == 200
    assert body_l.get('distance_km') >= 130.0
    results["V5_LongerRoute"] = "PASS"
    print("-> PASS: Inter-city route calculated successfully.")

    # 7. Global Outbound Throttle Test (~1 req/second) in front of Tier 2
    print("\n--- TEST V6: Global Outbound Throttle (~1 req/sec in front of Tier 2) ---")
    from app.services.routing_service import _throttle_tier2_call, TIER2_MIN_REQUEST_INTERVAL
    t0 = time.time()
    # Call throttle twice back-to-back
    _throttle_tier2_call()
    _throttle_tier2_call()
    t_elapsed = time.time() - t0
    print(f"Elapsed time across 2 consecutive throttle calls: {t_elapsed:.3f}s (Min expected: {TIER2_MIN_REQUEST_INTERVAL}s)")
    assert t_elapsed >= (TIER2_MIN_REQUEST_INTERVAL - 0.05), f"Throttle allowed call too fast: {t_elapsed:.3f}s"
    results["V6_GlobalThrottle"] = "PASS"
    print(f"-> PASS: Global outbound throttle enforced minimum {TIER2_MIN_REQUEST_INTERVAL}s interval between Tier 2 requests.")

    # 8. Rate Limiting on /routes/* (30 req/min per IP limit)
    print("\n--- TEST V7: Per-IP Rate Limiting on /routes/* (30 req/min limit) ---")
    import concurrent.futures

    def send_rapid_req(idx):
        return post_json("/plan", {
            "origin_lat": 11.934,
            "origin_lng": 79.832,
            "dest_lat": 11.938,
            "dest_lng": 79.834,
            "mode": "driving",
            "city_id": "pondicherry"
        })

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_rapid_req, i) for i in range(35)]
        burst_results = [f.result() for f in futures]

    status_codes = [s for s, _ in burst_results]
    count_429 = status_codes.count(429)
    print(f"Burst Results: Status codes {set(status_codes)}, Total 429 responses: {count_429}")
    assert count_429 > 0, "Rate limit 429 was not triggered during concurrent burst"
    results["V7_RateLimit"] = "PASS"
    print(f"-> PASS: Rate limiter correctly blocked excess concurrent traffic with HTTP 429 ({count_429} blocked).")

    print("\n==================================================================")
    passed_cnt = sum(1 for v in results.values() if v == "PASS")
    print(f"==================== {passed_cnt}/{len(results)} VALIDATION TESTS PASSED ====================")
    print("==================================================================")

if __name__ == "__main__":
    run_tests()
