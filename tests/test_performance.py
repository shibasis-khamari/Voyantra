import requests
import time

BASE_URL = 'http://127.0.0.1:8000/api/v1'

def benchmark():
    # 1. Recommendation endpoint latency
    t0 = time.perf_counter()
    r_rec = requests.post(f'{BASE_URL}/recommendations', json={
        "city_id": "pondicherry",
        "age_group": "family",
        "dietary_preference": "pure_veg_jain",
        "budget_tier": "moderate"
    })
    t_rec = (time.perf_counter() - t0) * 1000

    # 2. Crowd place endpoint latency
    t0 = time.perf_counter()
    r_crowd = requests.get(f'{BASE_URL}/crowd/place/pondy-01?city_id=pondicherry&hour=18')
    t_crowd = (time.perf_counter() - t0) * 1000

    # 3. Crowd city endpoint latency
    t0 = time.perf_counter()
    r_city_crowd = requests.get(f'{BASE_URL}/crowd/city/pondicherry')
    t_city_crowd = (time.perf_counter() - t0) * 1000

    # 4. Itinerary generation latency (LLM RAG)
    t0 = time.perf_counter()
    r_itin = requests.post(f'{BASE_URL}/recommendations/generate-itinerary', json={
        "city_id": "pondicherry",
        "query_text": "2-day trip to Pondicherry",
        "duration_days": 2
    }, timeout=60)
    t_itin = (time.perf_counter() - t0) * 1000

    print(f"Recommendation API latency: {t_rec:.2f} ms (Target < 500 ms: {t_rec < 500})")
    print(f"Crowd Place API latency:     {t_crowd:.2f} ms (Target < 500 ms: {t_crowd < 500})")
    print(f"Crowd City API latency:      {t_city_crowd:.2f} ms (Target < 500 ms: {t_city_crowd < 500})")
    print(f"AI Itinerary API latency:    {t_itin:.2f} ms ({t_itin/1000:.2f} s)")

if __name__ == '__main__':
    benchmark()
