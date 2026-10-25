const BACKEND_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const BACKEND_OFFLINE_MSG = 'Backend Server Disconnected: Could not connect to FastAPI server at http://localhost:8000. Please start the backend by running "cd backend && python run.py".';

/**
 * Strict Connected API Client (No offline seed fallbacks)
 */
export const VoyantraAPI = {
  // Fetch available cities
  async getCities() {
    try {
      const res = await fetch(`${BACKEND_URL}/places/cities/all`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) return await res.json();
      throw new Error(`Server returned status ${res.status}`);
    } catch (e) {
      throw new Error(BACKEND_OFFLINE_MSG);
    }
  },

  // Direct Internet Ingestion (OpenStreetMap + Wikipedia)
  async fetchCityFromInternet(cityName) {
    try {
      const token = localStorage.getItem('voyantra_token');
      const headers = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      const res = await fetch(`${BACKEND_URL}/places/fetch-from-internet?city_name=${encodeURIComponent(cityName)}`, {
        method: 'POST',
        headers,
        signal: AbortSignal.timeout(30000)
      });
      if (res.ok) {
        return await res.json();
      } else {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to fetch city from internet');
      }
    } catch (e) {
      if (e.message.includes('Backend Server Disconnected') || e.name === 'TimeoutError' || e.message.includes('Failed to fetch')) {
        throw new Error(BACKEND_OFFLINE_MSG);
      }
      throw e;
    }
  },

  // 1. Fetch Places
  async getPlaces(filters = {}) {
    const cityId = filters.city_id || 'pondicherry';
    try {
      const queryParams = new URLSearchParams();
      queryParams.append('city_id', cityId);
      if (filters.category && filters.category !== 'all') {
        queryParams.append('category', filters.category);
      }
      if (filters.budget) {
        queryParams.append('budget', filters.budget);
      }
      if (filters.search) {
        queryParams.append('search', filters.search);
      }
      if (filters.age_group) {
        queryParams.append('age_group', filters.age_group);
      }
      if (filters.dietary && filters.dietary !== 'all') {
        queryParams.append('dietary', filters.dietary);
      }

      const res = await fetch(`${BACKEND_URL}/places?${queryParams.toString()}`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        return await res.json();
      }
      throw new Error(`Server status ${res.status}`);
    } catch (e) {
      throw new Error(BACKEND_OFFLINE_MSG);
    }
  },

  // 2. Fetch Hotels
  async getHotels(filters = {}) {
    try {
      const queryParams = new URLSearchParams();
      if (filters.budget) queryParams.append('budget', filters.budget);
      if (filters.max_price) queryParams.append('max_price', filters.max_price);
      
      const res = await fetch(`${BACKEND_URL}/hotels?${queryParams.toString()}`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        return await res.json();
      }
      throw new Error(`Server status ${res.status}`);
    } catch (e) {
      throw new Error(BACKEND_OFFLINE_MSG);
    }
  },

  // 3. Preset Suggestions
  async getPresetSuggestions() {
    try {
      const res = await fetch(`${BACKEND_URL}/recommendations/preset-suggestions`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) return await res.json();
      throw new Error(`Server status ${res.status}`);
    } catch (e) {
      throw new Error(BACKEND_OFFLINE_MSG);
    }
  },

  // 4. Generate AI Itinerary (RAG + Gemini)
  async generateAiItinerary({ city_id, query_text, age_group, dietary_preference, duration_days = 2, existing_days = null }) {
    try {
      const res = await fetch(`${BACKEND_URL}/recommendations/generate-itinerary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          city_id: city_id || 'pondicherry',
          query_text,
          age_group,
          dietary_preference,
          duration_days,
          existing_days
        }),
        signal: AbortSignal.timeout(40000)
      });
      if (res.ok) {
        return await res.json();
      }
      const errData = await res.json();
      throw new Error(errData.detail || `Server status ${res.status}`);
    } catch (e) {
      if (e.message.includes('Server status') || e.name === 'TimeoutError' || e.message.includes('Failed to fetch')) {
        throw new Error(BACKEND_OFFLINE_MSG);
      }
      throw e;
    }
  },

  // 5. Personalized Recommendation Ranking
  async getPersonalizedRecommendations({ age_group, dietary_preference, budget_tier, interests = [] }) {
    try {
      const res = await fetch(`${BACKEND_URL}/recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          city_id: 'pondicherry',
          age_group,
          dietary_preference,
          budget_tier,
          interests
        }),
        signal: AbortSignal.timeout(3000)
      });
      if (res.ok) {
        return await res.json();
      }
      throw new Error(`Server status ${res.status}`);
    } catch (e) {
      throw new Error(BACKEND_OFFLINE_MSG);
    }
  },

  // 6. Auth - Login
  async login({ email, password, role = 'user' }) {
    try {
      const res = await fetch(`${BACKEND_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, role }),
        signal: AbortSignal.timeout(5000)
      });
      if (res.ok) {
        return await res.json();
      }
      const err = await res.json();
      throw new Error(err.detail || 'Login failed');
    } catch (e) {
      if (e.message.includes('Server status') || e.name === 'TimeoutError' || e.message.includes('Failed to fetch')) {
        throw new Error(BACKEND_OFFLINE_MSG);
      }
      throw e;
    }
  },

  // 7. Auth - Register
  async register({ name, email, password, role = 'user' }) {
    try {
      const res = await fetch(`${BACKEND_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password, role }),
        signal: AbortSignal.timeout(5000)
      });
      if (res.ok) {
        return await res.json();
      }
      const err = await res.json();
      throw new Error(err.detail || 'Registration failed');
    } catch (e) {
      if (e.message.includes('Server status') || e.name === 'TimeoutError' || e.message.includes('Failed to fetch')) {
        throw new Error(BACKEND_OFFLINE_MSG);
      }
      throw e;
    }
  },

  // 8. Phase 3: Festivals Advisory API
  async getFestivals(city_id = 'pondicherry') {
    try {
      const res = await fetch(`${BACKEND_URL}/festivals?city_id=${encodeURIComponent(city_id)}`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) return await res.json();
      return [];
    } catch (e) {
      return [];
    }
  },

  async getActiveFestivals(city_id = 'pondicherry', target_date = null) {
    try {
      const q = target_date ? `&target_date=${encodeURIComponent(target_date)}` : '';
      const res = await fetch(`${BACKEND_URL}/festivals/active?city_id=${encodeURIComponent(city_id)}${q}`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) return await res.json();
      return [];
    } catch (e) {
      return [];
    }
  },

  // 9. Phase 3: Rule-Based Crowd Estimation API
  async getPlaceCrowdEstimate(place_id, city_id = 'pondicherry', target_date = null, hour = null) {
    try {
      const params = new URLSearchParams();
      params.append('city_id', city_id);
      if (target_date) params.append('target_date', target_date);
      if (hour !== null && hour !== undefined) params.append('hour', hour);

      const res = await fetch(`${BACKEND_URL}/crowd/place/${encodeURIComponent(place_id)}?${params.toString()}`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) return await res.json();
      return null;
    } catch (e) {
      return null;
    }
  },

  async getCityCrowdIndex(city_id = 'pondicherry', target_date = null) {
    try {
      const q = target_date ? `?target_date=${encodeURIComponent(target_date)}` : '';
      const res = await fetch(`${BACKEND_URL}/crowd/city/${encodeURIComponent(city_id)}${q}`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) return await res.json();
      return null;
    } catch (e) {
      return null;
    }
  },

  // Phase 5: Real-Time Crowdsourced Reporting & Live Status
  async getLiveCrowdStatus(placeId, cityId = 'pondicherry') {
    try {
      const res = await fetch(`${BACKEND_URL}/crowd/place/${encodeURIComponent(placeId)}/live?city_id=${encodeURIComponent(cityId)}`, {
        signal: AbortSignal.timeout(4000)
      });
      if (res.ok) return await res.json();
      return null;
    } catch (e) {
      console.warn('[VoyantraAPI] getLiveCrowdStatus notice:', e.message);
      return null;
    }
  },

  async submitCrowdReport(payload) {
    try {
      const token = localStorage.getItem('voyantra_token');
      const headers = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      const res = await fetch(`${BACKEND_URL}/crowd/report`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(6000)
      });
      if (res.ok) {
        return await res.json();
      }
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Report failed with status ${res.status}`);
    } catch (e) {
      console.error('[VoyantraAPI] submitCrowdReport error:', e.message);
      throw e;
    }
  },

  // 10. Phase 4: OSRM Routing, Matrix & Day Optimization
  async getRoutePlan(payload) {
    try {
      const res = await fetch(`${BACKEND_URL}/routes/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(10000)
      });
      if (res.ok) return await res.json();
      throw new Error(`Routing failed with status ${res.status}`);
    } catch (e) {
      console.warn('[VoyantraAPI] getRoutePlan notice:', e.message);
      return null;
    }
  },

  async getRouteMatrix(payload) {
    try {
      const res = await fetch(`${BACKEND_URL}/routes/matrix`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(10000)
      });
      if (res.ok) return await res.json();
      throw new Error(`Matrix calculation failed with status ${res.status}`);
    } catch (e) {
      console.warn('[VoyantraAPI] getRouteMatrix notice:', e.message);
      return null;
    }
  },

  async optimizeDaySchedule(payload) {
    try {
      const res = await fetch(`${BACKEND_URL}/routes/optimize-day`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(30000)
      });
      if (res.ok) return await res.json();
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Optimization failed with status ${res.status}`);
    } catch (e) {
      console.warn('[VoyantraAPI] optimizeDaySchedule error:', e.message);
      throw e;
    }
  }
};
