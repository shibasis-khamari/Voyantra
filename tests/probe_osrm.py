import urllib.request
import json
import sys

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

coords = '79.832,11.934;79.834,11.938'
req_headers = {'User-Agent': 'Voyantra-Travel-Planner/1.0 (Academic/Demo)'}

for mode in ['driving', 'walking']:
    url = f'http://router.project-osrm.org/route/v1/{mode}/{coords}?overview=full&geometries=geojson&steps=true'
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw_body = resp.read().decode('utf-8')
            data = json.loads(raw_body)
            route = data['routes'][0]
            print(f"=== OSRM PUBLIC DEMO PROBE: {mode.upper()} ===")
            print(f"URL: {url}")
            print(f"HTTP Status: {resp.status}")
            print(f"OSRM Code: {data.get('code')}")
            print(f"Road Distance: {route['distance']:.1f} m ({route['distance']/1000:.3f} km)")
            print(f"Reported Duration: {route['duration']:.1f} s ({route['duration']/60:.2f} min)")
            speed_kmh = (route['distance'] / 1000.0) / (route['duration'] / 3600.0) if route['duration'] > 0 else 0
            print(f"Computed Implied Speed: {speed_kmh:.2f} km/h")
            print(f"Number of Route Steps: {len(route['legs'][0]['steps'])}")
            print(f"First Step Instruction: {route['legs'][0]['steps'][0]['maneuver']['type']} on {route['legs'][0]['steps'][0].get('name', 'unnamed')}")
            print("Raw Response Sample (first 250 chars):")
            print(raw_body[:250])
            print()
    except Exception as e:
        print(f"Probe Error for {mode}: {e}")
