# Voyantra 🗺️
**Personalized Worldwide AI Travel Concierge & Dynamic Trip-Planning Engine**

Voyantra is an intelligent, full-stack travel platform designed to help travelers decide **where to go, when to go, and how to get there**. Combining Google Gemini generative intelligence, interactive Google Maps navigation, TSP route optimization, real-time weather forecasting, and cloud persistence with MongoDB Atlas, Voyantra provides seamless travel assistance for destinations across India and worldwide.

---

## ✨ Key Features & Capabilities

### 🌍 Worldwide Travel Assistance & Concierge
- **Global Destination Support**: Plan trips and ask questions about any city, state, country, or landmark worldwide, with deep ground-truth catalog support for pilot corridors in **Pondicherry** and **Chennai**.
- **Dynamic Conversational AI**: Natural multi-turn chat covering attractions, hotels, food scenes, cultural etiquette, and side-by-side destination comparisons in **English, Hindi, and Tamil**.
- **Instant Multilingual Greetings & Fast-Path**: Welcomes travelers warmly in English, Hindi (`नमस्ते!`), and Tamil (`வணக்கம்!`) with actionable starter chips (*"Plan a 2-day trip to Pondicherry"*, *"Top places in Chennai"*, etc.) bypassing unnecessary database scans.
- **In-App Knowledge & Capabilities Engine**: Instant answers to questions about Voyantra's identity, features, and supported travel corridors.
- **Powered by Google Gemini with Auto-Failover**: Uses `GEMINI_MODEL` (default `gemini-3.5-flash`) with automatic fallback to `gemini-3.5-flash-lite` on HTTP 429 rate limits or quota spikes, ensuring uninterrupted concierge interactions. If offline or no key is configured, the system gracefully uses local deterministic fallbacks.

### 📅 Intelligent Multi-Day Itinerary Synthesis
- **Personalized Itineraries (1 to 7 Days)**: Synthesizes structured schedules with morning, afternoon, and evening slots clustered by logical geographical proximity.
- **Strict Dietary & Demographic Personalization**:
  - Pacing tiers: Young Adult, Family, Senior Traveler.
  - Dietary constraints: Pure Veg / Jain (strictly filters zero-onion/garlic breakfast venues), Halal, Vegan, or All.
  - Budget tiers: Budget, Moderate, Luxury.
- **Feasibility & Reality Auditing**: Validates that destinations exist, checks opening hour constraints, and warns against geographically impossible schedules (e.g. snow skiing in tropical coastal towns).

### 🗺️ Dual Map & Navigation Engine
- **Google Maps Integration**:
  - Live JavaScript Maps, Google DirectionsService, and traffic layer (requires your own Google Maps API key, restricted by HTTP referrer).
  - Authentic road routing between stops with maneuver instructions and road distances.
  - **User GPS Navigation**: Bottom-right one-click routing from traveler's live GPS position to any selected itinerary stop with external Google Maps navigation links.
  - **Adjustable Splitter**: Drag-and-drop sliding divider to flexibly adjust the ratio between itinerary cards and map display.
- **OpenStreetMap / Leaflet Fallback**:
  - 100% offline-resilient backup with OSRM road geometry.

### ⚡ Route Optimization & Time-Constrained TSP
- **Traveling Salesperson Problem (TSP) Solver**: Optimizes waypoint sequencing (`/routes/optimize-day`) to minimize total transit distance and travel time.
- **Time Anchors & Windows**: Honors fixed visit anchors (e.g., sunset at beaches, pooja at temples) and venue opening hours.

### ☁️ Cloud Persistence with MongoDB Atlas
- **Live Cloud Connectivity**: Seamlessly connected to MongoDB Atlas (`voyantra_db` on `cluster0`).
- **Collections Persisted**:
  - `users`: User profiles with bcrypt password hashing and role-based access control (`user` vs `admin`).
  - `places`: High-density verified catalog records with GPS coordinates, categories, and etiquette advisories.
  - `hotels`: Verified accommodation options with pricing and amenities.
  - `festivals`: Cultural event calendar with temporal crowd and road closure warnings.
  - `route_cache`: Idempotent route distance caching with 7-day TTL.
  - `crowd_reports` & `feature_snapshots`: Live traveler crowd telemetry with exponential decay.

### 🎨 Modern Typography & UI
- **Refined Typography Pairing**:
  - Headings: `"Instrument Serif"`, Georgia, serif (elegant, editorial warmth).
  - UI & Body: `"Plus Jakarta Sans"`, sans-serif (clean, modern legibility).
- **Aesthetic Palette**: Sandstone canvas (`#FAF8F5`), amber highlights (`#FCD34D`), terracotta accents, and frosted glassmorphism.

### 🏛️ Voyantra Unified Tourism Knowledge Engine (VTKE)
- **Multi-Source Knowledge Ingestion**: Ingests and standardizes records from Wikidata, OpenStreetMap, Wikipedia, and official State Tourism bodies (PTDC & TTDC) with field-level provenance and licence tracking.
- **SSRF-Hardened Crawler**: Socket-level IP pinning, private IP and loopback blocking, redirect revalidation (max 3 hops), and content-hash diffing for Voyantra documentation and pages.
- **Hybrid Multi-Channel Retrieval**: Combines hard constraint filters, independent lexical BM25 token matching, geospatial radius search, and multilingual vector similarity via Reciprocal Rank Fusion (RRF).
- **Process-Safe Vector Indexing**: Single-writer architecture, cross-process atomic file locking (`index.lock`), generation tracking (`index.meta.json`), and atomic shadow swaps (`index_{version}.bin`).
- **Conversational RAG Grounding**: Grounds chat turns with verified citations in English, Hindi, and Tamil, with anti-prompt-injection sanitization and instant rollback via `KNOWLEDGE_RAG_ENABLED`.
- **Candidate Place Adapter**: Feeds candidate knowledge entities to Itinerary Engine V2 with conservative missing-data fallbacks while preserving all 40 scheduling and duplicate elimination rules.

---

## 🏛️ System Architecture

```
Voyantra/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints (auth, chat, recommendations, routes, places, hotels, crowd, festivals, knowledge, preferences)
│   │   ├── core/            # Config, MongoDB connector, geo utilities, auth dependencies, HTTP helpers (client IP)
│   │   ├── data/            # Static city catalog datasets (*_places.json, *_hotels.json, *_festivals.json)
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Gemini LLM, routing, TSP, places, crowd, weather, conversation + knowledge (VTKE) engines
│   │   └── main.py          # FastAPI entrypoint (CORS + router registration)
│   ├── requirements.txt          # Runtime dependencies
│   ├── requirements-optional.txt # Optional: sentence-transformers (pulls in PyTorch)
│   ├── requirements-dev.txt      # Runtime + pytest/httpx
│   ├── run.py                    # Uvicorn dev runner (port 8000)
│   └── .env                      # Backend environment configuration (not committed)
│
├── frontend/
│   ├── public/images/       # Optimised images (WebP photos, resized PNG logos)
│   ├── src/
│   │   ├── components/      # UI components
│   │   ├── context/         # AuthContext & PreferencesContext
│   │   ├── pages/           # Planner, Explore, Hotels, Map, Profile, SignUp, Saved basket (lazy-loaded)
│   │   ├── services/        # VoyantraAPI client
│   │   └── types/           # Taxonomy constants, icons, colors
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── .env                 # Frontend environment configuration (not committed)
│
├── mobile/                  # React Native client
├── tests/                   # pytest suite (run from the repo root)
├── docs/                    # Specifications and design plans
└── README.md
```

---

## ⚙️ Environment Configuration

### Backend (`backend/.env`)
```env
PROJECT_NAME="Voyantra API"
VERSION="1.0.0"
HOST="0.0.0.0"
PORT=8000
DEBUG=True

# Google Gemini API Key (Free Tier)
GEMINI_API_KEY="your_gemini_api_key_here"
GEMINI_MODEL="gemini-3.5-flash"

# MongoDB Atlas Cloud Database
MONGODB_URL="mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority"
MONGODB_DB_NAME="voyantra_db"

# Auth: REQUIRED in production. Generate with: python -c "import secrets; print(secrets.token_urlsafe(48))"
JWT_SECRET_KEY="voyantra_jwt_secret_key_prod_2026_pondicherry_chennai"

# Comma-separated list of allowed browser origins (defaults to localhost dev ports)
CORS_ORIGINS="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

# Set to True ONLY when running behind a trusted reverse proxy / load balancer.
# Rate limiting then keys on X-Forwarded-For instead of the proxy's address.
TRUST_PROXY_HEADERS=False

# Knowledge Engine (VTKE)
KNOWLEDGE_RAG_ENABLED=True
KNOWLEDGE_GEMINI_EMBEDDING_MODEL="models/gemini-embedding-001"
```

### Frontend (`frontend/.env`)
```env
# Google Maps JavaScript API Key (for in-app routing & DirectionsService)
VITE_GOOGLE_MAPS_API_KEY="your_google_maps_api_key_here"

# Voyantra FastAPI Backend API Endpoint
VITE_API_URL="http://localhost:8000/api/v1"
```

---

## 🚀 Getting Started

### Prerequisites
- **Python**: 3.10+
- **Node.js**: 18+
- **MongoDB**: MongoDB Atlas cloud cluster (pre-configured) or local MongoDB instance.

### 1. Start the Backend API
```bash
cd backend
python -m venv .venv
# On Windows: .venv\Scripts\activate | On macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python run.py
```
- **Backend API**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

### 2. Start the Frontend Client
```bash
cd frontend
npm install
npm run dev
```
- **Web App**: `http://localhost:5173`

---

## 🔐 Default Demo Accounts

For instant testing of authentication, profile management, and admin controls:

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Traveler** | `user@voyantra.com` | `user123` | Plan itineraries, chat with AI concierge, save favorites, route navigation |
| **Admin** | `admin@voyantra.com` | `admin123` | Full access, user management dashboard (`/admin/users`), role promotion/deletion |

*Demo accounts are for local development only: disable or change them before deploying.*

**Registration & roles:** `POST /auth/register` always creates a **Traveler** account. The `role` field is ignored, so nobody can self-register as an admin. Admins promote users via `PATCH /auth/users/{id}/role`. Passwords are stored with bcrypt.

**Chat & memory are per-user:** every `/chat/*` endpoint requires a `Bearer` token and is scoped to the signed-in user. Conversations belonging to other users return `404`.

**Rate limiting:** simple in-memory sliding-window limiters live in `recommendations.py` (10 req/min per IP) and `routes.py` (30 req/min per IP). They are per-process, so use a shared store (e.g. Redis) if you run multiple workers.

**Tests:** run the automated test suite from the repository root:
```bash
backend\.venv\Scripts\python.exe -m pytest tests/test_voyantra2_ai.py tests/test_rag_conversation.py -v
```

---

## 📡 API Overview (`/api/v1`)

| Endpoint | Method | Auth | Description |
| :--- | :--- | :--- | :--- |
| `/auth/login` | `POST` | Public | Authenticate and issue a JWT bearer token. |
| `/auth/register` | `POST` | Public | Create a Traveler account (role cannot be chosen). |
| `/auth/users` | `GET` | Admin | List registered users. |
| `/auth/users/{id}/role` | `PATCH` | Admin | Promote/demote a user. |
| `/auth/users/{id}` | `DELETE` | Admin | Delete a user. |
| `/chat/message` | `POST` | User | Conversational concierge turn (English / Hindi / Tamil). |
| `/chat/conversations` | `GET` | User | List your saved conversations. |
| `/chat/memory` | `GET/PUT/DELETE` | User | Read, update or clear your consented memory profile. |
| `/recommendations/chat` | `POST` | Public (rate-limited) | Conversational travel concierge covering destinations worldwide. |
| `/recommendations/generate-itinerary` | `POST` | Public (rate-limited) | Synthesize 1-7 day feasible travel plans with dietary and age constraints. |
| `/routes/plan` | `POST` | Public (rate-limited) | Real road routing between coordinates with maneuver instructions. |
| `/routes/matrix` | `POST` | Public (rate-limited) | NxN distance and duration matrix for multi-stop journeys. |
| `/routes/optimize-day` | `POST` | Public (rate-limited) | Time-constrained TSP optimizer for optimal daily route sequence. |
| `/crowd/city/{city_id}` | `GET` | Public | Seasonal crowd congestion heuristics. |
| `/crowd/report` | `POST` | Optional | Geofenced crowd report (attributed to you if signed in). |
| `/festivals`, `/festivals/active` | `GET` | Public | Festival calendar and currently active festivals. |
| `/festivals/impact` | `GET` | Public | Festival date matching with temple and road closure alerts. |

---

## 📄 License
Open-source academic mini-project built for accessible, transparent, and intelligent travel planning.
