# Monsoon Preparedness & Citizen Assistance

A production-grade, fully free monsoon preparedness and citizen assistance application for Indian citizens. Provides personalized safety guidance, weather-aware recommendations, emergency checklists, and real-time alerts using real weather data, deterministic safety rules, and GenAI-powered personalized guidance.

## 🌟 Features

### 1. **Real-Time Weather & Monsoon Context**
- Live weather from Open-Meteo API (free, no API key)
- Current conditions, 7-day forecast, hourly rainfall
- Monsoon phase detection (Pre-monsoon, Active, Retreating, Northeast)
- Caching with Redis (5min current, 30min forecast)

### 2. **Deterministic Alert Engine** (Zero LLM in Decisions)
- IMD-standard rainfall thresholds (Heavy: ≥50mm, Very Heavy: ≥64.5mm, Extreme: ≥124.5mm)
- Wind alerts (≥60 km/h, ≥90 km/h storm)
- Thunderstorm detection
- Sustained flood risk evaluation
- Cooldown/deduplication (configurable per rule)
- NDMA/SACHET RSS integration for official alerts

### 3. **Personalized Preparedness Plans**
- Household profiling (size, children, elderly, pets, housing type, vehicle, accessibility)
- Risk classification: LOW → MODERATE → HIGH → SEVERE
- Time-phased actions: Immediate / Next 6h / Next 24h
- Emergency kit checklist (context-aware)
- Household-specific actions (children, elderly, pets, vulnerable housing)
- Groq LLM generation with deterministic fallback

### 4. **Persistent Emergency Checklist**
- Context-aware items (weather + household triggered)
- Persistent across sessions (PostgreSQL)
- Progress tracking with completion percentage
- Categories: Essentials, Food/Water, Medical, Documents, Property, Vehicle, Evacuation

### 5. **Weather-Aware Safety Assistant (RAG)**
- Intent classification (Preparedness / Weather / Travel / Emergency)
- Retrieval from NDMA safety guidelines
- Live weather context injection
- Source attribution on every response
- Hallucination detection (blocks unverified claims: road closures, flood timelines, shelter openings)
- Groq LLM with structured output validation

### 6. **Travel Advisory**
- Origin → Destination weather comparison
- Risk levels: LOW / MODERATE / HIGH / AVOID
- Explicit data limitation disclaimers ("Road-level flooding data unavailable")
- Safety recommendations

### 7. **Multilingual Support**
- English, Tamil (தமிழ்), Hindi (हिन्दी)
- Safety-critical translation (preserves severity, numbers, measurements)
- UI i18n + dynamic content translation via Groq

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Nginx Reverse Proxy                       │
│                    (/: frontend, /api/*: backend)                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │  Frontend   │  │   Backend   │  │  PostgreSQL │
    │  (React)    │  │  (FastAPI)  │  │  (Data)     │
    └─────────────┘  └──────┬──────┘  └─────────────┘
                            │
                   ┌────────┴────────┐
                   ▼                 ▼
             ┌─────────────┐   ┌─────────────┐
             │    Redis    │   │  External   │
             │   (Cache)   │   │    APIs     │
             └─────────────┘   │ Open-Meteo  │
                               │ Nominatim   │
                               │ NDMA RSS    │
                               │ Groq API    │
                               └─────────────┘
```

### Backend (FastAPI)
- **Layered Architecture**: Routes → Services → Domain Rules → Infrastructure
- **Deterministic First**: All safety decisions via pure Python rules
- **LLM as Presentation**: Groq only rewrites/formats, never decides
- **Async Throughout**: asyncpg, aioredis, httpx

### Frontend (React + Vite)
- Single-page app with tab navigation
- Tailwind-style CSS variables (dark monsoon theme)
- i18n with 3 languages
- Responsive, mobile-first

---

## 🔧 Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Backend | Python 3.12 + FastAPI | Async, type-safe, auto-docs |
| Frontend | React 18 + Vite | Fast HMR, modern |
| Database | PostgreSQL 16 | Robust, free on Render |
| Cache | Redis 7 | TTL-based weather caching |
| Weather | Open-Meteo | Free, no key, India coverage |
| Geocoding | Nominatim (OSM) | Free reverse geocoding |
| Alerts | NDMA/SACHET RSS | Official Indian alerts |
| LLM | Groq (Llama 3.1 8B) | Free tier, 14.4k req/day |
| Container | Docker + Compose | Local parity with prod |
| CI/CD | GitHub Actions → Render | Auto-deploy on merge |

---

## 🚀 Quick Start (Local)

### Prerequisites
- Docker & Docker Compose
- Groq API key (free at console.groq.com)

### Start Full Stack
```bash
# Clone
git clone https://github.com/your-org/monsoon-prep.git
cd monsoon-prep

# Configure
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Start
docker compose up --build
```

### Access
| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/api/docs |
| Health | http://localhost:8000/api/health |

---

## ☁️ Production Deployment (Render)

### 1. Create Resources in Render Dashboard
1. **PostgreSQL**: New → PostgreSQL → `monsoonprep-db` (Free, Oregon)
2. **Redis**: New → Redis → `monsoonprep-redis` (Free, Oregon)
3. **Backend Web Service**: Connect GitHub repo → Docker → `./backend/Dockerfile`
4. **Frontend Web Service**: Connect GitHub repo → Docker → `./frontend/Dockerfile`

### 2. Configure Backend Environment Variables
| Key | Value |
|-----|-------|
| `DATABASE_URL` | Copy from PostgreSQL "External Database URL" |
| `REDIS_URL` | Copy from Redis "External Connection URL" |
| `GROQ_API_KEY` | Your Groq API key |
| `APP_ENV` | `production` |
| `LOG_LEVEL` | `INFO` |
| `CORS_ORIGINS` | `https://your-frontend.onrender.com` |

### 3. Build Command (Backend)
```bash
pip install -r requirements.txt && alembic upgrade head
```

### 4. Deploy
- Push to `main` → Auto-deploys via Render
- Health check: `https://your-backend.onrender.com/api/health`

---

## 🧪 Testing

### Backend
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
# 14 tests: 9 unit + 5 integration
```

### Frontend E2E (Playwright)
```bash
cd frontend
npm install
npx playwright install
BASE_URL=http://localhost npx playwright test
# 23 tests covering all features + live API verification
```

---

## 📁 Project Structure

```
monsoon-prep/
├── backend/
│   ├── src/
│   │   ├── api/              # HTTP layer
│   │   │   ├── middleware/   # CORS, rate-limit, errors, request-ID
│   │   │   └── routes/       # Weather, Preparedness, Checklist, Assistant, Travel, Alerts, Health
│   │   ├── application/      # Use cases / orchestration
│   │   │   ├── weather_service.py
│   │   │   ├── preparedness_service.py
│   │   │   ├── checklist_service.py
│   │   │   ├── assistant_service.py
│   │   │   ├── travel_service.py
│   │   │   ├── alert_service.py
│   │   │   └── translation_service.py
│   │   ├── domain/           # Pure business logic
│   │   │   ├── models/       # Pydantic domain models
│   │   │   ├── rules/        # Deterministic safety rules
│   │   │   └── exceptions/   # Typed exceptions
│   │   ├── infrastructure/   # External integrations
│   │   │   ├── weather/      # Open-Meteo client + normalizer
│   │   │   ├── llm/          # Groq client + prompts + validator
│   │   │   ├── alerts/       # NDMA RSS client
│   │   │   ├── geocoding/    # Nominatim client
│   │   │   ├── persistence/  # SQLAlchemy + repositories
│   │   │   ├── cache/        # Redis client
│   │   │   └── knowledge/    # NDMA safety guidelines
│   │   ├── observability/    # Structured logging + metrics
│   │   ├── config.py         # Pydantic settings
│   │   └── main.py           # FastAPI app + lifespan
│   ├── tests/                # Unit + integration tests
│   ├── alembic/              # Migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable UI
│   │   ├── pages/            # Page-level (not used - single App.jsx)
│   │   ├── i18n/             # en.json, ta.json, hi.json
│   │   ├── styles/           # CSS design system
│   │   ├── App.jsx           # Main SPA
│   │   └── main.jsx
│   ├── tests/                # Playwright E2E
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── infra/
│   ├── docker/
│   │   ├── postgres/init.sql
│   │   └── redis/redis.conf
│   └── nginx/nginx.conf
├── docker-compose.yml
├── docker-compose.dev.yml
├── Makefile
└── README.md
```

---

## 🔐 Safety & Compliance

- **Deterministic Decisions**: LLM never triggers alerts or classifies risk
- **Hallucination Guard**: Regex patterns block unverified claims (road closures, flood timelines, shelter info)
- **Source Attribution**: Every assistant response cites sources
- **Data Freshness**: Weather data age tracked; stale data flagged
- **Fallback Modes**: Deterministic templates when LLM unavailable
- **Rate Limiting**: 100 req/min per IP
- **Input Validation**: Pydantic on all endpoints

---

## 📊 Monitoring

- **Structured JSON Logs**: Request IDs, latency, error context
- **Prometheus Metrics**: `/metrics` endpoint (Groq latency, cache hit rate, API errors)
- **Health Endpoint**: `/api/health` checks DB, Redis, Groq connectivity

---

## 🤝 Contributing

1. Fork → Create feature branch
2. Add tests for new features
3. Run `make test` (backend) and `npm test` (frontend)
4. PR → Auto-deploys preview on Render
5. Merge to `main` → Production deploy

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Open-Meteo** for free weather API
- **NDMA/SACHET** for official Indian disaster alerts
- **OpenStreetMap/Nominatim** for free geocoding
- **Groq** for free-tier LLM inference
- **Render** for free hosting tier

---

**Built for Indian citizens to stay safe during monsoon season.** 🌧️🛡️