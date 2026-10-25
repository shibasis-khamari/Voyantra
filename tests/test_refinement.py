import requests
import json

BASE_URL = 'http://localhost:8000/api/v1'

# Initial generation
orig_prompt = "2-day trip to Pondicherry, vegetarian, mid budget, love beaches and heritage"
p_init = {
    "city_id": "pondicherry",
    "query_text": orig_prompt,
    "dietary_preference": "vegetarian",
    "duration_days": 2
}
r1 = requests.post(f'{BASE_URL}/recommendations/generate-itinerary', json=p_init, timeout=60)
itin1 = r1.json().get('itinerary', {})
day1_init = itin1.get('days', [])[0] if itin1.get('days') else {}
day2_init = itin1.get('days', [])[1] if len(itin1.get('days')) > 1 else {}

print("Initial Day 1:", day1_init)
print("Initial Day 2:", day2_init)

# Refinement: Make Day 2 more relaxed
refinement_prompt = f'Original request: "{orig_prompt}". FOLLOW-UP REFINEMENT INSTRUCTION: "Make Day 2 more relaxed". Re-synthesize the itinerary days, timings, and dining to satisfy this follow-up update.'
r2 = requests.post(f'{BASE_URL}/recommendations/generate-itinerary', json={
    "city_id": "pondicherry",
    "query_text": refinement_prompt,
    "dietary_preference": "vegetarian",
    "duration_days": 2
}, timeout=60)
itin2 = r2.json().get('itinerary', {})
day1_ref = itin2.get('days', [])[0] if itin2.get('days') else {}
day2_ref = itin2.get('days', [])[1] if len(itin2.get('days')) > 1 else {}

print("\nRefined Day 1:", day1_ref)
print("Refined Day 2:", day2_ref)

# Compare Day 1
day1_unchanged = (day1_init.get('morning', {}).get('place_name') == day1_ref.get('morning', {}).get('place_name') and
                  day1_init.get('afternoon', {}).get('place_name') == day1_ref.get('afternoon', {}).get('place_name') and
                  day1_init.get('evening', {}).get('place_name') == day1_ref.get('evening', {}).get('place_name'))

print("\nDay 1 unchanged?:", day1_unchanged)
