# Monsoon Action Copilot --- 10/10 Implementation Plan

## 1. Product Mission

Build a production-minded, mobile-first **Monsoon Action Copilot** for
individuals, families, and communities in India.

The product must convert **real weather, geospatial context, official
alerts, household context, and deterministic safety rules** into one
clear answer:

> **What should I do now?**

The system must assist citizens:

-   **Before** severe monsoon conditions --- prepare.
-   **During** severe monsoon conditions --- respond.
-   **After** severe monsoon conditions --- recover.

The application is **not** a generic weather dashboard, chatbot, flood
prediction system, or map demo.

The core product is a **hyperlocal, family-aware action engine**.

------------------------------------------------------------------------

# 2. Core Engineering Principle

> **Use deterministic software for facts, risk evidence, thresholds,
> action selection, alert decisions, authorization, and validation. Use
> Gemini for personalization, explanation, conversational interaction,
> and multilingual communication. Never use AI to fabricate missing
> reality.**

The LLM must never independently:

-   Declare an official warning.
-   Claim a road is flooded or closed.
-   Claim a route is safe.
-   Invent weather values.
-   Invent shelters.
-   Invent emergency contacts.
-   Trigger a safety alert.
-   Select arbitrary emergency actions outside the approved action
    catalog.
-   Convert uncertain model evidence into verified fact.

------------------------------------------------------------------------

# 3. Five Core Use Cases

Build these five use cases end-to-end before adding optional features.

## UC-1: Hyperlocal Personal Preparedness Plan

Input:

-   Approximate user location.
-   Household size.
-   Children.
-   Elderly members.
-   Pets.
-   Ground-floor / upper-floor / independent house context.
-   Vehicle availability.
-   Accessibility assistance requirements.
-   Essential medication dependency.

Pipeline:

``` text
Location
   ↓
H3 Risk Cell
   ↓
Environmental Risk Context
   +
Household Profile
   ↓
Household Impact Engine
   ↓
Monsoon Phase
   ↓
Action Engine
   ↓
Approved Actions
   ↓
Gemini Personalization
   ↓
Personal Preparedness Plan
```

Output:

``` json
{
  "environmentalRisk": {
    "level": "HIGH",
    "evidence": []
  },
  "householdImpact": {
    "level": "HIGH",
    "reasons": []
  },
  "phase": "PRE_EVENT",
  "actions": {
    "now": [],
    "next6Hours": [],
    "next24Hours": []
  },
  "emergencyKit": [],
  "limitations": [],
  "updatedAt": "ISO-8601"
}
```

------------------------------------------------------------------------

## UC-2: Live "What Should I Do Now?" Engine

The dashboard must prioritize actions, not weather decoration.

The primary API use case is:

``` text
GET /api/action-plan/current
```

Conceptual pipeline:

``` text
Current Weather
      +
Forecast
      +
Official Alerts
      +
Risk Cell
      +
Household Impact
      +
Monsoon Phase
      ↓
Deterministic Action Engine
      ↓
NOW
NEXT 6 HOURS
NEXT 24 HOURS
```

Example:

``` text
WHAT SHOULD I DO NOW?

1. Prepare essential medication.
2. Charge phones and power banks.
3. Waterproof identity and medical documents.

No verified evacuation alert is currently available.

Updated 2 minutes ago.
```

The Action Engine owns action selection.

Gemini may:

-   Rephrase.
-   Explain why.
-   Personalize wording.
-   Translate.

Gemini must not add unapproved safety actions.

------------------------------------------------------------------------

## UC-3: Family-Aware Emergency Checklist

Generate checklist items from the Action Engine.

Do not maintain a separate AI-generated checklist logic.

``` text
Action Engine
     ↓
Selected Actions
     ↓
Checklist Projection
```

Checklist state:

``` text
PENDING
COMPLETED
NOT_APPLICABLE
```

Requirements:

-   Persist state in PostgreSQL.
-   Survive refresh and backend restart.
-   Preserve completed items when risk changes.
-   Add newly applicable actions.
-   Do not recreate irrelevant items.
-   Record why each item was selected.
-   Record source rule ID.

Example model:

``` json
{
  "id": "uuid",
  "actionId": "PREPARE_ESSENTIAL_MEDICATION",
  "status": "PENDING",
  "sourceRuleId": "ELDERLY_MEDICATION_HIGH_IMPACT",
  "phase": "PRE_EVENT",
  "createdAt": "ISO-8601",
  "completedAt": null
}
```

------------------------------------------------------------------------

## UC-4: Contextual Monsoon Alert Engine

Alerts are deterministic.

``` text
Weather / Official Alert Data
             ↓
Normalize
             ↓
Freshness Validation
             ↓
Risk Cell Evaluation
             ↓
Deterministic Alert Rules
             ↓
Deduplication
             ↓
Cooldown
             ↓
Persist Decision Evidence
             ↓
Optional Gemini Rewrite
             ↓
Citizen Notification
```

The LLM has zero authority over alert triggering.

Every alert must record:

-   Rule ID.
-   Risk cell.
-   Triggering evidence.
-   Evidence source.
-   Source authority.
-   Source timestamp.
-   Evaluation timestamp.
-   Severity.
-   Deduplication key.
-   Expiry.
-   Cooldown.

Deduplication key:

``` text
user_id
+
h3_cell
+
rule_id
+
forecast_window
```

Never repeatedly notify for unchanged conditions.

------------------------------------------------------------------------

## UC-5: Multilingual Grounded Safety Copilot

Supported languages for MVP:

-   English.
-   Tamil.
-   Hindi.

The assistant is an interface to the intelligence platform.

It is not an unrestricted chatbot.

Intent classes:

``` text
GENERAL_PREPAREDNESS
CURRENT_ACTION
WEATHER_CONTEXT
TRAVEL_SAFETY
ESSENTIAL_TRAVEL
ALERT_EXPLANATION
POST_EVENT_RECOVERY
OUT_OF_SCOPE
```

Pipeline:

``` text
User Question
      ↓
Input Validation
      ↓
Intent Classification
      ↓
Retrieve Current User Context
      ↓
Retrieve Risk + Action Evidence
      ↓
Retrieve Trusted Safety Knowledge
      ↓
Fetch Live Data If Required
      ↓
Gemini Structured Response
      ↓
Schema Validation
      ↓
Unsupported Claim Validation
      ↓
Localized Citizen Response
```

Every dynamic response must internally track:

``` json
{
  "liveDataUsed": true,
  "weatherObservedAt": "...",
  "officialAlertUsed": false,
  "evidenceIds": [],
  "limitations": [],
  "language": "ta"
}
```

------------------------------------------------------------------------

# 4. Domain Model

## 4.1 Environmental Risk and Household Impact Must Be Separate

Never combine household vulnerability into environmental severity.

``` text
Environmental Risk
        ≠
Household Impact
```

Example:

``` text
Environmental Risk: HIGH

Household A
2 adults
Upper-floor apartment
Impact: MODERATE

Household B
Elderly member
Ground-floor house
No vehicle
Impact: HIGH
```

Domain models:

``` python
class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class EnvironmentalRisk:
    level: RiskLevel
    evidence: list["RiskEvidence"]
    evaluated_at: datetime
    valid_until: datetime


class HouseholdImpact:
    level: RiskLevel
    reasons: list[str]
    environmental_risk: RiskLevel
```

------------------------------------------------------------------------

## 4.2 Evidence Authority

Every risk claim must preserve source semantics.

``` python
class EvidenceAuthority(str, Enum):
    OFFICIAL_ALERT = "OFFICIAL_ALERT"
    WEATHER_FORECAST = "WEATHER_FORECAST"
    HYDROLOGY_MODEL = "HYDROLOGY_MODEL"
    TERRAIN_DATA = "TERRAIN_DATA"
    HISTORICAL_CONTEXT = "HISTORICAL_CONTEXT"
```

Example:

``` python
class RiskEvidence:
    evidence_type: str
    authority: EvidenceAuthority
    source: str
    observed_at: datetime
    value: float | str | None
    unit: str | None
```

UI language must reflect authority.

Allowed:

> Forecast data indicates elevated rainfall.

Allowed:

> An official severe-weather alert is active.

Not allowed:

> Flood warning active.

unless `EvidenceAuthority.OFFICIAL_ALERT` contains a relevant verified
warning.

------------------------------------------------------------------------

## 4.3 Monsoon Phase

Explicitly model before, during, and after.

``` python
class MonsoonPhase(str, Enum):
    PRE_EVENT = "PRE_EVENT"
    ACTIVE_EVENT = "ACTIVE_EVENT"
    POST_EVENT = "POST_EVENT"
```

Phase classification must be deterministic.

Inputs may include:

-   Current weather.
-   Forecast window.
-   Active official alerts.
-   Recent risk history.
-   Alert expiry.
-   Event recency.

Do not ask Gemini to classify the phase.

------------------------------------------------------------------------

## 4.4 H3 Risk Cell

Use H3 as the hyperlocal spatial indexing layer.

``` python
class RiskCell:
    h3_index: str
    resolution: int
    environmental_risk: EnvironmentalRisk
    evaluated_at: datetime
    valid_until: datetime
```

Pipeline:

``` text
Latitude + Longitude
        ↓
H3 Cell
        ↓
Weather Evidence
        +
Hydrology Evidence
        +
Terrain Evidence
        +
Official Alert Evidence
        ↓
Environmental Risk Engine
```

H3 resolution must be configurable:

``` text
H3_RESOLUTION=8
```

Do not hardcode spatial resolution into domain logic.

------------------------------------------------------------------------

# 5. Action Engine

The Action Engine is the heart of the product.

## Action Catalog

Maintain a reviewed catalog of allowed actions.

Example:

``` python
class Action:
    id: str
    title_key: str
    description_key: str
    phases: set[MonsoonPhase]
    priority: int
    category: str
```

Examples:

``` text
CHARGE_COMMUNICATION_DEVICES
PREPARE_ESSENTIAL_MEDICATION
WATERPROOF_IDENTITY_DOCUMENTS
STORE_DRINKING_WATER
PREPARE_CHILD_ESSENTIALS
PREPARE_PET_SUPPLIES
KEEP_TORCH_ACCESSIBLE
AVOID_UNNECESSARY_TRAVEL
FOLLOW_VERIFIED_EVACUATION_INSTRUCTIONS
AVOID_STANDING_WATER
CHECK_ELECTRICAL_SYSTEM_BEFORE_REUSE
```

## Action Rules

Example:

``` python
ActionRule(
    id="ELDERLY_MEDICATION_HIGH_IMPACT",
    conditions=[
        HouseholdHasElderly(),
        HouseholdRequiresEssentialMedication(),
        MinimumHouseholdImpact(RiskLevel.HIGH),
    ],
    actions=[
        "PREPARE_ESSENTIAL_MEDICATION",
        "WATERPROOF_IDENTITY_DOCUMENTS",
    ],
)
```

Evaluation:

``` text
Risk Context
     +
Household Context
     +
Monsoon Phase
     ↓
Rule Evaluation
     ↓
Action IDs
     ↓
Priority + Deduplication
     ↓
Approved Action Set
```

The Action Engine must be:

-   Pure domain logic.
-   Deterministic.
-   Unit-testable.
-   Independent of FastAPI.
-   Independent of Gemini.
-   Independent of PostgreSQL.

------------------------------------------------------------------------

# 6. Risk Engine

## Inputs

Use available evidence from:

-   Open-Meteo weather forecast.
-   Current weather observations exposed by the provider.
-   Official NDMA/SACHET alerts.
-   Terrain/elevation context where implemented.
-   Hydrology context where implemented.
-   Historical data only as contextual evidence.

## Important Naming Rule

Do not implement:

``` text
FLOOD_RISK = rainfall + soil moisture
```

as a verified flood claim.

Use evidence-oriented rule names:

``` text
HEAVY_RAIN_PREPAREDNESS
EXTREME_RAIN_CONTEXT
HIGH_WIND_CONTEXT
SATURATED_GROUND_HEAVY_RAIN
ELEVATED_HYDROLOGY_CONTEXT
```

An official flood warning is a separate fact:

``` text
OFFICIAL_FLOOD_ALERT_ACTIVE
```

and must come from an authoritative alert source.

## Example Rules

``` yaml
rules:
  - id: HEAVY_RAIN_PREPAREDNESS
    conditions:
      forecast_rainfall_mm_gte: 50
      forecast_window_hours_lte: 24
    risk_level: HIGH

  - id: EXTREME_RAIN_CONTEXT
    conditions:
      forecast_rainfall_mm_gte: 100
      forecast_window_hours_lte: 24
    risk_level: SEVERE

  - id: HIGH_WIND_CONTEXT
    conditions:
      wind_speed_kmph_gte: 60
    risk_level: HIGH
```

Thresholds must be:

-   Configurable.
-   Source-documented.
-   Boundary-tested.
-   Never hidden inside prompts.

------------------------------------------------------------------------

# 7. Geospatial Intelligence

## Required MVP Libraries

Backend:

``` text
h3
geopandas
shapely
openmeteo-requests
```

Travel extension:

``` text
osmnx
networkx
```

Terrain extension:

``` text
rasterio
```

Do not install geospatial libraries without a working product use case.

## Package Structure

``` text
backend/src/
├── domain/
│   ├── geospatial/
│   │   ├── risk_cell.py
│   │   └── spatial_context.py
│   └── rules/
│       └── environmental_risk.py
│
└── infrastructure/
    └── geospatial/
        ├── h3_indexer.py
        ├── geopandas_context.py
        ├── terrain_provider.py
        └── risk_cell_repository.py
```

## Spatial Data Rules

-   Normalize CRS explicitly.
-   Validate latitude and longitude.
-   Record spatial data source.
-   Record dataset version/date where available.
-   Reject stale datasets where freshness is safety-relevant.
-   Do not infer road flooding from polygon overlap without appropriate
    source evidence.

------------------------------------------------------------------------

# 8. Travel Assistance

Travel has two explicit modes.

## Mode A: SHOULD_I_TRAVEL

No routing required.

``` text
Origin Risk Context
        +
Destination Risk Context
        +
Forecast
        +
Official Alerts
        ↓
Travel Advisory Rules
```

Output:

``` json
{
  "recommendation": "AVOID_NON_ESSENTIAL_TRAVEL",
  "reasons": [],
  "verifiedRoadClosureDataAvailable": false,
  "limitations": []
}
```

Never use `SAFE`.

Use:

``` text
LOWER_RISK_CONTEXT
AVOID_NON_ESSENTIAL_TRAVEL
CONDITIONS_UNCERTAIN
ESSENTIAL_TRAVEL_CAUTION
```

## Mode B: ESSENTIAL_TRAVEL

Only invoke route intelligence when essential travel is explicitly
required.

``` text
Origin
   +
Destination
   ↓
OSMnx Road Graph
   +
H3 Risk Cells
   ↓
Risk-Weighted Edge Cost
   ↓
NetworkX
   ↓
Lower-Risk Route Candidate
```

Example:

``` python
edge_cost = travel_time_seconds * (
    1 + risk_penalty_multiplier * edge_risk_score
)
```

The route must be described as:

> Lower-risk route based on currently available data.

Never:

> Safe route.

The API must expose limitations when real road closure or road flooding
data is unavailable.

------------------------------------------------------------------------

# 9. Weather Architecture

Use one normalized weather context.

``` text
Open-Meteo
     ↓
Provider Adapter
     ↓
Normalizer
     ↓
Freshness Validator
     ↓
Redis Cache
     ↓
Normalized Weather Context
     ↓
├── Dashboard
├── Risk Engine
├── Action Engine
├── Alerts
├── Travel
└── Assistant
```

Do not call Open-Meteo independently from every service.

## Weather Model

``` json
{
  "location": {
    "latitude": 11.0168,
    "longitude": 76.9558
  },
  "observedAt": "ISO-8601",
  "forecastGeneratedAt": "ISO-8601",
  "rainfall": {
    "currentMm": 0,
    "next6HoursMm": 0,
    "next24HoursMm": 0
  },
  "precipitationProbability": 0,
  "windSpeedKmph": 0,
  "windGustKmph": 0,
  "soilMoisture": null,
  "source": "open-meteo",
  "dataAgeSeconds": 0
}
```

Cache policy:

``` text
Current context: 5 minutes
Forecast context: 30 minutes
```

Make TTLs configurable.

If unavailable:

> Live weather data is currently unavailable. Recommendations requiring
> current conditions may be limited.

Never synthesize fallback weather.

------------------------------------------------------------------------

# 10. Official Alerts

Official alerts and model/forecast context must remain separate.

``` text
Official Alerts
→ NDMA / SACHET / authoritative CAP or RSS source

Forecast Context
→ Open-Meteo

Hydrology Context
→ Hydrology model/provider

Historical Context
→ Meteostat / IMD-compatible historical dataset
```

Package:

``` text
infrastructure/
└── alerts/
    ├── official_alert_provider.py
    ├── ndma_sachet_client.py
    ├── cap_parser.py
    └── alert_normalizer.py
```

Normalized model:

``` python
class OfficialAlert:
    id: str
    authority_name: str
    event_type: str
    severity: str
    area: str
    issued_at: datetime
    expires_at: datetime | None
    source_url: str
```

Never convert forecast evidence into `OfficialAlert`.

------------------------------------------------------------------------

# 11. Geocoding

Define an abstraction:

``` python
class GeocodingProvider(Protocol):
    async def geocode(self, query: str) -> Location:
        ...

    async def reverse_geocode(
        self,
        latitude: float,
        longitude: float,
    ) -> Location:
        ...
```

MVP implementation:

``` text
NominatimGeocodingProvider
```

Requirements:

-   Identifying User-Agent.
-   Configurable provider URL.
-   Backend rate limiting.
-   Redis caching.
-   Request timeout.
-   Bounded retry.
-   Attribution in UI where required.

Cache:

``` text
geocode:{normalized_query}
TTL = 7 days
```

Frontend location search:

``` text
debounce = 700 ms
minimum characters = 3
```

Never invoke geocoding for every keystroke.

------------------------------------------------------------------------

# 12. Gemini Architecture

## Gemini Role

Gemini is responsible for:

-   Personalized explanations.
-   Citizen-friendly language.
-   Conversation.
-   Intent understanding.
-   Tamil/Hindi/English dynamic communication.
-   Explaining approved actions.
-   Explaining evidence and limitations.

Gemini is not responsible for:

-   Risk thresholds.
-   Alert triggering.
-   Phase classification.
-   Official alert determination.
-   Action selection.
-   Route safety determination.

## Prompt Context

``` text
SYSTEM SAFETY POLICY
+
USER LANGUAGE
+
NORMALIZED WEATHER CONTEXT
+
ENVIRONMENTAL RISK
+
HOUSEHOLD IMPACT
+
MONSOON PHASE
+
APPROVED ACTIONS
+
OFFICIAL ALERTS
+
TRUSTED SAFETY KNOWLEDGE
+
USER QUESTION
```

System rule:

> Never invent weather values, official warnings, road conditions,
> shelters, emergency contacts, or current events. Use only the supplied
> evidence. Do not add safety actions outside APPROVED_ACTIONS. If
> required evidence is absent, explicitly state the limitation.

## Structured Output

``` json
{
  "answer": "...",
  "referencedActionIds": [],
  "referencedEvidenceIds": [],
  "limitations": [],
  "followUpIntent": null
}
```

Validation:

``` text
Gemini Output
      ↓
JSON Schema Validation
      ↓
Action ID Allowlist Validation
      ↓
Evidence Reference Validation
      ↓
Unsupported Current-Fact Detection
      ↓
Render
```

If invalid:

1.  Retry once with correction context.
2.  Return deterministic fallback.

Never display malformed model output.

------------------------------------------------------------------------

# 13. Backend Architecture

``` text
backend/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   ├── middleware/
│   │   └── schemas/
│   │
│   ├── application/
│   │   ├── weather_service.py
│   │   ├── risk_context_service.py
│   │   ├── household_impact_service.py
│   │   ├── action_plan_service.py
│   │   ├── checklist_service.py
│   │   ├── alert_service.py
│   │   ├── assistant_service.py
│   │   └── travel_service.py
│   │
│   ├── domain/
│   │   ├── models/
│   │   │   ├── weather.py
│   │   │   ├── location.py
│   │   │   ├── household.py
│   │   │   ├── risk.py
│   │   │   ├── risk_cell.py
│   │   │   ├── evidence.py
│   │   │   ├── phase.py
│   │   │   ├── action.py
│   │   │   ├── checklist.py
│   │   │   ├── alert.py
│   │   │   └── travel.py
│   │   │
│   │   ├── rules/
│   │   │   ├── environmental_risk.py
│   │   │   ├── household_impact.py
│   │   │   ├── phase_classifier.py
│   │   │   ├── action_rules.py
│   │   │   ├── action_engine.py
│   │   │   ├── alert_rules.py
│   │   │   └── travel_rules.py
│   │   │
│   │   └── exceptions/
│   │
│   ├── infrastructure/
│   │   ├── weather/
│   │   ├── geospatial/
│   │   ├── alerts/
│   │   ├── geocoding/
│   │   ├── llm/
│   │   ├── persistence/
│   │   ├── cache/
│   │   └── knowledge/
│   │
│   ├── security/
│   ├── observability/
│   ├── config.py
│   └── main.py
│
├── tests/
├── alembic/
├── Dockerfile
├── requirements.txt
└── .env.example
```

Dependency direction:

``` text
API
 ↓
Application
 ↓
Domain

Infrastructure
 ↓
implements ports required by Application/Domain
```

The domain layer must not import:

-   FastAPI.
-   SQLAlchemy ORM models.
-   Redis.
-   Gemini SDK.
-   httpx provider clients.

------------------------------------------------------------------------

# 14. API Design

``` text
GET  /api/v1/weather/current
GET  /api/v1/risk/current
GET  /api/v1/action-plan/current

POST /api/v1/household
GET  /api/v1/household

GET  /api/v1/checklist
PATCH /api/v1/checklist/{item_id}

GET  /api/v1/alerts
POST /api/v1/assistant/ask

POST /api/v1/travel/advisory
POST /api/v1/travel/essential-route

GET  /health
GET  /ready
```

Do not expose separate endpoints simply because a provider has an
endpoint.

Design APIs around product use cases.

------------------------------------------------------------------------

# 15. Frontend Product Design

## Primary Dashboard

The first screen must answer:

1.  What is happening?
2.  Is there a verified official alert?
3.  What should I do now?
4.  What should I prepare next?
5.  When was the data updated?

Recommended hierarchy:

``` text
┌────────────────────────────────────┐
│ HIGH HOUSEHOLD IMPACT              │
│ Environmental risk: HIGH           │
│ Updated 2 min ago                  │
│                                    │
│ WHAT SHOULD I DO NOW?              │
│                                    │
│ 1. Prepare essential medication    │
│ 2. Charge communication devices    │
│ 3. Waterproof documents            │
│                                    │
│ [VIEW ALL 7 ACTIONS]               │
│                                    │
│ OFFICIAL ALERT STATUS              │
│ No verified evacuation alert       │
└────────────────────────────────────┘
```

Pages:

``` text
Dashboard
My Plan
Checklist
Ask Copilot
Travel
Settings
```

## UI Rules

Use:

-   Strong typography.
-   High contrast.
-   Severity label + icon + color.
-   Visible timestamps.
-   Source attribution.
-   Explicit degraded states.
-   Large touch targets.
-   Mobile-first layouts.

Avoid:

-   Animated rain.
-   Decorative weather effects.
-   Glassmorphism that reduces contrast.
-   Meaningless charts.
-   Fake map layers.
-   Excessive gradients.
-   Color-only severity indicators.

Accessibility target:

``` text
WCAG 2.2 AA
```

------------------------------------------------------------------------

# 16. Persistence

PostgreSQL stores:

``` text
users
household_profiles
user_locations
risk_evaluations
risk_evidence
action_plans
action_plan_items
checklist_items
official_alerts
alert_decisions
assistant_sessions
```

Redis stores ephemeral/cache state:

``` text
weather:{h3_cell}
forecast:{h3_cell}
geocode:{normalized_query}
risk_context:{h3_cell}
rate_limit:{key}
```

Do not store durable checklist state in Redis.

Do not store persistent state in container memory or local files.

------------------------------------------------------------------------

# 17. Security

Requirements:

-   Centralized Pydantic settings.
-   `.env.example`.
-   No committed secrets.
-   CORS allowlist.
-   Request size limits.
-   Rate limiting.
-   Lat/lng validation.
-   Language enum validation.
-   Text length limits.
-   Server-side resource ownership checks.
-   Structured safe errors.
-   No secrets in Gemini prompts.
-   No API keys in frontend bundles.
-   Prompt injection defense.
-   LLM tool allowlist if tools are introduced.

Do not assume sanitization replaces validation.

Validate structured input by schema and business invariants.

------------------------------------------------------------------------

# 18. Observability

Structured logs to stdout/stderr.

Example:

``` json
{
  "event": "action_plan_generated",
  "requestId": "...",
  "h3Cell": "...",
  "environmentalRisk": "HIGH",
  "householdImpact": "HIGH",
  "phase": "PRE_EVENT",
  "selectedActionCount": 7
}
```

Metrics:

``` text
weather_api_latency
weather_api_error_rate
weather_cache_hit_rate
risk_evaluations_total
risk_level_total
action_rules_evaluated_total
actions_selected_total
alert_rules_evaluated_total
alerts_triggered_total
alerts_deduplicated_total
llm_latency
llm_validation_failure_rate
geocoding_cache_hit_rate
```

Never log:

-   API keys.
-   Auth tokens.
-   Raw passwords.
-   Exact location history unless explicitly required.
-   Full private conversations by default.

------------------------------------------------------------------------

# 19. Testing Strategy

## Unit Tests

Mandatory:

``` text
Environmental risk rules
Household impact rules
Phase classifier
Action rules
Action deduplication
Action prioritization
Alert thresholds
Alert cooldown
Alert deduplication
Weather normalization
Weather freshness
H3 cell indexing
LLM output validation
Evidence reference validation
```

Boundary tests:

``` text
49.9 mm
50.0 mm
50.1 mm
```

For every safety threshold.

## Integration Tests

``` text
Open-Meteo Adapter → Normalizer → Risk Context Service
Risk Cell → Household Impact → Action Engine
Action Engine → Checklist Projection → PostgreSQL
Official Alert Adapter → Normalizer → Alert Engine
Context Builder → Gemini Adapter → Output Validator
Geocoder → Cache → Provider
```

Mock network boundaries.

Do not mock domain business logic in domain integration tests.

## End-to-End Tests

Mandatory flow:

``` text
1. User shares location.
2. Location maps to H3 cell.
3. Real weather context loads.
4. Environmental risk is calculated.
5. Household profile is saved.
6. Household impact is calculated.
7. Monsoon phase is classified.
8. Action plan is generated.
9. Checklist is projected and persisted.
10. User completes an action.
11. Refresh preserves checklist state.
12. Assistant answers from current evidence.
13. Language changes to Tamil.
14. Safety meaning remains equivalent.
15. Alert rule evaluates.
16. Duplicate alert is suppressed.
17. Weather API failure produces degraded state.
```

## False Positive Tests

Every alert rule must test:

``` text
Below threshold
Exact threshold
Above threshold
Stale evidence
Missing evidence
Duplicate event
Active cooldown
Expired official alert
Conflicting evidence
```

An LLM response must never trigger an alert test.

------------------------------------------------------------------------

# 20. Deployment Readiness

Deployment must require only:

``` text
1. Push GitHub repository.
2. Connect frontend deployment.
3. Connect backend deployment.
4. Configure environment variables.
5. Deploy.
```

No source-code changes.

Recommended target:

``` text
Frontend
React + Vite
    ↓
Vercel / Firebase Hosting

Backend
FastAPI
    ↓
Docker
    ↓
Google Cloud Run

Database
Supabase PostgreSQL

Cache
Redis-compatible managed free tier where available
or optional cache degradation

AI
Gemini

Weather
Open-Meteo
```

Important: Redis must be treated as an optimization where possible.

The application should not become completely unusable if Redis is
unavailable.

Fallback:

``` text
Redis Available
→ Cached provider access

Redis Unavailable
→ Bounded direct provider access
→ Log degraded mode
→ Preserve safety validation
```

Backend requirements:

-   Bind to `0.0.0.0`.
-   Read `PORT`.
-   Stateless containers.
-   Production Dockerfile.
-   Non-root runtime user.
-   `/health`.
-   `/ready`.
-   Structured stdout logging.

------------------------------------------------------------------------

# 21. Environment Variables

Example:

``` text
APP_ENV=
PORT=
LOG_LEVEL=

DATABASE_URL=
REDIS_URL=

GEMINI_API_KEY=
GEMINI_MODEL=

OPEN_METEO_BASE_URL=
SACHET_ALERT_URL=
NOMINATIM_BASE_URL=
NOMINATIM_USER_AGENT=

ALLOWED_ORIGINS=

H3_RESOLUTION=

WEATHER_CURRENT_TTL_SECONDS=
WEATHER_FORECAST_TTL_SECONDS=
GEOCODING_TTL_SECONDS=

WEATHER_REQUEST_TIMEOUT_SECONDS=
LLM_REQUEST_TIMEOUT_SECONDS=
GEOCODING_REQUEST_TIMEOUT_SECONDS=

ALERT_DEFAULT_COOLDOWN_MINUTES=
```

Startup must validate required configuration.

Never silently inject fake defaults for required production credentials
or URLs.

------------------------------------------------------------------------

# 22. Build Phases

## Phase 1 --- Intelligence Foundation

Build:

``` text
FastAPI foundation
Configuration
PostgreSQL
Redis abstraction
Open-Meteo adapter
Weather normalizer
H3 indexing
Evidence model
Environmental Risk Engine
Household Impact Engine
Monsoon Phase Classifier
```

Acceptance criteria:

``` text
Location → H3 → Weather → Risk → Household Impact → Phase
```

works end-to-end without Gemini.

------------------------------------------------------------------------

## Phase 2 --- Action Product

Build:

``` text
Action Catalog
Action Rules
Action Engine
Current Action Plan API
Checklist Projection
Checklist Persistence
Primary Dashboard
```

Acceptance criteria:

``` text
User opens app
→ sees genuine current context
→ sees household-specific actions
→ completes checklist
→ refreshes
→ progress remains
```

This phase establishes the core product.

------------------------------------------------------------------------

## Phase 3 --- Safety AI

Build:

``` text
Gemini adapter
Context builder
Structured outputs
Output validator
Evidence reference validator
Intent classifier
Safety Copilot
English / Tamil / Hindi
```

Acceptance criteria:

``` text
Gemini can explain approved actions
but cannot invent actions or unsupported current facts.
```

------------------------------------------------------------------------

## Phase 4 --- Alerts

Build:

``` text
Official alert provider abstraction
SACHET/NDMA adapter
Official alert normalizer
Alert rule engine
Deduplication
Cooldown
Alert history
Citizen-friendly rewriting
```

Acceptance criteria:

``` text
Deterministic condition
→ one alert
→ duplicate evaluation
→ no duplicate notification
```

------------------------------------------------------------------------

## Phase 5 --- Travel

Build:

``` text
SHOULD_I_TRAVEL advisory
Geocoding abstraction
Nominatim adapter
Geocoding cache
ESSENTIAL_TRAVEL intent
OSMnx graph
H3 risk overlay
NetworkX risk-weighted routing
```

Acceptance criteria:

``` text
Normal travel question
→ advisory only

Essential travel
→ lower-risk route candidate
→ explicit limitations
```

Do not build route intelligence before the Action Product works.

------------------------------------------------------------------------

## Phase 6 --- Hardening

Build and verify:

``` text
Accessibility
Mobile usability
Failure states
Rate limits
Security checks
Observability
Docker production build
E2E tests
Deployment configuration
```

------------------------------------------------------------------------

# 23. Definition of Done

A feature is complete only when:

-   [ ] It directly maps to the challenge.
-   [ ] It works end-to-end.
-   [ ] Real data is used where live data is claimed.
-   [ ] Source authority is preserved.
-   [ ] Input validation exists.
-   [ ] External API timeout exists.
-   [ ] Failure state exists.
-   [ ] Loading state exists.
-   [ ] Empty state exists.
-   [ ] Critical domain logic is tested.
-   [ ] Accessibility is checked.
-   [ ] Mobile viewport works.
-   [ ] No production data is hardcoded.
-   [ ] Gemini output is grounded.
-   [ ] Gemini output is validated.
-   [ ] Safety-critical decisions are deterministic.
-   [ ] Logs and metrics exist.
-   [ ] Production build succeeds.
-   [ ] Docker image builds.
-   [ ] Deployment requires no code edits.

------------------------------------------------------------------------

# 24. Pre-Demo Gate

Do not demo until all items pass.

``` text
[ ] Real weather data loads
[ ] Weather source is displayed
[ ] Last updated time is displayed
[ ] H3 risk cell is genuinely calculated
[ ] Environmental risk evidence is inspectable
[ ] Household impact is separate from environmental risk
[ ] Phase is deterministically classified
[ ] Actions come from Action Engine
[ ] Gemini cannot add unknown action IDs
[ ] Checklist persists
[ ] Official alerts are visually distinguished
[ ] No forecast is presented as an official warning
[ ] Alert deduplication works
[ ] Alert cooldown works
[ ] Tamil response preserves safety meaning
[ ] Hindi response preserves safety meaning
[ ] No fake road closure exists
[ ] No route is labelled "safe"
[ ] Weather failure produces degraded state
[ ] Gemini failure produces deterministic fallback
[ ] Redis failure degrades safely
[ ] Mobile flow works
[ ] Keyboard navigation works
[ ] Secrets are not committed
[ ] Frontend production build passes
[ ] Backend tests pass
[ ] Backend Docker image builds
[ ] /health returns 200
[ ] /ready reflects critical dependency readiness
```

------------------------------------------------------------------------

# 25. Demo Story

Use one connected citizen journey.

``` text
Citizen opens application
        ↓
Shares approximate location
        ↓
H3 identifies local risk cell
        ↓
Real weather evidence loads
        ↓
Environmental risk evaluated
        ↓
Citizen adds household context

1 elderly member
1 child
Ground-floor house
No vehicle
Essential medication

        ↓
Household impact evaluated
        ↓
Monsoon phase classified
        ↓
Action Engine selects approved actions
        ↓

"WHAT SHOULD I DO NOW?"

Prepare essential medication
Charge communication devices
Waterproof medical documents

        ↓
Citizen completes checklist items
        ↓
Progress persists
        ↓
Citizen asks in Tamil

"இப்ப வெளிய போகலாமா?"

        ↓
Copilot retrieves live evidence
        ↓
Explains current travel context in Tamil
        ↓
Citizen says hospital travel is essential
        ↓
ESSENTIAL_TRAVEL flow activates
        ↓
Lower-risk route candidate evaluated
        ↓
Copilot explains evidence and limitations
        ↓
Weather context changes
        ↓
Alert rules evaluate
        ↓
One contextual alert is created
        ↓
Duplicate evaluation is suppressed
```

------------------------------------------------------------------------

# 26. Final Product Positioning

> **Monsoon Action Copilot is a hyperlocal, family-aware GenAI system
> that converts real weather, geospatial risk context, and verified
> alerts into personalized actions before, during, and after severe
> monsoon events.**

The differentiation is simple:

``` text
Traditional Weather App
        ↓
"What is happening?"

Monsoon Action Copilot
        ↓
"What should I do now?"
```

## Final Build Rule

> **Do not add another feature until Location → Risk Cell →
> Environmental Risk → Household Impact → Monsoon Phase → Action Engine
> → Checklist works genuinely end-to-end.**

That flow is the product.
