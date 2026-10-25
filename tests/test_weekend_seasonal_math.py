import requests

BASE_URL = 'http://localhost:8000/api/v1'

# Pick a medium-crowd place, say Auroville (pondy-02) or Nature (chennai-05) at 10 AM
# Wednesday: 2026-10-14 vs Saturday: 2026-10-17 at 10 AM
wed = requests.get(f'{BASE_URL}/crowd/place/pondy-02?city_id=pondicherry&target_date=2026-10-14&hour=10').json()
sat = requests.get(f'{BASE_URL}/crowd/place/pondy-02?city_id=pondicherry&target_date=2026-10-17&hour=10').json()
print("Wednesday 10 AM:", wed['crowd_density_pct'], "Saturday 10 AM:", sat['crowd_density_pct'], "Diff:", sat['crowd_density_pct'] - wed['crowd_density_pct'])

# Seasonal: Oct 14 vs Dec 16 at 10 AM
dec = requests.get(f'{BASE_URL}/crowd/place/pondy-02?city_id=pondicherry&target_date=2026-12-16&hour=10').json()
print("October 10 AM:", wed['crowd_density_pct'], "December 10 AM:", dec['crowd_density_pct'], "Diff:", dec['crowd_density_pct'] - wed['crowd_density_pct'])
