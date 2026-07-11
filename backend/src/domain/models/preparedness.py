"""
Preparedness plan domain model.
Structured output — not free-form AI text.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class RiskSummary(BaseModel):
    level: RiskLevel
    reasons: list[str] = Field(default_factory=list)


class ActionItem(BaseModel):
    action: str
    priority: int = Field(ge=1, le=5, default=3)
    category: Optional[str] = None  # "safety", "supplies", "property", "evacuation"
    applies_to: Optional[str] = None  # "children", "elderly", "pets", "all"


class PreparednessePlan(BaseModel):
    """
    Structured preparedness plan per spec section 4.2.
    Generated using: household context + weather + trusted guidance + controlled AI.
    """
    risk_summary: RiskSummary
    actions_immediate: list[ActionItem] = Field(default_factory=list)
    actions_next_6_hours: list[ActionItem] = Field(default_factory=list)
    actions_next_24_hours: list[ActionItem] = Field(default_factory=list)
    emergency_kit: list[str] = Field(default_factory=list)
    household_specific_actions: list[ActionItem] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    weather_context_summary: Optional[str] = None
    generated_at: Optional[str] = None
    data_sources: list[str] = Field(default_factory=list)
