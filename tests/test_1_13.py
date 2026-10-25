import requests

BASE_URL = 'http://localhost:8000/api/v1'

# 1. Recommendation endpoint with conflicting diet + budget
r_rec = requests.post(f'{BASE_URL}/recommendations', json={
    'city_id': 'pondicherry',
    'dietary_preference': 'kosher',
    'budget_tier': 'budget'
})
print('Rec with kosher + budget status:', r_rec.status_code)
if r_rec.status_code == 200:
    data = r_rec.json()
    print('Total ranked:', data['total_results'])
    # Check lowest and highest scores
    scores = [item['match_score'] for item in data['ranked_places']]
    print('Scores range:', min(scores), 'to', max(scores))
else:
    print('Response:', r_rec.text)

# 2. Places filter with conflicting diet + budget
r_places = requests.get(f'{BASE_URL}/places?city_id=pondicherry&dietary=kosher&budget=budget')
print('Places filter with kosher + budget status:', r_places.status_code)
if r_places.status_code == 200:
    print('Places count:', len(r_places.json()))
else:
    print('Response:', r_places.text)
