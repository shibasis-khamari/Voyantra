import subprocess
import sys
import os
import time
import codecs
import requests
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "replace")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "replace")

SUITES = [
    ("test_phase3_5.py", "Phase 3.5: Dual-Corridor Geodesic Operating Bounds & UI Detection"),
    ("test_route_validations_and_limits.py", "Phase 4 (P4-T1/T2): Route Validations, 70km Bounds & 30 req/min Rate Limiting"),
    ("test_throttle_and_maxwait.py", "Phase 4 (P4-T2): Global 1 req/s Outbound Throttle & Max-Wait Fallback"),
    ("test_phase4_routes.py", "Phase 4 (P4-T1): 3-Tier Routing Cascade, Pedestrian Calibration & Detour Factor"),
    ("test_phase4_caching.py", "Phase 4 (P4-T3): High-Performance Route Caching, Single-Flight & Key Isolation"),
    ("test_phase4_tsp.py", "Phase 4 (P4-T4/T5): Time-Constrained TSP Solver, Anchor-Locks & Festival Closures"),
    ("test_phase4_e2e_ui.py", "Phase 4 (P4-T6/T7): Playwright E2E UI - Leaflet Navigation & Day Optimizer"),
    ("test_phase5_crowdsource.py", "Phase 5 (P5-T1..T4/T6): 200m Geofenced Footfall, Snapshot Logging & Exponential Decay"),
    ("test_phase5_e2e_ui.py", "Phase 5 (P5-T5): Playwright E2E UI - Live Crowdsourcing Modal & Geofence Rejection"),
    ("test_seasonality_provenance.py", "Phase 6 (P6-T1..T4): Data-Calibrated Seasonality, District 3302 & MoT 2014 Prior")
]

def main():
    print("=" * 80)
    print("VOYANTRA MASTER TEST SUITE: PHASES 3.5, 4, 5 & 6 CONSOLIDATED RUN")
    print("=" * 80)

    # Reset rate limit before starting
    try:
        requests.post("http://127.0.0.1:8000/api/v1/routes/reset-rate-limit", timeout=3)
    except Exception:
        pass

    tests_dir = Path(__file__).parent.resolve()
    results = []
    total_start = time.time()

    for idx, (filename, desc) in enumerate(SUITES, 1):
        test_path = tests_dir / filename
        assert test_path.exists(), f"Suite file missing: {filename}"

        print(f"\n[{idx}/{len(SUITES)}] RUNNING: {filename}")
        print(f"     Description: {desc} ...", flush=True)

        # Reset rate limit before each suite
        try:
            requests.post("http://127.0.0.1:8000/api/v1/routes/reset-rate-limit", timeout=3)
        except Exception:
            pass

        t0 = time.time()
        res = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=True,
            text=True,
            timeout=180,
            encoding="utf-8",
            errors="replace"
        )
        elapsed = time.time() - t0
        passed = (res.returncode == 0)
        status_str = "PASS" if passed else f"FAIL (exit {res.returncode})"

        results.append({
            "file": filename,
            "desc": desc,
            "status": status_str,
            "passed": passed,
            "elapsed": elapsed,
            "stdout": res.stdout,
            "stderr": res.stderr
        })

        print(f"  -> {status_str} in {elapsed:.2f}s")
        if not passed:
            print("  --- ERROR OUTPUT ---")
            print(res.stdout[-600:])
            print(res.stderr[-600:])

    total_time = time.time() - total_start
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = len(results) - passed_count

    print("\n" + "=" * 80)
    print("FINAL CONSOLIDATED TEST SUITE SUMMARY (ALL PHASES)")
    print("=" * 80)
    print(f"{'#':<3} | {'Test Suite':<38} | {'Status':<10} | {'Time (s)':<8}")
    print("-" * 80)
    for idx, r in enumerate(results, 1):
        print(f"{idx:<3} | {r['file']:<38} | {r['status']:<10} | {r['elapsed']:>6.2f}s")
    print("-" * 80)
    print(f"Total Suites: {len(results)} | Passed: {passed_count} | Failed: {failed_count} | Total Time: {total_time:.2f}s")
    print("=" * 80)

    if failed_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
