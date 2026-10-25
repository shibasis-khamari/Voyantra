import sys
import os
import time
import json
import concurrent.futures
import urllib.request
import urllib.error

sys.path.insert(0, "backend")
sys.path.insert(0, os.path.abspath("backend"))

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from app.services.routing_service import routing_service, MAX_THROTTLE_WAIT_SECONDS, TIER2_MIN_REQUEST_INTERVAL

def test_throttle_and_maxwait_direct():
    print("==================================================================")
    print("CONCURRENT TEST: GLOBAL 1 REQ/S OUTBOUND THROTTLE & MAX-WAIT FALLBACK")
    print("==================================================================")

    print(f"\nConfiguration: Throttle interval = {TIER2_MIN_REQUEST_INTERVAL}s, Max wait threshold = {MAX_THROTTLE_WAIT_SECONDS}s")
    print("Firing 10 simultaneous requests to routing_service.get_route...")

    req_data = {
        "origin_lat": 11.934,
        "origin_lng": 79.832,
        "dest_lat": 11.938,
        "dest_lng": 79.834,
        "mode": "driving",
        "city_id": "pondicherry"
    }

    run_offset = round((time.time() * 1000) % 500 * 0.0001, 6)
    def execute_route_call(idx):
        t0 = time.time()
        # Use distinct, uncached coordinates per run to test throttle queue without cache collision
        res = routing_service.get_route(
            origin_lat=round(11.9320 + run_offset + idx * 0.0003, 6),
            origin_lng=round(79.8300 + run_offset + idx * 0.0003, 6),
            dest_lat=round(11.9340 + run_offset + idx * 0.0003, 6),
            dest_lng=round(79.8340 + run_offset + idx * 0.0003, 6),
            mode=req_data["mode"],
            city_id=req_data["city_id"]
        )
        t_taken = time.time() - t0
        return idx, res.tier_used, res.is_approximate, res.approximate_label, t_taken

    start_overall = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(execute_route_call, i) for i in range(10)]
        results = [f.result() for f in futures]
    total_elapsed = time.time() - start_overall

    results.sort(key=lambda x: x[0])

    print(f"\nAll 10 concurrent requests completed in {total_elapsed:.2f}s total:")
    tier2_count = 0
    tier3_fallback_count = 0

    for idx, tier_used, is_approx, approx_label, duration in results:
        print(f"  Req #{idx:02d} -> tier_used: {tier_used:<16} approximate: {str(is_approx):<5} label: '{approx_label}' (latency: {duration:.2f}s)")
        if tier_used == "public_demo":
            tier2_count += 1
        elif tier_used == "haversine_detour":
            tier3_fallback_count += 1

    print(f"\nSummary: Tier 2 (public_demo) = {tier2_count}, Tier 3 (haversine_detour fallback) = {tier3_fallback_count}")
    
    # Assertions:
    # 1. Tier 2 can accept at most requests where wait_needed <= MAX_THROTTLE_WAIT_SECONDS
    assert tier2_count > 0, "At least one request must be served by Tier 2"
    assert tier2_count <= 5, f"Tier 2 admitted {tier2_count} requests, which violates max-wait threshold of {MAX_THROTTLE_WAIT_SECONDS}s"
    
    # 2. Over-quota requests MUST fall back to Tier 3 immediately
    assert tier3_fallback_count >= 5, f"Expected >= 5 Tier 3 fallbacks, got {tier3_fallback_count}"
    
    # 3. None of the requests hung (> 10.0s includes queue wait + network latency headroom)
    assert total_elapsed <= 10.0, f"Total elapsed time {total_elapsed:.2f}s exceeded max threshold"

    print("\n-> PASS: Outbound 1 req/s throttle strictly maintained; surplus concurrent requests gracefully fell back to Tier 3 with approximate label.")
    print("==================================================================")

if __name__ == "__main__":
    test_throttle_and_maxwait_direct()
