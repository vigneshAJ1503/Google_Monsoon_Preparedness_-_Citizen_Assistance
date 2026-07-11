"""Checklist domain model.
Supports: Pending / Completed / Not Applicable states.
Persists across page refreshes.
"""

from enum import Enum

from pydantic import BaseModel, Field


class ChecklistStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    NOT_APPLICABLE = "not_applicable"


class ChecklistCategory(str, Enum):
    ESSENTIALS = "essentials"
    DOCUMENTS = "documents"
    FOOD_WATER = "food_water"
    MEDICAL = "medical"
    PROPERTY = "property"
    COMMUNICATION = "communication"
    EVACUATION = "evacuation"
    CHILDREN = "children"
    ELDERLY = "elderly"
    PETS = "pets"
    VEHICLE = "vehicle"


class ChecklistItem(BaseModel):
    """Single checklist item with state tracking."""

    id: str | None = None
    title: str
    description: str | None = None
    category: ChecklistCategory
    status: ChecklistStatus = ChecklistStatus.PENDING
    priority: int = Field(ge=0, le=10, default=5)
    weather_context: str | None = (
        None  # Why this item is relevant given current weather
    )
    household_id: str | None = None


class Checklist(BaseModel):
    """Full checklist for a household."""

    household_id: str
    items: list[ChecklistItem] = Field(default_factory=list)
    total_items: int = 0
    completed_items: int = 0
    completion_percent: float = 0.0
