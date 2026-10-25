#!/usr/bin/env python3
"""
VOYANTRA PHASE 6 TEST SUITE: DATA-CALIBRATED SEASONALITY & PROVENANCE INTEGRITY
==============================================================================
Validates:
1. JSON structure and metadata conformance in backend/app/data/seasonality_index.json
2. Chennai calibration against Tamil Nadu Tourism Dept District 3302 records (2022-2024)
3. Pondicherry calibration labeled strictly "2014 survey data, rough prior" (never DES)
4. Deterministic reproducibility of backend/scripts/extract_seasonality.py
5. CrowdService integration across all 12 months for both cities
6. Live API endpoint transparency and drivers breakdown
"""

import sys
import os
import json
import codecs
import subprocess
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")

backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import requests
from app.services.crowd_service import crowd_service

BASE_URL = "http://127.0.0.1:8000/api/v1"
DATA_FILE = backend_path / "app" / "data" / "seasonality_index.json"
SCRIPT_FILE = backend_path / "scripts" / "extract_seasonality.py"

def test_seasonality():
    print("=" * 75)
    print("VOYANTRA PHASE 6: EMPIRICAL SEASONALITY & DATA PROVENANCE TEST SUITE")
    print("=" * 75)

    # -------------------------------------------------------------------------
    # TEST 6.1: JSON Integrity & Metadata
    # -------------------------------------------------------------------------
    print("\n--- TEST 6.1: Seasonality JSON Integrity & Metadata ---")
    assert DATA_FILE.exists(), f"Missing seasonality data file: {DATA_FILE}"
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("metadata", {})
    assert meta.get("schema_version") == "1.0", "Invalid schema version"
    assert "extract_seasonality.py" in meta.get("generator_script", ""), "Invalid generator script"

    # Chennai metadata check
    ch_meta = meta.get("chennai", {})
    assert ch_meta.get("district_code") == "3302", "District code must be 3302 for Chennai"
    assert ch_meta.get("years_analyzed") == [2022, 2023, 2024], "Years analyzed must be 2022-2024"
    assert "Tamil Nadu Tourism Dept" in ch_meta.get("provenance_label", ""), "Chennai provenance label invalid"
    print("-> Chennai metadata: Verified District 3302 (Years 2022-2024).")

    # Pondicherry metadata check
    py_meta = meta.get("pondicherry", {})
    assert py_meta.get("provenance_label") == "2014 survey data, rough prior", \
        f"Pondicherry provenance must be strictly '2014 survey data, rough prior', got: {py_meta.get('provenance_label')}"
    assert "DES" not in py_meta.get("provenance_label", ""), "Must NOT attribute Pondicherry numbers to DES"
    print("-> Pondicherry metadata: Verified strict label '2014 survey data, rough prior'.")
    print("[PASS] Test 6.1: Metadata & Provenance Schema verified.")

    # -------------------------------------------------------------------------
    # TEST 6.2: Chennai District 3302 Calibration
    # -------------------------------------------------------------------------
    print("\n--- TEST 6.2: Chennai Empirical Multipliers (District 3302) ---")
    chennai_months = data["cities"]["chennai"]["months"]
    assert len(chennai_months) == 12, "Must contain exactly 12 months for Chennai"

    ch_mults = [chennai_months[str(m)]["multiplier"] for m in range(1, 13)]
    avg_ch_mult = sum(ch_mults) / 12.0
    print(f"Chennai monthly multipliers: {ch_mults}")
    print(f"Chennai mean multiplier: {avg_ch_mult:.4f}")
    assert 0.98 <= avg_ch_mult <= 1.02, f"Chennai mean multiplier must normalize to ~1.0, got: {avg_ch_mult}"

    # December peak (Margazhi music festival & New Year)
    dec_ch = chennai_months["12"]
    assert dec_ch["multiplier"] >= 1.25, f"Expected December peak >= 1.25, got {dec_ch['multiplier']}"
    assert dec_ch["season_category"] == "Peak", "December should be Peak category"

    # January Pongal
    jan_ch = chennai_months["1"]
    assert jan_ch["multiplier"] >= 1.10, f"Expected January Pongal >= 1.10, got {jan_ch['multiplier']}"

    # Summer Vacation peak (May)
    may_ch = chennai_months["5"]
    assert may_ch["multiplier"] >= 1.08, f"Expected May summer vacation >= 1.08, got {may_ch['multiplier']}"

    # Shoulder / Off-peak (March exams)
    mar_ch = chennai_months["3"]
    assert mar_ch["multiplier"] <= 0.85, f"Expected March exam period <= 0.85, got {mar_ch['multiplier']}"
    print("[PASS] Test 6.2: Chennai District 3302 empirical seasonal pattern verified.")

    # -------------------------------------------------------------------------
    # TEST 6.3: Pondicherry 2014 Prior Calibration
    # -------------------------------------------------------------------------
    print("\n--- TEST 6.3: Pondicherry Empirical Prior (2014 MoT Survey) ---")
    pondy_months = data["cities"]["pondicherry"]["months"]
    assert len(pondy_months) == 12, "Must contain exactly 12 months for Pondicherry"

    py_mults = [pondy_months[str(m)]["multiplier"] for m in range(1, 13)]
    avg_py_mult = sum(py_mults) / 12.0
    print(f"Pondicherry monthly multipliers: {py_mults}")
    print(f"Pondicherry mean multiplier: {avg_py_mult:.4f}")
    assert 0.98 <= avg_py_mult <= 1.02, f"Pondicherry mean multiplier must normalize to ~1.0, got: {avg_py_mult}"

    # December holiday peak
    dec_py = pondy_months["12"]
    assert dec_py["multiplier"] >= 1.30, f"Expected Pondicherry December peak >= 1.30, got {dec_py['multiplier']}"

    # August Aurobindo anniversary & French holiday
    aug_py = pondy_months["8"]
    assert aug_py["multiplier"] >= 1.10, f"Expected Pondicherry August >= 1.10, got {aug_py['multiplier']}"

    # June pre-monsoon shoulder
    jun_py = pondy_months["6"]
    assert jun_py["multiplier"] <= 0.80, f"Expected Pondicherry June <= 0.80, got {jun_py['multiplier']}"
    print("[PASS] Test 6.3: Pondicherry 2014 survey prior calibration verified.")

    # -------------------------------------------------------------------------
    # TEST 6.4: Deterministic Reproducibility
    # -------------------------------------------------------------------------
    print("\n--- TEST 6.4: Reproducibility via extract_seasonality.py ---")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        before_content = json.load(f)

    res = subprocess.run([sys.executable, str(SCRIPT_FILE)], capture_output=True, text=True)
    assert res.returncode == 0, f"Extraction script failed:\n{res.stderr}"

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        after_content = json.load(f)

    # Multipliers and figures must be 100% identical
    assert before_content["cities"] == after_content["cities"], "Non-deterministic seasonality values generated!"
    print("-> Re-extraction run executed cleanly with 100% deterministic output.")
    print("[PASS] Test 6.4: Pipeline reproducibility verified.")

    # -------------------------------------------------------------------------
    # TEST 6.5: CrowdService Integration Across All 12 Months
    # -------------------------------------------------------------------------
    print("\n--- TEST 6.5: CrowdService In-Memory Loading & Accuracy ---")
    for m in range(1, 13):
        # Chennai
        ch_info = crowd_service.get_seasonality_info("chennai", m)
        assert ch_info["multiplier"] == chennai_months[str(m)]["multiplier"], f"Chennai month {m} multiplier mismatch"
        assert ch_info["seasonal_point_adjustment"] == chennai_months[str(m)]["seasonal_point_adjustment"]
        assert "District 3302" in ch_info["provenance_label"]

        # Pondicherry
        py_info = crowd_service.get_seasonality_info("pondicherry", m)
        assert py_info["multiplier"] == pondy_months[str(m)]["multiplier"], f"Pondy month {m} multiplier mismatch"
        assert py_info["seasonal_point_adjustment"] == pondy_months[str(m)]["seasonal_point_adjustment"]
        assert py_info["provenance_label"] == "2014 survey data, rough prior"
    print("-> All 24 city-month tuples accurately reflected in CrowdService without hardcoding.")
    print("[PASS] Test 6.5: CrowdService seasonal calibration verified.")

    # -------------------------------------------------------------------------
    # TEST 6.6: Live API Endpoint & Drivers Transparency
    # -------------------------------------------------------------------------
    print("\n--- TEST 6.6: Live API Endpoint Transparency ---")
    # Fetch a place in Pondicherry
    r_places = requests.get(f"{BASE_URL}/places?city_id=pondicherry").json()
    place_id = r_places[0]["id"]

    # Test December (Peak)
    r_dec = requests.get(f"{BASE_URL}/crowd/place/{place_id}?city_id=pondicherry&target_date=2026-12-25&hour=18").json()
    assert "seasonality" in r_dec, "Missing seasonality block in API response"
    assert r_dec["seasonality"]["multiplier"] == pondy_months["12"]["multiplier"]
    assert any("Seasonality" in d for d in r_dec["drivers"]), "Seasonality driver must be explicitly listed"
    print(f"-> December API output: density {r_dec['crowd_density_pct']}%, seasonality mult {r_dec['seasonality']['multiplier']}")

    # Test June (Low)
    r_jun = requests.get(f"{BASE_URL}/crowd/place/{place_id}?city_id=pondicherry&target_date=2026-06-15&hour=18").json()
    assert r_jun["seasonality"]["multiplier"] == pondy_months["6"]["multiplier"]
    assert r_dec["crowd_density_pct"] > r_jun["crowd_density_pct"], "December crowd must exceed June crowd due to seasonality"
    print(f"-> June API output: density {r_jun['crowd_density_pct']}%, seasonality mult {r_jun['seasonality']['multiplier']}")
    print("[PASS] Test 6.6: Live API endpoint returns calibrated seasonality and provenance.")

    print("\n" + "=" * 75)
    print("ALL PHASE 6 SEASONALITY & PROVENANCE TESTS PASSED (6/6)!")
    print("=" * 75)

if __name__ == "__main__":
    test_seasonality()
