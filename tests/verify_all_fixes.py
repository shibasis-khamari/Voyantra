import requests
import json
import codecs
import sys

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

BASE_URL = 'http://127.0.0.1:8000/api/v1'

def run_all_verifications():
    results = {}
    print("=" * 60)
    print("RUNNING VOYANTRA FULL REGRESSION VERIFICATION SUITE")
    print("=" * 60)

    # ---------------------------------------------------------
    # STEP 0.1: MongoDB Collections Document Counts
    # ---------------------------------------------------------
    from pathlib import Path
    sys.path.insert(0, str(Path(r"e:\Voyantra\backend").resolve()))
    from app.core.database import db
    col_names = db.db.list_collection_names() if db.db is not None else []
    u_cnt = db.get_collection('users').count_documents({})
    p_cnt = db.get_collection('places').count_documents({})
    h_cnt = db.get_collection('hotels').count_documents({})
    f_cnt = db.get_collection('festivals').count_documents({})
    
    pass_0_1 = (all(c in col_names for c in ['users', 'places', 'hotels', 'festivals']) 
                and u_cnt >= 2 and p_cnt >= 14 and h_cnt >= 6 and f_cnt >= 8)
    results['0.1_mongo_collections'] = (
        "PASS" if pass_0_1 else "FAIL", 
        f"Collections: {col_names}, users={u_cnt}, places={p_cnt}, hotels={h_cnt}, festivals={f_cnt}"
    )

    # ---------------------------------------------------------
    # 1.1 & 1.2: Login and Signed JWT Tokens
    # ---------------------------------------------------------
    r_user = requests.post(f"{BASE_URL}/auth/login", json={"email": "user@voyantra.com", "password": "user123"})
    user_token = r_user.json().get("access_token") if r_user.ok else None
    user_role = r_user.json().get("user", {}).get("role") if r_user.ok else None

    r_admin = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@voyantra.com", "password": "admin123"})
    admin_token = r_admin.json().get("access_token") if r_admin.ok else None
    admin_role = r_admin.json().get("user", {}).get("role") if r_admin.ok else None

    pass_1_1 = (r_user.status_code == 200 and user_role == "user" and user_token is not None and user_token.startswith("ey"))
    pass_1_2 = (r_admin.status_code == 200 and admin_role == "admin" and admin_token is not None and admin_token.startswith("ey"))
    results['1.1_user_login'] = ("PASS" if pass_1_1 else "FAIL", f"Status: {r_user.status_code}, Role: {user_role}, JWT: {bool(user_token)}")
    results['1.2_admin_login'] = ("PASS" if pass_1_2 else "FAIL", f"Status: {r_admin.status_code}, Role: {admin_role}, JWT: {bool(admin_token)}")

    # ---------------------------------------------------------
    # 1.5: Passwords Hashed with Bcrypt in MongoDB
    # ---------------------------------------------------------
    docs = list(db.get_collection('users').find())
    all_hashed = all(d.get("password", "").startswith("$2b$") or d.get("password", "").startswith("$2a$") for d in docs)
    results['1.5_password_hashing'] = ("PASS" if all_hashed else "FAIL", f"Total users inspected: {len(docs)}, All hashed: {all_hashed}")

    # ---------------------------------------------------------
    # 1.6 & S1: Ingestion RBAC Protection
    # ---------------------------------------------------------
    # No token -> 401
    r_no_tok = requests.post(f"{BASE_URL}/places/fetch-from-internet?city_name=Pondicherry")
    # User token -> 403
    r_usr_tok = requests.post(
        f"{BASE_URL}/places/fetch-from-internet?city_name=Pondicherry",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    # Admin token -> 200
    r_adm_tok = requests.post(
        f"{BASE_URL}/places/fetch-from-internet?city_name=Pondicherry",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    pass_1_6 = (r_no_tok.status_code == 401 and r_usr_tok.status_code == 403 and r_adm_tok.status_code == 200)
    results['1.6_ingestion_rbac'] = (
        "PASS" if pass_1_6 else "FAIL",
        f"No Token: {r_no_tok.status_code} (Exp 401), User Token: {r_usr_tok.status_code} (Exp 403), Admin: {r_adm_tok.status_code} (Exp 200)"
    )

    # ---------------------------------------------------------
    # 1.7: Query Alias city=Chennai and city=Pondicherry
    # ---------------------------------------------------------
    r_pondy = requests.get(f"{BASE_URL}/places?city=Pondicherry")
    r_chennai = requests.get(f"{BASE_URL}/places?city=Chennai")
    pondy_places = r_pondy.json() if r_pondy.ok else []
    chennai_places = r_chennai.json() if r_chennai.ok else []

    all_p_pondy = all(p.get("city_id") == "pondicherry" for p in pondy_places)
    all_p_chennai = all(p.get("city_id") == "chennai" for p in chennai_places)
    pass_1_7 = (r_pondy.ok and r_chennai.ok and len(pondy_places) > 0 and len(chennai_places) > 0 and all_p_pondy and all_p_chennai)
    results['1.7_city_query_alias'] = (
        "PASS" if pass_1_7 else "FAIL",
        f"Pondy count: {len(pondy_places)} (all pondy: {all_p_pondy}), Chennai count: {len(chennai_places)} (all chennai: {all_p_chennai})"
    )

    # ---------------------------------------------------------
    # 1.8: Strict Dietary Hard Filtering
    # ---------------------------------------------------------
    r_jain = requests.get(f"{BASE_URL}/places?city=Pondicherry&dietary=pure_veg_jain")
    jain_dining = [p for p in r_jain.json() if p.get("category") in ["cafe", "dining"]]
    no_jain_leaks = all("pure_veg_jain" in p.get("dietary_options", []) for p in jain_dining)

    r_halal = requests.get(f"{BASE_URL}/places?city=Pondicherry&dietary=halal")
    halal_dining = [p for p in r_halal.json() if p.get("category") in ["cafe", "dining"]]
    no_halal_leaks = all("halal" in p.get("dietary_options", []) for p in halal_dining)

    pass_1_8 = (no_jain_leaks and no_halal_leaks)
    results['1.8_strict_dietary_filter'] = (
        "PASS" if pass_1_8 else "FAIL",
        f"Jain dining returned: {[p['name'] for p in jain_dining]}, No leaks: {no_jain_leaks}; Halal dining: {[p['name'] for p in halal_dining]}, No leaks: {no_halal_leaks}"
    )

    # ---------------------------------------------------------
    # 1.10: MatchScore Formula Verification
    # ---------------------------------------------------------
    # [(W_category*0.45)+(C_budget*0.25)+(F_dietary*0.20)+(A_accessibility*0.10)]*100
    r_rec = requests.post(f"{BASE_URL}/recommendations", json={
        "city_id": "pondicherry",
        "age_group": "young_adult",
        "dietary_preference": "vegetarian",
        "budget_tier": "moderate"
    })
    rec_items = r_rec.json().get("ranked_places", [])
    formula_matches = []
    for item in rec_items[:3]:
        cs = item.get("component_scores")
        api_score = item.get("match_score")
        if cs:
            expected = round(((cs["w_category"] * 0.45) + (cs["c_budget"] * 0.25) + (cs["f_dietary"] * 0.20) + (cs["a_accessibility"] * 0.10)) * 100, 1)
            diff = abs(expected - api_score)
            formula_matches.append(diff <= 0.2)
    pass_1_10 = (len(formula_matches) >= 3 and all(formula_matches))
    results['1.10_match_score_formula'] = (
        "PASS" if pass_1_10 else "FAIL",
        f"Checked top 3 places against linear equation: {formula_matches}"
    )

    # ---------------------------------------------------------
    # 1.12: Age Matrix & Boundary 60
    # ---------------------------------------------------------
    age_statuses = {}
    for age_v in [22, 25, 26, 33, 40, 41, 50, 60, 61, 68]:
        r_age = requests.post(f"{BASE_URL}/recommendations", json={
            "city_id": "pondicherry",
            "age": age_v,
            "dietary_preference": "all"
        })
        app_grp = r_age.json().get("applied_preferences", {}).get("age_group") if r_age.ok else None
        age_statuses[age_v] = (r_age.status_code, app_grp)
    
    pass_1_12 = (
        age_statuses[25][1] == "young_adult" and
        age_statuses[26][1] == "adult" and
        age_statuses[40][1] == "adult" and
        age_statuses[41][1] == "family" and
        age_statuses[60][1] == "senior" and
        age_statuses[61][1] == "senior" and
        all(s[0] == 200 for s in age_statuses.values())
    )
    results['1.12_age_matrix_and_boundaries'] = (
        "PASS" if pass_1_12 else "FAIL",
        f"Age mappings: 25->{age_statuses[25][1]}, 26->{age_statuses[26][1]}, 40->{age_statuses[40][1]}, 41->{age_statuses[41][1]}, 60->{age_statuses[60][1]}, 61->{age_statuses[61][1]}"
    )

    # ---------------------------------------------------------
    # 2.3: Feasibility Reality Checks ("Himalayan Lake", "Eiffel Tower", "Snow Skiing")
    # ---------------------------------------------------------
    r_snow = requests.post(f"{BASE_URL}/recommendations/generate-itinerary", json={
        "city_id": "pondicherry",
        "query_text": "Snow skiing in Pondicherry",
        "duration_days": 1
    }, timeout=45)
    itin_snow = r_snow.json().get("itinerary", {})
    warn_snow = itin_snow.get("has_unavailability_warning") is True

    r_himal = requests.post(f"{BASE_URL}/recommendations/generate-itinerary", json={
        "city_id": "chennai",
        "query_text": "Scuba trip to a Himalayan lake in Chennai",
        "duration_days": 1
    }, timeout=45)
    itin_himal = r_himal.json().get("itinerary", {})
    warn_himal = itin_himal.get("has_unavailability_warning") is True

    r_paris = requests.post(f"{BASE_URL}/recommendations/generate-itinerary", json={
        "city_id": "pondicherry",
        "query_text": "Visit Paris Eiffel Tower",
        "duration_days": 1
    }, timeout=45)
    itin_paris = r_paris.json().get("itinerary", {})
    warn_paris = itin_paris.get("has_unavailability_warning") is True

    pass_2_3 = (warn_snow and warn_himal and warn_paris)
    results['2.3_feasibility_reality_checks'] = (
        "PASS" if pass_2_3 else "FAIL",
        f"Snow warning: {warn_snow}, Himalayan warning: {warn_himal}, Eiffel warning: {warn_paris}"
    )

    # ---------------------------------------------------------
    # 2.4: Geographic Boundary (Reject Bangalore)
    # ---------------------------------------------------------
    r_bglr_city = requests.post(f"{BASE_URL}/recommendations/generate-itinerary", json={
        "city_id": "bangalore",
        "query_text": "2-day trip to Lalbagh botanical garden",
        "duration_days": 2
    })
    r_bglr_query = requests.post(f"{BASE_URL}/recommendations/generate-itinerary", json={
        "city_id": "pondicherry",
        "query_text": "Plan a trip to Bangalore",
        "duration_days": 2
    })
    pass_2_4 = (r_bglr_city.status_code == 400 and r_bglr_query.status_code == 400)
    results['2.4_geographic_boundary_rejection'] = (
        "PASS" if pass_2_4 else "FAIL",
        f"city_id=bangalore: {r_bglr_city.status_code} (Exp 400), query='trip to Bangalore': {r_bglr_query.status_code} (Exp 400)"
    )

    # ---------------------------------------------------------
    # 2.5: Refinement Day 1 Immutability
    # ---------------------------------------------------------
    init_req = requests.post(f"{BASE_URL}/recommendations/generate-itinerary", json={
        "city_id": "pondicherry",
        "query_text": "2-day trip to Pondicherry, vegetarian, mid budget, love beaches and heritage",
        "duration_days": 2
    }, timeout=45)
    itin_init = init_req.json().get("itinerary", {})
    day1_before = itin_init.get("days", [])[0] if itin_init.get("days") else {}

    refine_req = requests.post(f"{BASE_URL}/recommendations/generate-itinerary", json={
        "city_id": "pondicherry",
        "query_text": "Make Day 2 more relaxed",
        "duration_days": 2,
        "existing_days": itin_init.get("days")
    }, timeout=45)
    itin_ref = refine_req.json().get("itinerary", {})
    day1_after = itin_ref.get("days", [])[0] if itin_ref.get("days") else {}
    day2_after = itin_ref.get("days", [])[1] if len(itin_ref.get("days")) > 1 else {}

    day1_identical = (day1_before.get("morning", {}).get("place_name") == day1_after.get("morning", {}).get("place_name") and
                      day1_before.get("afternoon", {}).get("place_name") == day1_after.get("afternoon", {}).get("place_name") and
                      day1_before.get("evening", {}).get("place_name") == day1_after.get("evening", {}).get("place_name"))
    pass_2_5 = (day1_identical and "relaxed" in day2_after.get("theme", "").lower())
    results['2.5_refinement_day1_immutability'] = (
        "PASS" if pass_2_5 else "FAIL",
        f"Day 1 identical: {day1_identical}, Day 2 theme: '{day2_after.get('theme')}'"
    )

    # ---------------------------------------------------------
    # 2.6: Empty Prompt Validation
    # ---------------------------------------------------------
    r_empty = requests.post(f"{BASE_URL}/recommendations/generate-itinerary", json={
        "city_id": "pondicherry",
        "query_text": "   ",
        "duration_days": 2
    })
    pass_2_6 = (r_empty.status_code == 422)
    results['2.6_empty_prompt_422'] = ("PASS" if pass_2_6 else "FAIL", f"Status: {r_empty.status_code} (Exp 422)")

    # ---------------------------------------------------------
    # 3.8 & 3.9: Crowd 404 for Invalid Place & Invalid City
    # ---------------------------------------------------------
    r_cr_place = requests.get(f"{BASE_URL}/crowd/place/non-existent-place-999")
    r_cr_city = requests.get(f"{BASE_URL}/crowd/city/unknown-city-xyz")
    pass_3_8_9 = (r_cr_place.status_code == 404 and r_cr_city.status_code == 404)
    results['3.8_3.9_crowd_404_handling'] = (
        "PASS" if pass_3_8_9 else "FAIL",
        f"Invalid Place: {r_cr_place.status_code} (Exp 404), Invalid City: {r_cr_city.status_code} (Exp 404)"
    )

    # ---------------------------------------------------------
    # 3.10 & 3.11: Festivals City Alias & Schema
    # ---------------------------------------------------------
    r_f_pondy = requests.get(f"{BASE_URL}/festivals?city=Pondicherry")
    r_f_che = requests.get(f"{BASE_URL}/festivals?city=Chennai")
    f_p_data = r_f_pondy.json() if r_f_pondy.ok else []
    f_c_data = r_f_che.json() if r_f_che.ok else []

    p_has_fields = all(all(k in f for k in ['id', 'name', 'month_day_start', 'month_day_end', 'affected_streets', 'procession_routes', 'closure_alerts']) for f in f_p_data)
    pass_3_10 = (r_f_pondy.ok and r_f_che.ok and len(f_p_data) > 0 and len(f_c_data) > 0 and p_has_fields)
    results['3.10_festivals_schema_and_city_alias'] = (
        "PASS" if pass_3_10 else "FAIL",
        f"Pondy count: {len(f_p_data)}, Chennai count: {len(f_c_data)}, Has required schema keys: {p_has_fields}"
    )

    # ---------------------------------------------------------
    # 3.12: Admin Festival Management
    # ---------------------------------------------------------
    new_fest = {
        "city_id": "pondicherry",
        "name": "French Heritage Music Carnival",
        "month_day_start": "07-14",
        "month_day_end": "07-16",
        "affected_areas": ["White Town", "Alliance Francaise"],
        "advisory_level": "Peak Tourist Crowd"
    }
    r_f_user = requests.post(f"{BASE_URL}/festivals", json=new_fest, headers={"Authorization": f"Bearer {user_token}"})
    r_f_admin = requests.post(f"{BASE_URL}/festivals", json=new_fest, headers={"Authorization": f"Bearer {admin_token}"})
    
    pass_3_12 = (r_f_user.status_code == 403 and r_f_admin.status_code == 201)
    results['3.12_admin_festival_crud'] = (
        "PASS" if pass_3_12 else "FAIL",
        f"User Token: {r_f_user.status_code} (Exp 403), Admin Token: {r_f_admin.status_code} (Exp 201)"
    )

    # ---------------------------------------------------------
    # S4: Gemini Endpoint Rate Limiting
    # ---------------------------------------------------------
    statuses = []
    for _ in range(12):
        r_rl = requests.post(f"{BASE_URL}/recommendations/generate-itinerary", json={
            "city_id": "pondicherry",
            "query_text": "quick rate test",
            "duration_days": 1
        })
        statuses.append(r_rl.status_code)
    got_429 = 429 in statuses
    results['S4_gemini_rate_limiting'] = (
        "PASS" if got_429 else "FAIL",
        f"Sequence of 12 requests returned: {statuses}, 429 observed: {got_429}"
    )

    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    for test_name, (status, detail) in results.items():
        icon = "[PASS]" if status == "PASS" else "[FAIL]"
        print(f"{icon} {test_name}: {status}")
        print(f"      {detail}")

    all_passed = all(status == "PASS" for status, _ in results.values())
    print("\nOVERALL STATUS:", "100% PASS!" if all_passed else "SOME TESTS FAILED")

if __name__ == '__main__':
    run_all_verifications()
