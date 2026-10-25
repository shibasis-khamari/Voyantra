import requests
import json
import re
from pathlib import Path

BASE_URL = 'http://localhost:8000/api/v1'

print("=== S1: Admin endpoints & token tampering ===")
# Generate a tampered or fake admin token
fake_admin_token = "voyantra_token_admin_fake123456"
expired_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

# Is there any endpoint that checks tokens?
# Let's test POST /places/fetch-from-internet
r_s1_fake = requests.post(f'{BASE_URL}/places/fetch-from-internet?city_name=Pondicherry', headers={'Authorization': f'Bearer {fake_admin_token}'})
print("S1 fake token on /places/fetch-from-internet:", r_s1_fake.status_code, r_s1_fake.text)

r_s1_jwt = requests.post(f'{BASE_URL}/places/fetch-from-internet?city_name=Pondicherry', headers={'Authorization': f'Bearer {expired_jwt}'})
print("S1 expired JWT on /places/fetch-from-internet:", r_s1_jwt.status_code, r_s1_jwt.text)

print("\n=== S2: NoSQL Injection on login ===")
# Try NoSQL injection payload: {"email": {"$ne": null}, "password": {"$ne": null}}
r_nosql1 = requests.post(f'{BASE_URL}/auth/login', json={"email": {"$ne": None}, "password": {"$ne": None}})
print("NoSQL injection dict payload status:", r_nosql1.status_code)

# Try stringified NoSQL payload in email field: '{"$gt": ""}' or 'admin@voyantra.com\' || \'1\'==\'1'
r_nosql2 = requests.post(f'{BASE_URL}/auth/login', json={"email": "admin@voyantra.com", "password": {"$gt": ""}})
print("NoSQL password dict injection status:", r_nosql2.status_code)

print("\n=== S3: CORS & Secret Exposure ===")
# CORS preflight options check
r_cors = requests.options(f'{BASE_URL}/places', headers={
    'Origin': 'http://malicious-site.com',
    'Access-Control-Request-Method': 'GET'
})
print("CORS Access-Control-Allow-Origin:", r_cors.headers.get('Access-Control-Allow-Origin'))

# Check frontend build bundles for exposed GEMINI_API_KEY or credentials
dist_dir = Path('frontend/dist/assets')
exposed_keys = []
if dist_dir.exists():
    for f in dist_dir.glob('*.js'):
        content = f.read_text(encoding='utf-8', errors='ignore')
        # Search for AIza or AQ. or GEMINI_API_KEY
        matches = re.findall(r'AIza[0-9A-Za-z-_]{35}|AQ\.[0-9A-Za-z-_]{40,}', content)
        if matches:
            exposed_keys.extend(matches)
print("Exposed Gemini API keys in frontend bundles:", exposed_keys)

# Check API responses for API key leak
r_root = requests.get('http://localhost:8000/')
print("Root response:", r_root.json())
r_demo = requests.get(f'{BASE_URL}/auth/demo-accounts')
print("Demo accounts response:", r_demo.json())

print("\n=== S4: Rate limiting on Gemini endpoint ===")
# Check if rate limiter exists on generate-itinerary by firing 10 rapid requests
statuses = []
for i in range(5):
    res = requests.post(f'{BASE_URL}/recommendations/generate-itinerary', json={
        "city_id": "pondicherry",
        "query_text": "quick test",
        "duration_days": 1
    }, timeout=45)
    statuses.append(res.status_code)
print("Rapid 5 requests statuses (checking for 429 Too Many Requests):", statuses)
