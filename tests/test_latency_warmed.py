import requests
import time

BASE_URL = 'http://localhost:8000/api/v1'

def benchmark_warmed():
    session = requests.Session()
    # Warmup
    session.get(f'{BASE_URL}/places')
    
    rec_latencies = []
    for _ in range(5):
        t0 = time.perf_counter()
        session.post(f'{BASE_URL}/recommendations', json={
            "city_id": "pondicherry",
            "age_group": "family",
            "dietary_preference": "pure_veg_jain",
            "budget_tier": "moderate"
        })
        rec_latencies.append((time.perf_counter() - t0) * 1000)

    crowd_latencies = []
    for _ in range(5):
        t0 = time.perf_counter()
        session.get(f'{BASE_URL}/crowd/place/pondy-01?city_id=pondicherry&hour=18')
        crowd_latencies.append((time.perf_counter() - t0) * 1000)

    print("Recommendation API warmed latencies (ms):", [round(x, 2) for x in rec_latencies], "Avg:", round(sum(rec_latencies)/len(rec_latencies), 2))
    print("Crowd Place API warmed latencies (ms):", [round(x, 2) for x in crowd_latencies], "Avg:", round(sum(crowd_latencies)/len(crowd_latencies), 2))

if __name__ == '__main__':
    benchmark_warmed()
