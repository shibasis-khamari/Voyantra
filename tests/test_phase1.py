import requests
import json

BASE_URL = 'http://localhost:8000/api/v1'

def test_1_10():
    payload = {
        'city_id': 'pondicherry',
        'age_group': 'young_adult',
        'dietary_preference': 'vegetarian',
        'budget_tier': 'moderate',
        'interests': ['beach', 'cafe']
    }
    r = requests.post(f'{BASE_URL}/recommendations', json=payload)
    data = r.json()
    print('Total results:', data['total_results'])
    for item in data['ranked_places']:
        p = item['place']
        print(f"Name: {p['name']} | Category: {p['category']} | Budget: {p['budget_tier']} | Score: {item['match_score']}")
        print(f"  Reasons: {item['match_reasons']}")

if __name__ == '__main__':
    test_1_10()
