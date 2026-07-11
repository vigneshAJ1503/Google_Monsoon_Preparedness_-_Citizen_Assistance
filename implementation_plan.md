# Monsoon Preparedness App — Implementation Plan

## Goal

Build a **production-grade, fully free, end-to-end monsoon preparedness and citizen assistance application** with a Python backend, modern frontend, and Docker Compose infrastructure. The app helps Indian citizens prepare for, survive, and recover from monsoon events using real weather data, deterministic safety rules, and GenAI-powered personalized guidance.

---

## Tech Stack (100% Free)

| Layer | Technology | Why |
|-------|-----------|-----|
| **Backend** | Python 3.12 + FastAPI | Async, auto-docs, Pydantic schemas, production-grade |
| **Frontend** | React 18 + Vite | Fast dev, modern SPA, rich ecosystem |
| **Database** | PostgreSQL 16 | Robust, free, handles structured data well |
| **Cache** | Redis 7 | TTL-based weather caching, session state |
| **LLM** | Google Gemini 2.5 Flash (free tier) | Structured JSON output, fast, 15 RPM free |
| **Weather API** | Open-Meteo | Free, no API key, forecast + historical, India coverage |
| **Maps** | Leaflet.js + OpenStreetMap | Free tiles, interactive, weather overlays |
| **Geocoding** | Nominatim (OSM) / geopy | Free reverse/forward geocoding |
| **Official Alerts** | SACHET (NDMA) RSS + Open-Meteo alerts | Government disaster alerts |
| **Monsoon Data** | Meteostat + IMDLIB | Historical monsoon patterns, IMD gridded data |
| **Containerization** | Docker + Docker Compose | Local dev orchestration |
| **Testing** | pytest + Vitest | Backend + frontend testing |
| **Reverse Proxy** | Nginx | Production-like routing in Docker |

---

## Project Structure

```
MonsoonPrep/
├── frontend/                          # React + Vite SPA
│   ├── public/
│   │   ├── favicon.ico
│   │   └── manifest.json
│   ├── src/
│   │   ├── assets/                    # Static assets (icons, images)
│   │   ├── components/                # Reusable UI components
│   │   │   ├── common/                # Buttons, Cards, Loaders, Alerts
│   │   │   ├── weather/               # WeatherCard, ForecastChart, RainGauge
│   │   │   ├── map/                   # MapView, WeatherOverlay, LocationPicker
│   │   │   ├── preparedness/          # PlanCard, RiskBadge, ActionList
│   │   │   ├── checklist/             # ChecklistItem, ChecklistProgress
│   │   │   ├── assistant/             # ChatBubble, ChatInput, SourceBadge
│   │   │   ├── alerts/                # AlertBanner, AlertHistory, SeverityIcon
│   │   │   └── travel/                # TravelForm, RouteInfo, TravelRiskCard
│   │   ├── pages/                     # Page-level components
│   │   │   ├── Dashboard.jsx          # Main home/dashboard
│   │   │   ├── Preparedness.jsx       # Preparedness plan page
│   │   │   ├── Checklist.jsx          # Emergency checklist
│   │   │   ├── Assistant.jsx          # Safety chat assistant
│   │   │   ├── Travel.jsx             # Travel advisory
│   │   │   └── Settings.jsx           # Language, location, household
│   │   ├── hooks/                     # Custom React hooks
│   │   ├── services/                  # API client functions
│   │   ├── context/                   # React Context (language, theme, location)
│   │   ├── utils/                     # Formatters, validators, constants
│   │   ├── i18n/                      # Translation files (en, ta, hi)
│   │   │   ├── en.json
│   │   │   ├── ta.json
│   │   │   └── hi.json
│   │   ├── styles/                    # CSS design system
│   │   │   ├── index.css              # Global styles + CSS variables
│   │   │   ├── components.css         # Component styles
│   │   │   └── pages.css              # Page-level styles
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── nginx.conf                     # Prod nginx config for SPA
│   ├── package.json
│   └── vite.config.js
│
├── backend/                           # Python FastAPI
│   ├── src/
│   │   ├── api/                       # HTTP layer
│   │   │   ├── routes/
│   │   │   │   ├── weather.py         # GET /api/weather
│   │   │   │   ├── preparedness.py    # POST /api/preparedness/plan
│   │   │   │   ├── checklist.py       # GET/POST /api/checklist
│   │   │   │   ├── assistant.py       # POST /api/assistant/ask
│   │   │   │   ├── travel.py          # POST /api/travel/advisory
│   │   │   │   ├── alerts.py          # GET /api/alerts
│   │   │   │   └── health.py          # GET /api/health
│   │   │   ├── middleware/
│   │   │   │   ├── error_handler.py   # Global exception → safe response
│   │   │   │   ├── rate_limiter.py    # Request rate limiting
│   │   │   │   ├── cors.py            # CORS configuration
│   │   │   │   └── request_id.py      # Correlation ID injection
│   │   │   └── schemas/
│   │   │       ├── weather.py         # Request/response Pydantic models
│   │   │       ├── preparedness.py
│   │   │       ├── checklist.py
│   │   │       ├── assistant.py
│   │   │       ├── travel.py
│   │   │       └── alerts.py
│   │   │
│   │   ├── application/               # Use cases / business logic orchestration
│   │   │   ├── weather_service.py     # Fetch, normalize, cache weather
│   │   │   ├── preparedness_service.py # Generate preparedness plans
│   │   │   ├── checklist_service.py   # Generate & manage checklists
│   │   │   ├── assistant_service.py   # RAG pipeline for safety Q&A
│   │   │   ├── travel_service.py      # Travel advisory generation
│   │   │   ├── alert_service.py       # Alert evaluation & management
│   │   │   └── translation_service.py # Multilingual output
│   │   │
│   │   ├── domain/                    # Pure business logic (no framework deps)
│   │   │   ├── models/
│   │   │   │   ├── weather.py         # WeatherObservation, Forecast, etc.
│   │   │   │   ├── location.py        # Location, GeoCoordinates
│   │   │   │   ├── household.py       # HouseholdProfile
│   │   │   │   ├── preparedness.py    # PreparednessePlan, RiskLevel
│   │   │   │   ├── checklist.py       # ChecklistItem, ChecklistStatus
│   │   │   │   ├── alert.py           # Alert, AlertSeverity, AlertRule
│   │   │   │   └── travel.py          # TravelAdvisory, RouteRisk
│   │   │   ├── rules/
│   │   │   │   ├── alert_rules.py     # Deterministic alert threshold rules
│   │   │   │   ├── risk_classifier.py # Risk level classification logic
│   │   │   │   └── monsoon_season.py  # Monsoon season detection (June-Sept)
│   │   │   └── exceptions/
│   │   │       ├── weather.py         # WeatherProviderUnavailable, StaleData
│   │   │       ├── llm.py             # InvalidAIResponse, LLMTimeout
│   │   │       └── validation.py      # InvalidInput, UnsupportedLocation
│   │   │
│   │   ├── infrastructure/            # External integrations
│   │   │   ├── weather/
│   │   │   │   ├── open_meteo.py      # Open-Meteo API client
│   │   │   │   ├── meteostat_client.py # Historical weather via Meteostat
│   │   │   │   └── weather_normalizer.py # Normalize to internal schema
│   │   │   ├── llm/
│   │   │   │   ├── gemini_client.py   # Google Gemini API client
│   │   │   │   ├── prompt_templates.py # System prompts, safety instructions
│   │   │   │   ├── output_validator.py # JSON schema + safety validation
│   │   │   │   └── context_builder.py # Build grounded context for LLM
│   │   │   ├── alerts/
│   │   │   │   ├── ndma_client.py     # SACHET/NDMA RSS feed parser
│   │   │   │   └── alert_normalizer.py # Normalize official alerts
│   │   │   ├── geocoding/
│   │   │   │   └── nominatim_client.py # OSM Nominatim geocoding
│   │   │   ├── persistence/
│   │   │   │   ├── database.py        # SQLAlchemy engine + session
│   │   │   │   ├── models.py          # ORM models
│   │   │   │   └── repositories.py    # Data access layer
│   │   │   ├── cache/
│   │   │   │   └── redis_client.py    # Redis cache with TTL
│   │   │   └── knowledge/
│   │   │       └── safety_knowledge.py # Trusted preparedness content
│   │   │
│   │   ├── security/
│   │   │   ├── input_validator.py     # Lat/lng, text length, enum validation
│   │   │   └── sanitizer.py          # Input sanitization
│   │   │
│   │   ├── observability/
│   │   │   ├── logger.py              # Structured JSON logging
│   │   │   └── metrics.py             # Prometheus-compatible metrics
│   │   │
│   │   ├── config.py                  # Centralized configuration
│   │   └── main.py                    # FastAPI app entry point
│   │
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_alert_rules.py
│   │   │   ├── test_risk_classifier.py
│   │   │   ├── test_weather_normalizer.py
│   │   │   ├── test_monsoon_season.py
│   │   │   └── test_output_validator.py
│   │   ├── integration/
│   │   │   ├── test_weather_service.py
│   │   │   ├── test_alert_service.py
│   │   │   └── test_preparedness_service.py
│   │   └── conftest.py
│   │
│   ├── alembic/                       # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── infra/                             # Infrastructure configs
│   ├── docker/
│   │   ├── postgres/
│   │   │   └── init.sql               # Initial DB schema
│   │   └── redis/
│   │       └── redis.conf             # Redis configuration
│   ├── nginx/
│   │   └── nginx.conf                 # Reverse proxy config
│   └── scripts/
│       ├── start.sh                   # Dev startup script
│       └── seed_data.sh               # Seed safety knowledge data
│
├── docker-compose.yml                 # Full stack orchestration
├── docker-compose.dev.yml             # Dev overrides (hot reload)
├── .env.example                       # Environment variable template
├── .gitignore
├── Makefile                           # Common commands
├── README.md                          # Project documentation
└── MONSOON_ENGINEERING_BUILD_SPEC.md  # Original spec
```

---

## Proposed Changes

### Phase 1: Foundation (Infrastructure + Weather)

#### Backend Core

##### [NEW] [main.py](file:///Users/Vignesh/MonsoonPrep/backend/src/main.py)
FastAPI application entry point with CORS, error handling, middleware, route registration.

##### [NEW] [config.py](file:///Users/Vignesh/MonsoonPrep/backend/src/config.py)
Centralized Pydantic settings: API URLs, cache TTLs, rate limits, Gemini API key, DB URL, Redis URL.

##### [NEW] Domain Models
All Pydantic models for: `WeatherObservation`, `Forecast`, `Location`, `HouseholdProfile`, `Alert`, `AlertRule`, `RiskLevel`, `ChecklistItem`, `PreparednessePlan`, `TravelAdvisory`.

##### [NEW] Weather Infrastructure
- `open_meteo.py` — Async httpx client for Open-Meteo (current + 7-day forecast + hourly rain)
- `meteostat_client.py` — Historical monsoon data for trend comparison
- `weather_normalizer.py` — Normalize all providers to internal schema with `dataAgeSeconds`, `source`, staleness detection
- `redis_client.py` — TTL-based caching (5 min for current, 30 min for forecast)

##### [NEW] Deterministic Rules Engine
- `alert_rules.py` — YAML-like rule definitions evaluated deterministically:
  - `HEAVY_RAIN_PREPAREDNESS`: forecast_rainfall ≥ 50mm/24h → HIGH
  - `EXTREME_RAIN_EMERGENCY`: forecast_rainfall ≥ 100mm/24h → SEVERE
  - `HIGH_WIND_WARNING`: wind_speed ≥ 60 kmph → HIGH
  - `FLOOD_RISK`: sustained rainfall + soil moisture → HIGH
- `risk_classifier.py` — Combine weather + household → LOW/MODERATE/HIGH/SEVERE
- `monsoon_season.py` — Detect active monsoon (June 1 – Sept 30 for most of India, with regional variation)

---

### Phase 2: GenAI Integration (Preparedness + Checklist + Assistant)

##### [NEW] LLM Infrastructure
- `gemini_client.py` — Google Gemini client with structured JSON output, timeout, retry, token limits
- `prompt_templates.py` — System safety prompt + per-feature prompts with grounding instructions
- `output_validator.py` — JSON schema validation + safety claim detection + hallucination guard
- `context_builder.py` — Assemble: system prompt + weather context + alerts + user profile + question

##### [NEW] Preparedness Service
- Collects household profile + current weather + forecast
- Sends grounded context to Gemini with structured output schema
- Returns: risk summary, immediate/6h/24h actions, emergency kit, household-specific actions
- Falls back to deterministic template if LLM fails

##### [NEW] Checklist Service
- Generates context-aware checklist items based on household + weather
- Supports: Pending / Completed / Not Applicable states
- Persists state in PostgreSQL (survives refresh)
- Filters irrelevant items (no pet items if no pets)

##### [NEW] Safety Assistant
- Intent classification: General Preparedness / Weather Question / Travel / Emergency
- RAG pipeline: retrieve trusted safety content → inject weather context → generate grounded response
- Every response includes: source, data timestamp, confidence, live-data flag
- Explicit uncertainty statements when data is missing

---

### Phase 3: Travel + Alerts + Multilingual

##### [NEW] Travel Advisory Service
- Combines: current weather at origin + destination, forecast, active alerts
- Never fabricates road closures — explicitly states data limitations
- Uses Nominatim for destination geocoding

##### [NEW] Alert Engine
- Deterministic evaluation against rule set
- Deduplication by rule ID + location + time window
- Cooldown periods (configurable per rule, default 180 min)
- Source freshness validation (reject data older than threshold)
- NDMA/SACHET RSS parsing for official government alerts
- LLM rewrites validated alerts into citizen-friendly language (never decides IF to alert)

##### [NEW] Multilingual Service
- 3 languages: English, Tamil (தமிழ்), Hindi (हिन्दी)
- Translation via Gemini with safety-preserving instructions
- Preserves: severity, numbers, times, measurements, warning terminology
- Frontend i18n files for static UI text
- Dynamic content translated on-demand

---

### Phase 4: Frontend + Integration + Polish

##### [NEW] Frontend SPA
- **Dashboard**: Current conditions, alert status, risk level, actions, checklist preview, assistant CTA
- **Interactive Map**: Leaflet + OSM tiles, weather overlay, location picker, rainfall visualization
- **Preparedness Page**: Household form → personalized plan with risk badge
- **Checklist Page**: Interactive checklist with progress bar, persistence
- **Assistant Page**: Chat interface with source attribution, data timestamps
- **Travel Page**: Origin/destination form, weather comparison, risk assessment
- **Settings**: Language selector, location, household profile management

##### [NEW] Design System
- Premium dark theme with monsoon-inspired color palette (deep blues, teals, warning ambers)
- Glassmorphism cards, smooth gradients
- Severity-aware styling (color + text labels for accessibility)
- Micro-animations (rain effect, loading states)
- Mobile-first responsive design
- Google Fonts (Inter for UI, Noto Sans Tamil/Devanagari for Indian languages)

##### [NEW] Infrastructure
- `docker-compose.yml`: PostgreSQL + Redis + Backend + Frontend + Nginx
- `docker-compose.dev.yml`: Hot reload for both frontend and backend
- `Makefile`: `make dev`, `make test`, `make build`, `make seed`
- Nginx reverse proxy: `/api/*` → backend, `/*` → frontend

---

## Key Architecture Decisions

### 1. LLM as Presentation Layer, Not Decision Engine
```
Weather Data → Deterministic Rules → Alert Decision → LLM Rewrites Alert Text
                                                       ↑ NOT ↑
                                              LLM decides if alert fires
```

### 2. Weather Data Flow
```
Open-Meteo API → Normalize → Redis Cache (5min TTL) → Internal Schema
                                  ↓
                    Reused across: Dashboard, Plans, Alerts, Travel, Chat
```

### 3. Safety-First Response Pipeline
```
User Input → Sanitize → Classify Intent → Retrieve Trusted Context
    → Fetch Live Weather → Apply Safety Policy → LLM Generate
    → Validate Output → Render (with source attribution)
```

### 4. Alert Engine (Zero LLM Involvement in Decisions)
```
Weather Data → Validate Freshness → Evaluate Rules → Dedup
    → Classify Severity → Record Source → Cooldown Check → Notify
    → (Optional) LLM Rewrites for Citizen-Friendly Language
```

---

## Open Questions

> [!IMPORTANT]
> **Gemini API Key**: You'll need a free Gemini API key from [Google AI Studio](https://aistudio.google.com/). Do you have one, or shall I add instructions for obtaining one?

> [!NOTE]
> **Scope Confirmation**: This plan covers all 7 features. The build order prioritizes the 4 critical features first (Weather, Preparedness, Checklist, Alerts), with Travel, Assistant, and Multilingual following. Are you OK with this phased approach?

---

## Verification Plan

### Automated Tests
```bash
# Backend unit tests (alert rules, risk classification, weather normalization)
cd backend && pytest tests/unit/ -v

# Backend integration tests (service layer with mocked external APIs)
cd backend && pytest tests/integration/ -v

# Frontend component tests
cd frontend && npx vitest run
```

### Manual Verification
- Docker Compose full stack startup: `docker compose up --build`
- Dashboard loads with real weather data for Coimbatore
- Alert engine fires on heavy rain forecast
- Preparedness plan generates with household context
- Checklist persists across page refreshes
- Assistant returns grounded responses with source attribution
- Language switching works (English → Tamil → Hindi)
- Mobile viewport is usable
- API returns safe error messages when weather API is down
