import { SEED_PLACES, SEED_HOTELS } from './seedData';

// If running on phone, change this to your computer's local IP (e.g., http://192.168.x.x:8000/api/v1)
const BACKEND_URL = 'http://localhost:8000/api/v1';

export const MobileAPI = {
  async getPlaces(filters = {}) {
    try {
      const res = await fetch(`${BACKEND_URL}/places`, { signal: AbortSignal.timeout(1000) });
      if (res.ok) return await res.json();
    } catch (e) {
      // Offline fallback
    }

    return SEED_PLACES.filter(place => {
      if (filters.category && filters.category !== 'all' && place.category !== filters.category) return false;
      if (filters.search) {
        const q = filters.search.toLowerCase();
        return place.name.toLowerCase().includes(q) || place.description.toLowerCase().includes(q);
      }
      return true;
    });
  },

  async getHotels() {
    try {
      const res = await fetch(`${BACKEND_URL}/hotels`, { signal: AbortSignal.timeout(1000) });
      if (res.ok) return await res.json();
    } catch (e) {}
    return SEED_HOTELS;
  },

  async getPersonalizedRecommendations({ age_group, dietary_preference, budget_tier }) {
    try {
      const res = await fetch(`${BACKEND_URL}/recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ city_id: 'pondicherry', age_group, dietary_preference, budget_tier }),
        signal: AbortSignal.timeout(1000)
      });
      if (res.ok) return await res.json();
    } catch (e) {}

    // Client-side ranking
    const ranked = SEED_PLACES.map(place => {
      let score = 55;
      const reasons = [];

      if (age_group === 'young_adult' && ['adventure', 'beach', 'cafe'].includes(place.category)) {
        score += 25;
        reasons.push('High energy & vibrant cafe scene');
      } else if (age_group === 'senior' && ['spiritual', 'heritage'].includes(place.category)) {
        score += 25;
        reasons.push('Serene, flat terrain & peaceful atmosphere');
      } else if (age_group === 'family' && ['beach', 'heritage'].includes(place.category)) {
        score += 20;
        reasons.push('Family-friendly walking route');
      }

      if (dietary_preference === 'pure_veg_jain' && place.category === 'dining') {
        score += 20;
        reasons.push('Dedicated Pure Veg / Jain options');
      }

      return {
        place,
        match_score: Math.min(99, score),
        match_reasons: reasons.length > 0 ? reasons : ['Iconic Pondicherry highlight']
      };
    });

    ranked.sort((a, b) => b.match_score - a.match_score);
    return { ranked_places: ranked };
  }
};
