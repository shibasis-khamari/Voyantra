# VOYANTRA: Full Platform System Specification

**Project Title:** VOYANTRA — Personalized Worldwide AI Travel Concierge & Dynamic Trip-Planning Platform  
**Geographic Scope:** Worldwide (Any destination across India and globally, with high-density curated datasets for pilot regions)  
**Technology Stack:** Python 3.10+ (FastAPI), MongoDB Atlas Cloud (`voyantra_db`), Vite/React (Tailwind CSS, Google Maps JavaScript API, Leaflet/OSM), Google Gemini 3.5 Flash AI Engine  
**Infrastructure Model:** Free-Tier & Resilient Architecture with Cloud Persistence  

---

## 1. Executive Summary & Operating Scope

**Voyantra** is an intelligent, full-stack travel platform designed to solve fragmented trip planning, unexpected festival road closures, crowd uncertainty, and generic recommendations that ignore user dietary, demographic, and geographical constraints.

### 1.1 Worldwide Dynamic Travel Scope
Voyantra operates **worldwide without hardcoded city limits**:
- **Dynamic Destination Detection:** Extracts target destinations from natural language queries, conversation history, or explicit parameters (e.g., Mumbai, Jaipur, Himachal Pradesh, Tokyo, Paris, Bali, Dubai, Kyoto).
- **Dual Data Strategy:**
  - **Global Destinations:** Powered dynamically by Google Gemini 3.5 Flash for authentic landmarks, regional cuisines, cultural etiquette, transit feasibility, and structured multi-day schedules.
  - **High-Density Pilot Catalogs (Pondicherry & Chennai):** Enriched with verified local POIs, exact street-level coordinates, pricing, opening hours, local festival calendars, and crowd heuristics.

---

## 2. Core Architecture & Cloud Data Layer

### 2.1 Decoupled Service-Repository Architecture
The backend is structured into modular layers adhering to the Service-Repository pattern:
- **`app/api/v1/`**: Modular REST endpoints (`auth`, `recommendations`, `routes`, `crowd`, `festivals`, `places`, `hotels`).
- **`app/services/`**: Decoupled business logic (`gemini_service`, `routing_service`, `places_service`, `crowd_service`, `weather_service`, `auth_service`).
- **`app/core/`**: Configuration, MongoDB Atlas manager, geo-utilities, security dependencies.
- **`app/schemas/`**: Strict Pydantic models for request/response validation and typing.

### 2.2 Cloud Database: MongoDB Atlas (`voyantra_db`)
Persistent data storage is hosted on **MongoDB Atlas** (`cluster0.hqayaiu.mongodb.net`):
- **`users` Collection:** Stores user and admin accounts with bcrypt password hashing (`$2b$`) and JWT-based authentication.
- **`places` Collection:** Verified points of interest, categories, coordinates, and etiquette rules.
- **`hotels` Collection:** Curated accommodation listings with budget classifications.
- **`festivals` Collection:** Cultural event calendars with impacted routes and date ranges.
- **`route_cache` Collection:** High-performance route distance and duration cache with 7-day TTL (`expireAfterSeconds=604800`).
- **`crowd_reports` & `feature_snapshots`:** Crowd telemetry with 24-hour TTL and compound indices for fast aggregation.

### 2.3 Authentication & Role-Based Access Control (RBAC)
- **Authentication:** Standard OAuth2-compatible Bearer JWT tokens (`HS256`, 24-hour expiration).
- **Roles:**
  - `user`: Standard traveler profile; can plan trips, query AI concierge, save favorites, and access turn-by-turn navigation.
  - `admin`: System administrator; access to user management dashboard (`/admin/users`), role modification, and data ingestion.
- **Pre-seeded Accounts:**
  - User: `user@voyantra.com` / `user123`
  - Admin: `admin@voyantra.com` / `admin123`

---

## 3. Conversational AI Engine & Itinerary Synthesis

### 3.1 Google Gemini 3.5 Flash Engine
The platform utilizes **`gemini-3.5-flash`** as its primary generative engine, offering optimal balance between deep reasoning, low latency (~3s), and generous free-tier quotas (15 RPM / 1,500 RPD):
- **Fallback Hierarchy:** If the primary model encounters rate limits or offline conditions, the engine falls back to `gemini-3.5-flash-lite`, and subsequently to a deterministic local heuristic planner.

### 3.2 Dynamic Conversational Concierge (`/recommendations/chat`)
- Answers travel queries about destinations, hotels, street food, history, and seasonal weather globally.
- Maintains multi-turn conversation context (e.g., Turn 1: *"What are the best places in Tokyo?"* &rarr; Turn 2: *"Suggest affordable hotels near there"* correctly resolves *"there"* to Tokyo).
- Provides side-by-side destination comparisons (e.g., *"Compare Goa and Kerala for a relaxing beach vacation"*).

### 3.3 Multi-Day Itinerary Synthesis (`/recommendations/generate-itinerary`)
- Synthesizes 1 to 7 day structured itineraries with `morning`, `afternoon`, and `evening` activity slots.
- **Dietary & Demographic Constraints:**
  - **Pacing:** Young Adult, Family, Senior Traveler.
  - **Dietary Strictness:** Pure Veg / Jain (enforces zero-onion/garlic breakfast venues), Halal, Vegan, or All.
  - **Budget Tiers:** Budget, Moderate, Luxury.
- **Geographic Feasibility Auditing:** Verifies that suggested landmarks are geographically compatible and logically clustered to minimize intra-day travel fatigue.

---

## 4. Dual Map, Routing & Navigation Engine

### 4.1 In-App Google Maps Navigation
- **Pre-configured Permanent Key:** Integrates Google Maps JavaScript API with permanent key support for seamless in-app navigation.
- **Live Directions & Traffic:** Real-time road routing between itinerary stops via `google.maps.DirectionsService` and optional live traffic overlay.
- **User Location Navigation:** Bottom-right navigation button detects traveler's live GPS coordinates, draws the route to any selected stop, and provides a direct launch link into Google Maps turn-by-turn navigation.
- **Adjustable Splitter:** Drag-and-drop divider allows users to slide and dynamically resize the space allocated between the itinerary cards and the map viewport.

### 4.2 OpenStreetMap / Leaflet Fallback
- Completely decoupled, zero-cost fallback utilizing OpenStreetMap tiles and Leaflet.js with OSRM (Open Source Routing Machine) road geometry.

### 4.3 Traveling Salesperson Problem (TSP) Optimizer (`/routes/optimize-day`)
- Implements time-constrained TSP sequencing:
  - Takes a day's stops and evaluates the complete waypoint distance/duration matrix (`/routes/matrix`).
  - Factors in fixed time anchors (e.g. sunset at beaches, pooja at temples) and opening hours.
  - Re-sequences stops to minimize transit distance while guaranteeing constraint compliance.

---

## 5. Crowd Heuristics, Weather & Festivals

### 5.1 Dynamic Crowd Estimation
- Computes crowd density percentages (0%–100%) and categorizes levels: Low (🟢), Moderate (🟡), High (🔴), Peak (🟣).
- Multi-factor heuristic model accounting for:
  - Time-of-day rush hours (morning pooja, evening promenade, dinner rush).
  - Weekend boost (+20% density on Saturday/Sunday).
  - Seasonal tourist multipliers and local festival collision alerts.

### 5.2 Dynamic Weather Geocoding
- Integrated with Open-Meteo's keyless API with dynamic worldwide geocoding (`_resolve_coordinates`), providing real-time temperatures, weather codes, and seasonal climate summaries for any city on Earth.

### 5.3 Local Festival & Road Closure Calendars
- Surfaces procession routes, affected streets, and temple closure warnings during cultural festivals.

---

## 6. Frontend Architecture & Design System

### 6.1 Typography Pairing
- **Serif / Display:** `"Instrument Serif"`, Georgia, serif (warm, editorial elegance).
- **Sans / UI:** `"Plus Jakarta Sans"`, system-ui, sans-serif (clean modern legibility across data tables, badges, and itinerary timelines).

### 6.2 Visual Styling & Aesthetics
- **Color Palette:** Warm sandstone background (`#FAF8F5`), secondary amber accents (`#FCD34D`), terracotta brand highlights, and deep charcoal text.
- **Glassmorphism:** Translucent frosted panels (`backdrop-blur-md`, subtle borders) for cards, chat bubbles, and modal dialogs.
- **Responsive Layout:** Adaptive single-page application with tabs for Explore, Planner, Hotels, Live Map, and Admin User Management.

---

## 7. REST API Endpoint Specification

| Method | Endpoint | Module | Description | Auth |
|:---|:---|:---|:---|:---|
| `POST` | `/api/v1/auth/login` | Auth | Authenticate user/admin & return JWT token | No |
| `POST` | `/api/v1/auth/register` | Auth | Register new traveler in MongoDB Atlas | No |
| `GET` | `/api/v1/auth/me` | Auth | Get current authenticated user profile | Bearer |
| `GET` | `/api/v1/auth/admin/users` | Admin | List all registered users in database | Admin |
| `POST` | `/api/v1/recommendations/chat` | AI Concierge | Natural language travel conversation worldwide | No |
| `POST` | `/api/v1/recommendations/generate-itinerary` | Itinerary | Synthesize 1–7 day feasible itinerary with Gemini | No |
| `POST` | `/api/v1/routes/plan` | Routing | Point-to-point driving/walking route with maneuvers | No |
| `POST` | `/api/v1/routes/matrix` | Routing | NxN distance & duration matrix (up to 10 stops) | No |
| `POST` | `/api/v1/routes/optimize-day` | Optimization | Time-constrained TSP daily stop re-sequencing | No |
| `GET` | `/api/v1/crowd/city/{city_id}` | Crowd | City-wide congestion estimate & travel advisories | No |
| `GET` | `/api/v1/crowd/place/{place_id}` | Crowd | Place-level density score & hourly curve | No |
| `GET` | `/api/v1/festivals` | Festivals | Cultural festival calendar with road closure alerts | No |
| `GET` | `/api/v1/places` | Catalog | Filter places by category, budget, dietary tags | No |
| `GET` | `/api/v1/hotels` | Catalog | Filter accommodations by price tier and radius | No |
| `GET` | `/api/v1/weather/forecast` | Weather | Real-time weather and temperature forecast | No |

---

## 8. Implementation & Verification Status Matrix

| Milestone / Capability | Scope & Details | Status |
|:---|:---|:---:|
| **Worldwide Travel Concierge** | Dynamic destination detection for any city/country globally; multi-turn context; comparison queries. | **COMPLETED** |
| **Generative AI Itinerary Engine** | Google Gemini 3.5 Flash integration; 1–7 day synthesis; Jain/Pure Veg dietary filtering; reality auditing. | **COMPLETED** |
| **Cloud Database (MongoDB Atlas)** | Persistent cloud storage for users, places, hotels, festivals, route cache, and crowd telemetry. | **COMPLETED** |
| **Dual Map Navigation Engine** | Google Maps JS API with permanent key; turn-by-turn routing; user GPS direction link; resizable divider; OSM fallback. | **COMPLETED** |
| **Time-Constrained TSP Optimizer** | NxN distance matrices and traveling salesperson optimization respecting visit durations and opening hours. | **COMPLETED** |
| **Crowd & Festival Intelligence** | Rule-based crowd curves, quiet window suggestions, and festival road closure alerts. | **COMPLETED** |
| **Dynamic Weather Geocoding** | Global coordinate resolution via Open-Meteo for real-time forecast data. | **COMPLETED** |
| **Auth & User Management** | User registration and admin user management with bcrypt hashing and JWT tokens. | **COMPLETED** |
| **Design System & Typography** | Instrument Serif + Plus Jakarta Sans typography; warm sandstone and amber glassmorphism aesthetics. | **COMPLETED** |
