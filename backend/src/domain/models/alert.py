"""Alert domain models.
Alerts are safety-critical — their structure is deterministic, not AI-driven.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class AlertSource(str, Enum):
    WEATHER_RULES = "weather_rules"  # Our deterministic rule engine
    NDMA = "ndma"  # National Disaster Management Authority
    IMD = "imd"  # India Meteorological Department
    MANUAL = "manual"


class AlertRule(BaseModel):
    """Deterministic alert rule definition.
    Per spec: 'The LLM must NOT decide whether an emergency alert should be triggered.'.
    """

    id: str  # e.g., "HEAVY_RAIN_PREPAREDNESS"
    name: str
    description: str
    conditions: dict  # Evaluated deterministically
    severity: AlertSeverity
    cooldown_minutes: int = 180
    message_template: str  # Used for citizen-friendly messaging
    requires_fields: list[str] = Field(default_factory=list)


class Alert(BaseModel):
    """An evaluated and triggered alert."""

    id: str | None = None
    rule_id: str
    severity: AlertSeverity
    title: str
    description: str
    location_lat: float | None = None
    location_lng: float | None = None
    location_name: str | None = None
    source: AlertSource
    source_data: dict | None = None  # The data that triggered this alert
    weather_data_age_seconds: int | None = None
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    is_active: bool = True
    citizen_message: str | None = None  # LLM-rewritten friendly message


class AlertEvaluation(BaseModel):
    """Result of evaluating alert rules against weather data."""

    rule_id: str
    triggered: bool
    severity: AlertSeverity | None = None
    reason: str | None = None
    source_value: float | None = None
    threshold_value: float | None = None
    is_duplicate: bool = False
    is_in_cooldown: bool = False
