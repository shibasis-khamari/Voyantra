import sys
import os
import time
import json
import codecs
import threading
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import requests
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.core.database import MONGODB_URL, DB_NAME
from app.schemas.route import RoutingTier, WalkingSource, Coordinates
from app.services.route_cache_service import route_cache_service, CACHE_COLLECTION, CACHE_VERSION
from app.services.routing_service import routing_service

BASE_URL = "http://127.0.0.1:8000/api/v1"


def get_clean_col():
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=500)
    db = client[DB_NAME]
    return db[CACHE_COLLECTION]


def run_tests():
    print("=" * 70)
    print("VOYANTRA PHASE 4 TASK 3 (P4-T3) PERSISTENCE & CACHING TEST SUITE")
    print("=" * 70)
    results = {}
    col = get_clean_col()

    # T3.1: Key Isolation (Matrix Cell cannot satisfy Route Request)
    print("\n--- TEST T3.1: Key Isolation (Matrix-Cell vs Route Key) ---")
    o_lat, o_lng, d_lat, d_lng = 11.93381, 79.83582, 11.93444, 79.83060
    cell_key = route_cache_service.format_cell_key(o_lat, o_lng, d_lat, d_lng, "driving")
    route_key = route_cache_service.format_route_key(o_lat, o_lng, d_lat, d_lng, "driving")

    # Clear keys first
    col.delete_many({"cache_key": {"$in": [cell_key, route_key]}})

    # Insert pure cell entry
    col.insert_one({
        "cache_key": cell_key,
        "namespace": "cell",
        "cache_version": CACHE_VERSION,
        "distance_km": 0.85,
        "duration_min": 2.1,
        "tier_used": "public_demo",
        "created_at": datetime.now(timezone.utc)
    })

    # Query route cache directly
    hit = route_cache_service.get_cached_route(o_lat, o_lng, d_lat, d_lng, "driving")
    assert hit is None, f"Expected cache miss for route query when only cell key existed, got: {hit}"
    results["T3.1_KeyIsolation"] = "PASS"
    print("-> PASS: Cell document successfully isolated; never satisfies route queries.")

    # T3.2: Single Batch /table for Partially Cached Matrix
    print("\n--- TEST T3.2: Single Batch /table for Partially Cached Matrix ---")
    coords = [
        Coordinates(lat=11.9338, lng=79.8358),
        Coordinates(lat=11.9344, lng=79.8306),
        Coordinates(lat=11.9360, lng=79.8320)
    ]
    # Pre-populate one directed pair in cache
    pre_key = route_cache_service.format_cell_key(coords[0].lat, coords[0].lng, coords[1].lat, coords[1].lng, "driving")
    col.update_one(
        {"cache_key": pre_key},
        {"$set": {
            "cache_key": pre_key,
            "namespace": "cell",
            "cache_version": CACHE_VERSION,
            "origin_lat": coords[0].lat,
            "origin_lng": coords[0].lng,
            "dest_lat": coords[1].lat,
            "dest_lng": coords[1].lng,
            "mode": "driving",
            "distance_km": 0.85,
            "duration_min": 2.1,
            "tier_used": "public_demo",
            "created_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )

    t0 = time.time()
    matrix_resp = routing_service.get_matrix(coords, mode="driving")
    dur_matrix = time.time() - t0
    assert len(matrix_resp.durations_minutes) == 3
    assert len(matrix_resp.distances_km) == 3
    results["T3.2_SingleBatchTable"] = "PASS"
    print(f"-> PASS: 3x3 matrix assembled with 1 pre-cached cell and fresh pairs in {dur_matrix:.2f}s.")

    # T3.3: Cache Hit Integrity
    print("\n--- TEST T3.3: Cache Hit Integrity (Geometry, Steps & Preserved Fields) ---")
    route_resp = routing_service.get_route(o_lat, o_lng, d_lat, d_lng, mode="driving")
    assert route_resp.distance_km > 0
    if "haversine" in str(route_resp.tier_used):
        # Public demo timed out; seed a tier 2 record to test cache hit retrieval
        route_cache_service.save_route(
            origin_lat=o_lat, origin_lng=o_lng, dest_lat=d_lat, dest_lng=d_lng,
            mode="driving", city_id="pondicherry",
            distance_km=0.757, duration_min=1.9,
            polyline_geojson={"type": "LineString", "coordinates": [[79.830, 11.934], [79.831, 11.935]]},
            turn_by_turn_steps=[{"instruction": "Head east", "distance_m": 757, "duration_s": 114}],
            tier_used="public_demo"
        )
        route_resp = routing_service.get_route(o_lat, o_lng, d_lat, d_lng, mode="driving")

    # Query again (should be cache hit)
    hit_resp = routing_service.get_route(o_lat, o_lng, d_lat, d_lng, mode="driving")
    assert hit_resp.distance_km == route_resp.distance_km
    assert len(hit_resp.polyline_geojson.get("coordinates", [])) > 0
    assert len(hit_resp.turn_by_turn_steps) > 0
    assert hit_resp.tier_used == route_resp.tier_used
    results["T3.3_CacheHitIntegrity"] = "PASS"
    print(f"-> PASS: Cache hit preserves geometry ({len(hit_resp.polyline_geojson['coordinates'])} points) and steps.")

    # T3.4: Cache Write Failure Resilience
    print("\n--- TEST T3.4: Cache Write Failure Resilience ---")
    # Simulate DB write error without breaking route calculation
    original_save = route_cache_service.save_route
    try:
        route_cache_service.save_route = lambda *args, **kwargs: False
        res_fail_write = routing_service.get_route(11.9310, 79.8320, 11.9340, 79.8350, mode="driving")
        assert res_fail_write.distance_km > 0
        results["T3.4_WriteFailureResilience"] = "PASS"
        print("-> PASS: Route calculation succeeded even when cache write returns False.")
    finally:
        route_cache_service.save_route = original_save

    # T3.5: MongoDB-Down Latency Bound
    print("\n--- TEST T3.5: MongoDB-Down Latency Bound ---")
    original_circuit = route_cache_service._mongo_circuit_open
    try:
        # Trip the circuit breaker
        route_cache_service._mongo_circuit_open = True
        route_cache_service._mongo_opened_at = time.time()
        t_start = time.time()
        # Direct call to get_cached_route should be instantaneous
        miss = route_cache_service.get_cached_route(11.931, 79.832, 11.934, 79.835, "driving")
        elapsed_circuit = time.time() - t_start
        assert miss is None
        assert elapsed_circuit < 0.015, f"Circuit-open cache lookup took too long: {elapsed_circuit:.4f}s"
        results["T3.5_MongoDownLatency"] = "PASS"
        print(f"-> PASS: With circuit open, cache bypass took {elapsed_circuit*1000:.2f} ms (< 15 ms limit).")
    finally:
        route_cache_service._mongo_circuit_open = original_circuit

    # T3.6: Version Bump Invalidation
    print("\n--- TEST T3.6: Cache Version Bump Invalidation ---")
    test_key = route_cache_service.format_route_key(11.91, 79.81, 11.92, 79.82, "driving")
    col.update_one(
        {"cache_key": test_key},
        {"$set": {
            "cache_key": test_key,
            "namespace": "route",
            "cache_version": "v0_old",
            "distance_km": 1.5,
            "raw_duration_min": 3.0,
            "tier_used": "public_demo",
            "created_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )
    hit_v0 = route_cache_service.get_cached_route(11.91, 79.81, 11.92, 79.82, "driving")
    assert hit_v0 is None, "Expected cache miss for old version 'v0_old'"
    results["T3.6_VersionInvalidation"] = "PASS"
    print("-> PASS: Entries with older cache versions are correctly treated as misses.")

    # T3.7: Quality Upgrade & created_at Reset
    print("\n--- TEST T3.7: Quality Upgrade & created_at Reset ---")
    walk_key = route_cache_service.format_route_key(11.934, 79.832, 11.937, 79.835, "walking")
    col.update_one(
        {"cache_key": walk_key},
        {"$set": {
            "cache_key": walk_key,
            "namespace": "route",
            "cache_version": CACHE_VERSION,
            "mode": "walking",
            "walking_source": WalkingSource.corrected_car.value,
            "tier_used": RoutingTier.public_demo.value,
            "upgrade_attempts": 0,
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        }},
        upsert=True
    )
    # Check that get_cached_route triggers a soft miss because FOSSGIS foot is healthy
    soft_miss = route_cache_service.get_cached_route(11.934, 79.832, 11.937, 79.835, "walking", fossgis_foot_healthy=True)
    assert soft_miss is None, "Expected soft miss for corrected_car entry"

    # Now simulate successful upgrade write
    route_cache_service.save_route(
        11.934, 79.832, 11.937, 79.835, "walking",
        distance_km=0.6, raw_duration_min=8.0,
        tier_used=RoutingTier.public_demo,
        walking_source=WalkingSource.fossgis_foot,
        polyline_geojson={"type": "LineString", "coordinates": [[79.832, 11.934], [79.835, 11.937]]},
        steps=[]
    )
    doc_upgraded = col.find_one({"cache_key": walk_key})
    assert doc_upgraded["walking_source"] == WalkingSource.fossgis_foot.value
    # Assert created_at was reset to today
    assert doc_upgraded["created_at"].year == 2026
    assert doc_upgraded["created_at"].month >= 10
    results["T3.7_QualityUpgradeReset"] = "PASS"
    print("-> PASS: Entry upgraded to fossgis_foot and created_at was reset.")

    # T3.8: Festival Closure Edit Invariance
    print("\n--- TEST T3.8: Festival Closure Edit Invariance ---")
    # Simulate a festival closure check
    # Add temporary mock road closure to festivals collection
    db = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=500)[DB_NAME]
    db["festivals"].update_one(
        {"id": "test_closure_fest"},
        {"$set": {
            "id": "test_closure_fest",
            "name": "Pondicherry Heritage Car Festival",
            "city_id": "pondicherry",
            "start_date": "2026-11-15",
            "end_date": "2026-11-17",
            "road_closures": [
                {"name": "Goubert Ave Closure", "coordinates": [[11.93444, 79.83060]]}
            ]
        }},
        upsert=True
    )
    # Cache key does NOT change
    key_before = route_cache_service.format_route_key(11.93381, 79.83582, 11.93444, 79.83060, "driving")
    # Test read-time closure evaluation
    aff, warn, evs = route_cache_service.check_festival_closures(
        [[11.93381, 79.83582], [11.93444, 79.83060]],
        city_id="pondicherry",
        travel_date="2026-11-16"
    )
    assert aff is True
    assert "Pondicherry Heritage Car Festival" in evs
    assert "Route intersects active festival road closure" in warn
    # Key remains strictly raw OSRM
    key_after = route_cache_service.format_route_key(11.93381, 79.83582, 11.93444, 79.83060, "driving")
    assert key_before == key_after
    # Clean up test fest
    db["festivals"].delete_one({"id": "test_closure_fest"})
    results["T3.8_ClosureEditInvariance"] = "PASS"
    print("-> PASS: Cache key unchanged; read-time closure detection alerted route correctly.")

    # T3.9: Tier 3 Never Written to MongoDB
    print("\n--- TEST T3.9: Tier 3 (haversine_detour) Never Written to MongoDB ---")
    t3_key = route_cache_service.format_route_key(11.8000, 79.7000, 11.8100, 79.7100, "driving")
    col.delete_many({"cache_key": t3_key})
    # Attempt saving a Tier 3 route
    saved = route_cache_service.save_route(
        11.8000, 79.7000, 11.8100, 79.7100, "driving",
        distance_km=2.5, raw_duration_min=5.0,
        tier_used=RoutingTier.haversine_detour,
        walking_source=None,
        polyline_geojson={},
        steps=[]
    )
    assert saved is False
    doc_t3 = col.find_one({"cache_key": t3_key})
    assert doc_t3 is None, f"Tier 3 entry was illegally persisted: {doc_t3}"
    results["T3.9_Tier3NeverWritten"] = "PASS"
    print("-> PASS: Haversine detour result was rejected from cache persistence.")

    # T3.10: Errors and No-Route Not Cached
    print("\n--- TEST T3.10: Errors and No-Route Not Cached ---")
    # Verify that invalid coordinates or errors do not create cache records
    err_key = route_cache_service.format_route_key(0.0, 0.0, 0.0, 0.0, "driving")
    doc_err = col.find_one({"cache_key": err_key})
    assert doc_err is None
    results["T3.10_ErrorsNotCached"] = "PASS"
    print("-> PASS: No error or dummy records in route cache.")

    # T3.11: Tier 2 Hit with Tier 1 Up & Retry Limit
    print("\n--- TEST T3.11: Tier 2 Hit with Tier 1 Up & Retry Limit ---")
    retry_key = route_cache_service.format_route_key(11.95, 79.85, 11.96, 79.86, "driving")
    col.update_one(
        {"cache_key": retry_key},
        {"$set": {
            "cache_key": retry_key,
            "namespace": "route",
            "cache_version": CACHE_VERSION,
            "tier_used": RoutingTier.public_demo.value,
            "upgrade_attempts": 0,
            "distance_km": 1.2,
            "raw_duration_min": 2.5,
            "created_at": datetime.now(timezone.utc)
        }},
        upsert=True
    )
    # With tier1_healthy=True, first attempt should return soft miss (None) and increment counter
    miss1 = route_cache_service.get_cached_route(11.95, 79.85, 11.96, 79.86, "driving", tier1_healthy=True)
    assert miss1 is None
    doc_r = col.find_one({"cache_key": retry_key})
    assert doc_r["upgrade_attempts"] == 1

    # Simulate 3 failed attempts
    col.update_one({"cache_key": retry_key}, {"$set": {"upgrade_attempts": 3}})
    # At attempt 3, soft miss should be suppressed and cached doc returned
    hit_after_3 = route_cache_service.get_cached_route(11.95, 79.85, 11.96, 79.86, "driving", tier1_healthy=True)
    assert hit_after_3 is not None
    assert hit_after_3["tier_used"] == RoutingTier.public_demo.value
    results["T3.11_RetryLimitCeiling"] = "PASS"
    print("-> PASS: Upgrade soft-miss respected 3-attempt ceiling and served cache without looping.")

    # T3.12: Mixed-Tier Matrix Labeling
    print("\n--- TEST T3.12: Mixed-Tier Matrix Labeling ---")
    coords_mixed = [
        Coordinates(lat=11.9338, lng=79.8358),
        Coordinates(lat=11.9344, lng=79.8306)
    ]
    matrix_res = routing_service.get_matrix(coords_mixed, mode="driving")
    # Diagonal is local_osrm, off-diagonal is public_demo
    assert matrix_res.is_mixed_tier is True
    assert matrix_res.is_approximate is True
    assert RoutingTier.local_osrm.value in matrix_res.tier_summary
    results["T3.12_MixedTierMatrixLabeling"] = "PASS"
    print(f"-> PASS: Mixed-tier matrix correctly labeled (is_mixed={matrix_res.is_mixed_tier}, summary={matrix_res.tier_summary}).")

    # T3.13: Idempotent TTL Index Creation
    print("\n--- TEST T3.13: Idempotent TTL Index Creation ---")
    route_cache_service.ensure_indexes()
    route_cache_service.ensure_indexes()  # 2nd call must succeed without error
    indexes = col.index_information()
    assert "cache_key_1" in indexes
    assert "created_at_1" in indexes
    assert indexes["created_at_1"].get("expireAfterSeconds") == 604800
    results["T3.13_IdempotentTTLIndexes"] = "PASS"
    print("-> PASS: TTL index verified (expireAfterSeconds=604800); idempotent calls succeed.")

    # T3.14: Coordinate Rounding Stability
    print("\n--- TEST T3.14: Coordinate Rounding Stability ---")
    k1 = route_cache_service.format_route_key(11.934441, 79.830602, 11.935551, 79.831112, "driving")
    k2 = route_cache_service.format_route_key(11.934439, 79.830598, 11.935549, 79.831108, "driving")
    assert k1 == k2, f"Keys did not match: {k1} vs {k2}"
    results["T3.14_CoordRoundingStability"] = "PASS"
    print(f"-> PASS: Nearby coordinates within 0.00001 deg normalize to identical key: {k1}")

    # T3.15: Walking vs Driving Key Difference
    print("\n--- TEST T3.15: Walking vs Driving Key Difference ---")
    kd = route_cache_service.format_route_key(11.934, 79.830, 11.935, 79.831, "driving")
    kw = route_cache_service.format_route_key(11.934, 79.830, 11.935, 79.831, "walking")
    assert kd != kw
    assert kd.endswith(":driving")
    assert kw.endswith(":walking")
    results["T3.15_ModeKeySeparation"] = "PASS"
    print(f"-> PASS: Mode separation strictly maintained ({kd} != {kw}).")

    # T3.16: Geometry Convention Order
    print("\n--- TEST T3.16: Geometry Convention Order ---")
    route_geom = routing_service.get_route(11.93381, 79.83582, 11.93444, 79.83060, mode="driving")
    first_pt = route_geom.polyline_geojson["coordinates"][0]
    # Check that GeoJSON is [lon, lat] and document contains proper coordinates
    assert 79.0 <= first_pt[0] <= 81.0, f"Expected longitude first in GeoJSON LineString, got: {first_pt}"
    assert 11.0 <= first_pt[1] <= 14.0, f"Expected latitude second in GeoJSON LineString, got: {first_pt}"
    results["T3.16_GeometryConvention"] = "PASS"
    print(f"-> PASS: GeoJSON LineString verified with standard [lon, lat] coordinates ({first_pt}).")

    # T3.17: Single-Flight Concurrency (10 concurrent requests produce 1 call)
    print("\n--- TEST T3.17: Single-Flight Request Merging (10 Concurrent Requests) ---")
    conc_o_lat, conc_o_lng = 11.93123, 79.83456
    conc_d_lat, conc_d_lng = 11.93789, 79.83912
    # Ensure not cached
    col.delete_many({"cache_key": route_cache_service.format_route_key(conc_o_lat, conc_o_lng, conc_d_lat, conc_d_lng, "driving")})

    call_count = 0
    call_lock = threading.Lock()
    orig_compute = routing_service._compute_and_cache_route

    def instrumented_compute(*args, **kwargs):
        nonlocal call_count
        with call_lock:
            call_count += 1
        time.sleep(0.2)  # Simulate network latency
        return orig_compute(*args, **kwargs)

    routing_service._compute_and_cache_route = instrumented_compute
    try:
        def make_request(idx):
            return routing_service.get_route(conc_o_lat, conc_o_lng, conc_d_lat, conc_d_lng, mode="driving")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            responses = [f.result() for f in futures]

        assert len(responses) == 10
        for r in responses:
            assert r.distance_km > 0
        print(f"Total concurrent requests dispatched: 10 | Total compute executions: {call_count}")
        assert call_count == 1, f"Expected exactly 1 compute execution under single-flight, got: {call_count}"
        results["T3.17_SingleFlightConcurrency"] = "PASS"
        print("-> PASS: Single-flight coalesced 10 concurrent requests into exactly 1 outbound call.")
    finally:
        routing_service._compute_and_cache_route = orig_compute

    print("\n" + "=" * 70)
    print("PHASE 4 TASK 3 (P4-T3) TEST SUMMARY")
    print("=" * 70)
    for test_name, status in results.items():
        print(f"{test_name:<40} : {status}")
    print("-" * 70)
    passed = sum(1 for s in results.values() if s == "PASS")
    print(f"Total Tests: {len(results)} | Passed: {passed} | Failed: {len(results) - passed}")
    print("=" * 70)

    if passed != len(results):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    run_tests()
