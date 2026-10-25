# VOYANTRA: Full Platform System Specification

**Project Title:** VOYANTRA — Personalized Tourist Trip-Planning Platform  
**Target Operating Cities:** Pondicherry & Chennai, India  
**Technology Stack:** Python 3.14 (FastAPI), MongoDB (`voyantra_db`), Vite/React (Tailwind CSS, Leaflet/OSM), Google Gemini 1.5/3.6 RAG AI Engine  
**Constraint:** 100% Free-Tier & Open-Source Infrastructure (Zero Paid API Dependencies)

---

## Executive Summary & Operating Scope

**Voyantra** is an intelligent, open-source personalized tourist trip-planning platform designed to solve key challenges in modern leisure tourism: fragmented planning tools, lack of crowd visibility at local destinations, unexpected road closures during local festival processions, and generic recommendations that ignore user age demographics and dietary/religious preferences.

> **STRICT GEOGRAPHIC BOUNDARY:** Voyantra is strictly optimized and scoped for **Pondicherry** and **Chennai**, India. All place catalogs, crowd rules, festival procession calendars, and dietary options are strictly benchmarked against real-world ground truth in Pondicherry and Chennai.

---

## 1. Phase 1: Core Architecture, Demographic Scoring & Data Layer

### 1.1 Decoupled Service-Repository Architecture
The backend is built with Python 3.14 (FastAPI) adhering to a Decoupled Service-Repository pattern. Core ranking math, database persistence, and external service clients are decoupled from HTTP router logic. The database layer uses MongoDB (`voyantra_db`) running locally on port 27017.

### 1.2 Dual-Role Authentication & Persistence
Voyantra features a complete User and Admin authentication system backed by MongoDB (`voyantra_db.users`):
- **User Role** (`user@voyantra.com` / `user123`): Standard tourist access to personalized ranking, Gemini AI planning, crowd analytics, and trip basket.
- **Admin Role** (`admin@voyantra.com` / `admin123`): System administrator access with permission to ingest new city POIs and edit festival calendars.

### 1.3 Personalization & Demographic Scoring Math
Personalization is computed using an explainable multi-factor scoring model:
$$\text{MatchScore} = \left[ (W_{\text{category}} \times 0.45) + (C_{\text{budget}} \times 0.25) + (F_{\text{dietary}} \times 0.20) + (A_{\text{accessibility}} \times 0.10) \right] \times 100\%$$

Where:
- $W_{\text{category}}$ applies demographic age matrix weights (Young Adult 18–25, Adult 26–40, Family 41–60, Senior 60+).
- $F_{\text{dietary}}$ enforces hard filtering for self-declared dietary options (Pure Veg/Jain, Halal, Vegan, Vegetarian).

---

## 2. Phase 2: Gemini RAG AI Itinerary Generator & Refinement Engine

Phase 2 equips Voyantra with natural language trip synthesis powered by Google Gemini 1.5/3.6 RAG (Retrieval-Augmented Generation):
1. **Query Intent Parsing:** Parses free-text prompts into structured JSON filters.
2. **Feasibility & Reality Check:** Audits prompt requests against location realities (e.g. flagging snow skiing in coastal Pondicherry as unfeasible).
3. **Interactive Drag & Drop Schedule:** Users can swap, reorder, or edit visiting slots across Day 1 and Day 2 timelines.
4. **Continuous AI Follow-Up Refinement Chat:** Below the generated itinerary, users can type follow-up prompts (e.g., *"Make Day 2 more relaxed"*) or click quick refinement chips, which dynamically re-synthesize and update the active itinerary in real-time.

---

## 3. Phase 3: Rule-Based Crowd Estimation & Local Festival Advisory Calendar

### 3.1 Dynamic Rule-Based Crowd Engine
Phase 3 calculates real-time crowd density percentage (0% - 100%), crowd level badges (🟢 Low, 🟡 Moderate, 🔴 High, 🟣 Peak), 24-hour hourly crowd curves (6 AM - 10 PM), and driver explanations based on multi-variable rules:
- **Time-of-Day Rule:** Sunset peak (5:00 PM - 7:30 PM) for beaches; Morning/Evening pooja (6–9 AM & 5–8 PM) for temples; Evening snack rush (4–8 PM) for cafes.
- **Day-of-Week Rule:** Saturday & Sunday receive a +20% crowd density boost.
- **Seasonal Rule:** December–January holiday surge adds +15% density.
- **Festival Collision Rule:** Active local festivals add +30% density and set advisory status to Peak.

### 3.2 Interactive CrowdBadge Popover
Clicking any `CrowdBadge` on place cards opens an interactive analytics popover displaying:
- Dynamic Capacity Progress Bar (0% to 100%).
- Recommended Quiet Visiting Window (e.g., *"8:00 AM - 10:30 AM (Lowest Crowd)"*).
- Active Festival Warnings & Traffic Alerts.
- Crowd Driver Breakdown (e.g., *"Weekend Tourist Boost +20%"*).
- 24-Hour Hourly Crowd Bar Chart.

### 3.3 Local Festival Advisory Calendar
Includes dedicated festival calendars (`pondicherry_festivals.json` & `chennai_festivals.json`) tracking events like Masi Magam Beach Festival, Sri Aurobindo Darshan, Bastille Day, Christmas/New Year, Margazhi Music Season, and Pongal. The `FestivalAdvisoryBanner` and `FestivalCalendarModal` surface active procession routes, affected streets, and road closure alerts.

---

## 4. Automatic Location & Proximity Detection System

Voyantra includes an automated GPS location detection and city switching engine:
- **GPS Proximity Detection:** Evaluates user coordinates against Pondicherry (11.9416, 79.8083) and Chennai (13.0827, 80.2707) using the Haversine distance formula.
- **Automatic Switching:** If user is within 70 km of Pondicherry or Chennai, `selectedCity` automatically switches to that city with a top toast notice.
- **Out-of-Bounds Location Choice Popup:** If the user is outside both cities (> 70 km away) or GPS permissions are denied, the `LocationPromptModal` pops up asking the user to manually select Pondicherry or Chennai.
- **Navbar GPS Trigger:** Users can click the `📍 GPS` button in the Navbar anytime to re-detect coordinates.

---

## 5. Complete REST API Endpoint Specification

| HTTP Method | Endpoint Path | Module / Purpose | Auth Required |
|---|---|---|---|
| POST | `/api/v1/auth/login` | User & Admin Authentication | No |
| POST | `/api/v1/auth/register` | New User / Admin Registration | No |
| GET | `/api/v1/places` | Fetch Places with Demographic/Dietary Filters | No |
| POST | `/api/v1/places/fetch-from-internet` | Direct Wikidata/Wikipedia Live Ingestion | Admin |
| GET | `/api/v1/hotels` | Fetch Hotels Filtered by Price Tier & Radius | No |
| POST | `/api/v1/recommendations` | Personalized Demographic Ranking Engine | No |
| GET | `/api/v1/recommendations/preset-suggestions` | Preset Travel Suggestions Carousel | No |
| POST | `/api/v1/recommendations/generate-itinerary` | Gemini RAG AI Itinerary Synthesis & Refinement | No |
| GET | `/api/v1/festivals` | Get City Festival Advisory Calendar | No |
| GET | `/api/v1/festivals/active` | Get Active Festivals for Travel Date | No |
| GET | `/api/v1/crowd/place/{place_id}` | Phase 3 Dynamic Crowd Density & Hourly Curve | No |
| GET | `/api/v1/crowd/city/{city_id}` | Overall City Congestion Index & Alerts | No |

---

## 6. Project Roadmap Matrix

| Phase | Feature Description | Status |
|---|---|---|
| **Phase 1** | Core Architecture, Places/Hotels DB, Demographic Ranking, Basket Estimator, Live Internet Ingestion, Dual Auth. | **COMPLETED** |
| **Phase 2** | Google Gemini RAG AI Itinerary Synthesis, Reality Auditing, Drag & Drop Timeline, Continuous AI Chat Refinement. | **COMPLETED** |
| **Phase 3** | Rule-Based Dynamic Crowd Density Engine, Hourly Curve Graphs, Quiet Window Recs, Local Festival Advisory Calendar. | **COMPLETED** |
| **Phase 3.5** | GPS Geolocation Proximity Detection (70 km radius), Auto City Switch, & Out-of-Bounds Location Choice Popup. | **COMPLETED** |
| **Phase 4** | OSRM Turn-by-Turn Multi-Stop Routing & Interactive Navigation Overlays. | Planned |
| **Phase 5** | Live Crowdsourced Realtime Crowd Reporting (Supabase 1-Tap Updates). | Planned |
| **Phase 6** | XGBoost Machine Learning Crowd Forecasting Model & SHAP Explainability. | Planned |
