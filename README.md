# Voyantra 🗺️
**Personalized Worldwide AI Travel Concierge & Dynamic Trip-Planning Engine**

Voyantra is an intelligent, full-stack travel platform designed to help travelers decide **where to go, when to go, and how to get there**. Combining Google Gemini generative intelligence, interactive Google Maps navigation, TSP route optimization, real-time weather forecasting, and cloud persistence with MongoDB Atlas, Voyantra provides seamless travel assistance for destinations across India and worldwide.

---

## ✨ Key Features & Capabilities

### 🌍 Worldwide Travel Assistance & Concierge
- **Global Destination Support**: Plan trips and ask questions about any city, state, country, or landmark worldwide (e.g., Pondicherry, Chennai, Mumbai, Jaipur, Himachal Pradesh, Tokyo, Paris, Bali, Dubai, Kyoto).
- **Dynamic Conversational AI**: Natural multi-turn chat covering attractions, hotels, food scenes, cultural etiquette, and side-by-side destination comparisons.
- **Powered by Google Gemini 3.5 Flash**: Configured with Google's balanced `gemini-3.5-flash` model, operating comfortably within free-tier limits (15 RPM / 1,500 RPD) with fallback to local heuristic synthesis.

### 📅 Intelligent Multi-Day Itinerary Synthesis
- **Personalized Itineraries (1 to 7 Days)**: Synthesizes structured schedules with morning, afternoon, and evening slots clustered by logical geographical proximity.
- **Strict Dietary & Demographic Personalization**:
  - Pacing tiers: Young Adult, Family, Senior Traveler.
  - Dietary constraints: Pure Veg / Jain (strictly filters zero-onion/garlic breakfast venues), Halal, Vegan, or All.
  - Budget tiers: Budget, Moderate, Luxury.
- **Feasibility & Reality Auditing**: Validates that destinations exist, checks opening hour constraints, and warns against geographically impossible schedules (e.g. snow skiing in tropical coastal towns).

### 🗺️ Dual Map & Navigation Engine
- **Google Maps Integration**:
  - Pre-configured with permanent API key for live JavaScript Maps, Google DirectionsService, and traffic layer.
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

---

## 🏛️ System Architecture

```
Voyantra/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints (auth, recommendations, routes, places, hotels, crowd, festivals)
│   │   ├── core/            # Config, MongoDB Atlas connector, geo utilities, auth dependencies
│   │   ├── data/            # Static high-density city catalog datasets (*_places.json, *_hotels.json)
│   │   ├── models/          # Entity models
│   │   ├── schemas/         # Pydantic schemas (auth, route, itinerary, place, crowd)
│   │   ├── services/        # Gemini LLM, routing engine, places, crowd heuristics, weather service
│   │   └── main.py          # FastAPI application entrypoint with CORS & rate limiting
│   ├── requirements.txt
│   ├── run.py               # Uvicorn dev runner (port 8000)
│   └── .env                 # Backend environment configuration
│
├── frontend/
│   ├── src/
│   │   ├── components/      # UI components (GoogleMapsRouteView, Navbar, PlaceCard, HotelCard, Modals)
│   │   ├── context/         # AuthContext & PreferencesContext (global state & live GPS)
│   │   ├── pages/           # Landing, Planner, Explore, Hotels, MapPage, AdminUsers, SignUpPage
│   │   ├── services/        # VoyantraAPI client (FastAPI integration + offline fallback)
│   │   └── types/           # Taxonomy constants, icons, colors
│   ├── package.json
│   ├── tailwind.config.js   # Custom font families & color themes
│   ├── vite.config.js
│   └── .env                 # Frontend environment configuration
│
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
MONGODB_URL="mongodb+srv://<username>:<password>@cluster0.hqayaiu.mongodb.net/?retryWrites=true&w=majority"
MONGODB_DB_NAME="voyantra_db"
```

### Frontend (`frontend/.env`)
```env
# Google Maps JavaScript API Key (for in-app routing & DirectionsService)
VITE_GOOGLE_MAPS_API_KEY="your_google_maps_api_key_here"
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

*New traveler registrations are dynamically saved to MongoDB Atlas in the cloud with bcrypt password hashing.*

---

## 📡 API Overview (`/api/v1`)

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/recommendations/chat` | `POST` | Conversational travel concierge covering destinations worldwide. |
| `/recommendations/generate-itinerary` | `POST` | Synthesize 1–7 day feasible travel plans with dietary and age constraints. |
| `/routes/plan` | `POST` | Real road routing between coordinates with maneuver instructions. |
| `/routes/matrix` | `POST` | NxN distance and duration matrix for multi-stop journeys. |
| `/routes/optimize-day` | `POST` | Time-constrained TSP optimizer for optimal daily route sequence. |
| `/crowd/city/{city_id}` | `GET` | Real-time and seasonal crowd congestion heuristics. |
| `/festivals/impact` | `GET` | Festival date matching with temple/road closure alerts. |
| `/auth/login` | `POST` | Authenticate user and issue JWT bearer token. |
| `/auth/register` | `POST` | Register a new user in MongoDB Atlas. |
| `/auth/admin/users` | `GET` | Retrieve list of registered users (Admin only). |

---

## 📄 License
Open-source academic mini-project built for accessible, transparent, and intelligent travel planning.
