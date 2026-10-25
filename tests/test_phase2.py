import requests
import json

BASE_URL = 'http://localhost:8000/api/v1'

# Load real catalog place names
with open('backend/app/data/pondicherry_places.json', 'r', encoding='utf-8') as f:
    pondy_places = json.load(f)
catalog_place_names = {p['name'].lower() for p in pondy_places}

print("=== 2.1: Itinerary Generation ===")
p1 = {
    "city_id": "pondicherry",
    "query_text": "2-day trip to Pondicherry, vegetarian, mid budget, love beaches and heritage",
    "dietary_preference": "vegetarian",
    "duration_days": 2
}
r1 = requests.post(f'{BASE_URL}/recommendations/generate-itinerary', json=p1, timeout=60)
print("Status code:", r1.status_code)
d1 = r1.json()
itinerary = d1.get('itinerary', {})
days = itinerary.get('days', [])
print("Days count:", len(days))
places_scheduled = []
hallucinations = []
veg_violations = []

for d in days:
    print(f"Day {d.get('day_number')}: {d.get('theme')}")
    for slot in ['morning', 'afternoon', 'evening']:
        s_data = d.get(slot, {})
        p_name = s_data.get('place_name')
        places_scheduled.append(p_name)
        print(f"  {slot}: {p_name} | {s_data.get('activity_note')}")
        # Check against catalog
        if not any(cat_name in p_name.lower() or p_name.lower() in cat_name for cat_name in catalog_place_names):
            hallucinations.append(p_name)

print("Places scheduled:", places_scheduled)
print("Hallucinations (not in catalog):", hallucinations)

# 2.2 Intent parsing: POST /recommendations/parse-query
print("\n=== 2.2: Intent Parsing ===")
r2 = requests.post(f'{BASE_URL}/recommendations/parse-query', json={"query_text": "2-day trip to Pondicherry, vegetarian, mid budget, love beaches and heritage"})
print("Parsed intent:", r2.status_code, json.dumps(r2.json(), indent=2))

# 2.3 Reality check
print("\n=== 2.3: Reality checks ===")
weird_prompts = [
    ("Snow skiing in Pondicherry", "pondicherry"),
    ("Scuba trip to a Himalayan lake in Chennai", "chennai"),
    ("Visit Paris Eiffel Tower", "pondicherry")
]
for prompt_text, city in weird_prompts:
    r3 = requests.post(f'{BASE_URL}/recommendations/generate-itinerary', json={
        "city_id": city,
        "query_text": prompt_text,
        "duration_days": 1
    }, timeout=45)
    itin = r3.json().get('itinerary', {})
    has_warn = itin.get('has_unavailability_warning')
    warn_notice = itin.get('unavailability_notice')
    feas_stat = itin.get('feasibility_status')
    print(f"Prompt: '{prompt_text}' -> Warning: {has_warn} | Notice: {warn_notice} | Status: {feas_stat}")

# 2.4 Geographic boundary
print("\n=== 2.4: Geographic boundary ===")
r4 = requests.post(f'{BASE_URL}/recommendations/generate-itinerary', json={
    "city_id": "bangalore",
    "query_text": "Plan a trip to Bangalore",
    "duration_days": 2
}, timeout=45)
print("Bangalore request status:", r4.status_code)
print("Bangalore response:", json.dumps(r4.json(), indent=2)[:400])
