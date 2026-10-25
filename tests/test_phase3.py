import requests
import json
import sys

# Ensure utf-8 stdout
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

BASE_URL = 'http://localhost:8000/api/v1'

print("=== 3.1: Crowd Endpoint Schema & Fields ===")
r1 = requests.get(f'{BASE_URL}/crowd/place/pondy-01?city_id=pondicherry')
print("Status code:", r1.status_code)
d1 = r1.json()
print("Density %:", d1.get('crowd_density_pct'))
print("Crowd level:", d1.get('crowd_level'))
print("Status badge:", d1.get('status_badge'))
print("Quiet window:", d1.get('quiet_window'))
print("Drivers:", d1.get('drivers'))
curve = d1.get('hourly_curve', [])
print("Hourly curve hours count:", len(curve), f"Hours range: {curve[0]['hour'] if curve else None} to {curve[-1]['hour'] if curve else None}")

print("\n=== 3.2: Time-of-day Rules ===")
neutral_date = "2026-10-14"
b_18 = requests.get(f'{BASE_URL}/crowd/place/pondy-01?city_id=pondicherry&target_date={neutral_date}&hour=18').json()
b_10 = requests.get(f'{BASE_URL}/crowd/place/pondy-01?city_id=pondicherry&target_date={neutral_date}&hour=10').json()
print(f"Beach: 6 PM ({b_18['crowd_density_pct']}%) vs 10 AM ({b_10['crowd_density_pct']}%) -> 6 PM > 10 AM?: {b_18['crowd_density_pct'] > b_10['crowd_density_pct']}")

t_7 = requests.get(f'{BASE_URL}/crowd/place/pondy-12?city_id=pondicherry&target_date={neutral_date}&hour=7').json()
t_18 = requests.get(f'{BASE_URL}/crowd/place/pondy-12?city_id=pondicherry&target_date={neutral_date}&hour=18').json()
t_13 = requests.get(f'{BASE_URL}/crowd/place/pondy-12?city_id=pondicherry&target_date={neutral_date}&hour=13').json()
print(f"Temple: 7 AM ({t_7['crowd_density_pct']}%), 6 PM ({t_18['crowd_density_pct']}%) vs 1 PM ({t_13['crowd_density_pct']}%)")
print(f"  7 AM > 1 PM?: {t_7['crowd_density_pct'] > t_13['crowd_density_pct']}, 6 PM > 1 PM?: {t_18['crowd_density_pct'] > t_13['crowd_density_pct']}")

c_17 = requests.get(f'{BASE_URL}/crowd/place/pondy-06?city_id=pondicherry&target_date={neutral_date}&hour=17').json()
c_11 = requests.get(f'{BASE_URL}/crowd/place/pondy-06?city_id=pondicherry&target_date={neutral_date}&hour=11').json()
print(f"Cafe: 5 PM ({c_17['crowd_density_pct']}%) vs 11 AM ({c_11['crowd_density_pct']}%) -> 5 PM > 11 AM?: {c_17['crowd_density_pct'] > c_11['crowd_density_pct']}")

print("\n=== 3.3: Weekend Rule (+20%) ===")
sat_date = "2026-10-17"
wed_resp = requests.get(f'{BASE_URL}/crowd/place/pondy-01?city_id=pondicherry&target_date={neutral_date}&hour=18').json()
sat_resp = requests.get(f'{BASE_URL}/crowd/place/pondy-01?city_id=pondicherry&target_date={sat_date}&hour=18').json()
diff_weekend = sat_resp['crowd_density_pct'] - wed_resp['crowd_density_pct']
print(f"Wednesday ({wed_resp['crowd_density_pct']}%) vs Saturday ({sat_resp['crowd_density_pct']}%) -> Diff: +{diff_weekend}%")
print(f"Saturday drivers: {sat_resp['drivers']}")

print("\n=== 3.4: Seasonal Rule (Dec/Jan +15%) ===")
dec_date = "2026-12-16"
dec_resp = requests.get(f'{BASE_URL}/crowd/place/pondy-01?city_id=pondicherry&target_date={dec_date}&hour=18').json()
diff_season = dec_resp['crowd_density_pct'] - wed_resp['crowd_density_pct']
print(f"October ({wed_resp['crowd_density_pct']}%) vs December ({dec_resp['crowd_density_pct']}%) -> Diff: +{diff_season}%")
print(f"December drivers: {dec_resp['drivers']}")

print("\n=== 3.5: Festival Collision Rule (+30%, status Peak) ===")
fests = requests.get(f'{BASE_URL}/festivals?city_id=pondicherry').json()
print(f"Found {len(fests)} festivals for Pondicherry.")

fest_date = "2026-07-14"
fest_resp = requests.get(f'{BASE_URL}/crowd/place/pondy-01?city_id=pondicherry&target_date={fest_date}&hour=18').json()
print(f"Bastille Day at Promenade Beach: density={fest_resp['crowd_density_pct']}%, level={fest_resp['crowd_level']}, status={fest_resp['status_badge']}")
print(f"Drivers: {fest_resp['drivers']}")

print("\n=== 3.6: Stacking & Clamping <= 100% ===")
sat_dec = "2026-12-19"
stack_resp = requests.get(f'{BASE_URL}/crowd/place/pondy-01?city_id=pondicherry&target_date={sat_dec}&hour=18').json()
print(f"Stacked Saturday + December + Sunset: density={stack_resp['crowd_density_pct']}% (clamped <= 100?: {stack_resp['crowd_density_pct'] <= 100})")

print("\n=== 3.8: Invalid place_id, past dates, invalid formats ===")
inv_place = requests.get(f'{BASE_URL}/crowd/place/invalid-place-999?city_id=pondicherry')
print("Invalid place_id status code:", inv_place.status_code, "body:", inv_place.text[:200])

past_date = requests.get(f'{BASE_URL}/crowd/place/pondy-01?city_id=pondicherry&target_date=2020-01-01&hour=10')
print("Past date status code:", past_date.status_code, "density:", past_date.json().get('crowd_density_pct'))

inv_date = requests.get(f'{BASE_URL}/crowd/place/pondy-01?city_id=pondicherry&target_date=invalid-date&hour=10')
print("Invalid date format status code:", inv_date.status_code, "density:", inv_date.json().get('crowd_density_pct'))

print("\n=== 3.9: City Congestion Index ===")
city_p = requests.get(f'{BASE_URL}/crowd/city/pondicherry')
print("Pondicherry city crowd index status:", city_p.status_code, "data:", city_p.json())

city_c = requests.get(f'{BASE_URL}/crowd/city/chennai')
print("Chennai city crowd index status:", city_c.status_code, "data:", city_c.json())

inv_city = requests.get(f'{BASE_URL}/crowd/city/invalid_city')
print("Invalid city status code:", inv_city.status_code, "data:", inv_city.text[:200])
