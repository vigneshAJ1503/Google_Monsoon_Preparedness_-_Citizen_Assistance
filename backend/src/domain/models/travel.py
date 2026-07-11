"""
Travel advisory domain model.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TravelRiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    AVOID = "AVOID"


class TravelAdvisory(BaseModel):
    """
    Travel advisory combining weather at origin + destination.
    Per spec: NEVER fabricate road closures. State limitations explicitly.
    """
    origin_name: Optional[str] = None
    destination_name: Optional[str] = None
    risk_level: TravelRiskLevel
    risk_reasons: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    origin_weather_summary: Optional[str] = None
    destination_weather_summary: Optional[str] = None
    active_alerts: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)  # Always state what data is NOT available
    data_sources: list[str] = Field(default_factory=list)
    generated_at: Optional[str] = None
