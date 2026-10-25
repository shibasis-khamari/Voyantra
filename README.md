# Voyantra 🗺️
**Personalized Tourist Trip-Planning Platform** (Pilot City: Pondicherry, India)

Voyantra is an intelligent, open-source, academic mini-project designed to help travelers decide **where to go, when to go, and what to expect**. It combines curated places and hotels with budget filtering, crowd-level estimations, festival-based travel advisories, and personalization based on the traveler's age demographic and opt-in religious/dietary preferences.

---

## 🏛️ Modular & Extensible Architecture

The codebase is built with modular separation so you can **easily change, extend, and add new features**:

```
E:\Voyantra\
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Modular API endpoints (places, hotels, recommendations, preferences)
│   │   ├── core/            # App config, database connectors, settings
│   │   ├── data/            # City-agnostic JSON datasets (*_places.json, *_hotels.json, etc.)
│   │   ├── models/          # Database entities
│   │   ├── schemas/         # Pydantic validation & data transfer schemas
│   │   ├── services/        # Decoupled business logic (ranking_service, places_service, hotels_service)
│   │   └── main.py          # FastAPI application entrypoint
│   ├── requirements.txt
│   └── run.py
│
├── frontend/
│   ├── src/
│   │   ├── components/      # Atomic UI components (Navbar, PlaceCard, HotelCard, MapView, Badges)
│   │   ├── context/         # User demographic & trip planning state
│   │   ├── pages/           # Explore, Planner, Hotels, Interactive Map, Profile
│   │   ├── services/        # Pluggable API client with automatic client-side fallback
│   │   └── types/           # Category tags, age brackets, constants
│   ├── package.json
│   └── vite.config.js
│
└── Voyantra_Full_Specification.docx
```

---

## 🌐 Direct Live Data Ingestion from the Internet

Voyantra includes a **Live Internet Ingestion Pipeline** that automatically fetches and populates destinations for **any city in the world** with 100% free, open-source APIs:

- **Geocoding**: OpenStreetMap Nominatim & Photon API.
- **Attractions & POIs**: Wikidata SPARQL & Wikipedia Search API (extracts real descriptions, coordinates, categories, and high-resolution Wikimedia images).
- **Auto-Enrichment**: Dynamically classifies categories (`heritage`, `beach`, `spiritual`, `cafe`, `nature`), estimated budgets, accessibility ratings, and demographic suitability.

### How to Ingest a New City:
1. **Via UI**: Click **`+ Ingest Live`** in the top navbar, type any city name (e.g. `Goa`, `Jaipur`, `Kochi`, `Manali`, `Varanasi`), and click **Fetch & Save to DB**.
2. **Via API**:
   ```bash
   POST http://localhost:8000/api/v1/places/fetch-from-internet?city_name=Goa
   ```
   The city is automatically saved to disk (`<city_id>_places.json`), added to `cities.json`, and displayed on the interactive Leaflet map!

---

## 🛠️ Running the Project

### 1. Running the Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

> **Note:** The frontend has a built-in offline adapter (`api.js` + `seedData.js`). It works immediately and dynamically even if the backend is not started!

### 2. Running the Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
python run.py
```
API Documentation will be live at `http://localhost:8000/docs`.

---

## 🌟 Phase 1 Deliverables Implemented
- ✅ **Curated Pondicherry Database**: POIs, French colonial landmarks, cafes, beaches, ashrams, and hotels with price tiers, coordinates, and crowd tendencies.
- ✅ **Personalization Engine**: Age-group demographic weighting (18-25, 26-40, 41-60, 60+) and opt-in dietary filtering (Pure Veg/Jain, Halal, Vegan, All).
- ✅ **Explainable Match Scoring**: Transparent reasons explaining why each destination was ranked for the user.
- ✅ **Interactive Leaflet & OpenStreetMap**: Map pins with category color-coding and OSRM direction triggers (100% free, zero paid Google API traps).
- ✅ **Responsive UI & Trip Basket**: Add/remove places, estimate total time and cost, and view detailed place modals.
