import sys
import json
import urllib.request

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

headers = {'User-Agent': 'Voyantra-Travel-Planner/1.0 (Academic Research & Travel Planning Demo)'}

print("=== 1. CHENNAI PAIR (Marina Beach -> Kapaleeshwarar Temple) ===")
url_pair = 'https://routing.openstreetmap.de/routed-foot/route/v1/driving/80.2824,13.0499;80.2698,13.0335?overview=full&geometries=geojson&steps=true'
req = urllib.request.Request(url_pair, headers=headers)
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    r = data['routes'][0]
    dist_m = r['distance']
    dur_s = r['duration']
    speed = (dist_m / 1000.0) / (dur_s / 3600.0) if dur_s > 0 else 0
    print(f"URL: {url_pair}")
    print(f"Status: {resp.status}, Code: {data.get('code')}")
    print(f"Distance: {dist_m:.1f} m ({dist_m/1000:.3f} km)")
    print(f"Duration: {dur_s:.1f} s ({dur_s/60:.2f} min)")
    print(f"Implied Pedestrian Speed: {speed:.2f} km/h")
    print(f"Steps Count: {len(r['legs'][0]['steps'])}")
    print(f"First Step: {r['legs'][0]['steps'][0].get('name', 'unnamed')}")

print("\n=== 2. LONGER CHENNAI ROUTE (Guindy National Park -> Marina Beach) ===")
url_long = 'https://routing.openstreetmap.de/routed-foot/route/v1/driving/80.2206,13.0067;80.2824,13.0499?overview=full&geometries=geojson'
req_l = urllib.request.Request(url_long, headers=headers)
with urllib.request.urlopen(req_l, timeout=10) as resp:
    data_l = json.loads(resp.read().decode('utf-8'))
    r_l = data_l['routes'][0]
    dist_l_m = r_l['distance']
    dur_l_s = r_l['duration']
    speed_l = (dist_l_m / 1000.0) / (dur_l_s / 3600.0) if dur_l_s > 0 else 0
    print(f"URL: {url_long}")
    print(f"Status: {resp.status}, Code: {data_l.get('code')}")
    print(f"Distance: {dist_l_m:.1f} m ({dist_l_m/1000:.3f} km)")
    print(f"Duration: {dur_l_s:.1f} s ({dur_l_s/60:.2f} min = {dur_l_s/3600:.2f} hours)")
    print(f"Implied Pedestrian Speed: {speed_l:.2f} km/h")
    print(f"Polyline Coordinates Count: {len(r_l['geometry']['coordinates'])}")

print("\n=== 3. /TABLE PROBE (3 Chennai Waypoints) ===")
coords = '80.2824,13.0499;80.2698,13.0335;80.2777,13.0337'
url_tbl = f'https://routing.openstreetmap.de/routed-foot/table/v1/driving/{coords}?annotations=duration,distance'
req_t = urllib.request.Request(url_tbl, headers=headers)
with urllib.request.urlopen(req_t, timeout=10) as resp:
    data_t = json.loads(resp.read().decode('utf-8'))
    print(f"URL: {url_tbl}")
    print(f"Status: {resp.status}, Code: {data_t.get('code')}")
    print("Durations Matrix (seconds):", data_t.get('durations'))
    print("Distances Matrix (meters):", data_t.get('distances'))
