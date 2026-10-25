import requests

BASE_URL = 'http://localhost:8000/api/v1'

# Test 1: What happens if we pass integer age?
for age_val in [22, 25, 26, 33, 40, 41, 50, 60, 61, 68]:
    r = requests.post(f'{BASE_URL}/recommendations', json={
        'city_id': 'pondicherry',
        'age_group': age_val,
        'dietary_preference': 'all',
        'budget_tier': 'moderate'
    })
    print(f"Passed integer age {age_val}: Status {r.status_code}")

# Test 2: Passing with enum strings (young_adult, adult, family, senior)
for grp in ['young_adult', 'adult', 'family', 'senior']:
    r = requests.post(f'{BASE_URL}/recommendations', json={
        'city_id': 'pondicherry',
        'age_group': grp,
        'dietary_preference': 'all',
        'budget_tier': 'moderate'
    })
    data = r.json()
    top_3 = [(item['place']['name'], item['match_score']) for item in data['ranked_places'][:3]]
    print(f"\nGroup '{grp}': Top 3:")
    for name, sc in top_3:
        print(f"  {name}: {sc}")
