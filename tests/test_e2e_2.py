import requests
import json
import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

BASE_URL = 'http://localhost:8000/api/v1'

def test_e2e_2_chennai():
    # 1. Active festivals on Saturday 2026-12-19 in Chennai
    date_str = "2026-12-19"
    r_fest = requests.get(f'{BASE_URL}/festivals/active?city_id=chennai&target_date={date_str}')
    print("Active festivals in Chennai on 2026-12-19:", [f['name'] for f in r_fest.json()])

    # 2. Crowd estimate for Kapaleeshwarar Temple (chennai-02)
    r_crowd = requests.get(f'{BASE_URL}/crowd/place/chennai-02?city_id=chennai&target_date={date_str}&hour=18')
    d_crowd = r_crowd.json()
    print("Kapaleeshwarar Temple Crowd on Saturday in Margazhi:")
    print("  Density:", d_crowd.get('crowd_density_pct'))
    print("  Level:", d_crowd.get('crowd_level'))
    print("  Badge:", d_crowd.get('status_badge'))
    print("  Drivers:", d_crowd.get('drivers'))

    # 3. Generate Itinerary for Chennai on December weekend
    r_itin = requests.post(f'{BASE_URL}/recommendations/generate-itinerary', json={
        "city_id": "chennai",
        "query_text": f"Weekend 2-day cultural trip to Chennai on {date_str} during Margazhi music festival",
        "duration_days": 2
    }, timeout=60)
    d_itin = r_itin.json()
    itin = d_itin.get('itinerary', {})
    print("\nChennai Itinerary:")
    print("  Title:", itin.get('itinerary_title'))
    print("  Feasibility status:", itin.get('feasibility_status'))
    print("  Tips:", itin.get('travel_tips'))
    for d in itin.get('days', []):
        print(f"  Day {d.get('day_number')}: Morning={d.get('morning', {}).get('place_name')}, Afternoon={d.get('afternoon', {}).get('place_name')}, Evening={d.get('evening', {}).get('place_name')}")

if __name__ == '__main__':
    test_e2e_2_chennai()
