"""
Household profile domain model.
Collected context used for personalized preparedness plans and checklists.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class HousingType(str, Enum):
    APARTMENT = "apartment"
    INDEPENDENT_HOUSE = "independent_house"
    GROUND_FLOOR = "ground_floor"
    KUTCHA_HOUSE = "kutcha_house"  # Mud/thatched — highly vulnerable
    SLUM = "slum"
    HOUSEBOAT = "houseboat"
    TEMPORARY_SHELTER = "temporary_shelter"


class HouseholdProfile(BaseModel):
    """
    Household context for personalized guidance.
    Per spec: collect only relevant context, filter irrelevant checklist items.
    """
    id: Optional[str] = None
    location_lat: float = Field(ge=-90, le=90)
    location_lng: float = Field(ge=-180, le=180)
    location_name: Optional[str] = None
    household_size: int = Field(ge=1, le=50, default=1)
    has_children: bool = False
    has_elderly: bool = False
    has_pets: bool = False
    pet_details: Optional[str] = None  # "2 dogs, 1 cat"
    housing_type: HousingType = HousingType.APARTMENT
    has_vehicle: bool = False
    vehicle_type: Optional[str] = None  # "car", "two_wheeler", "both"
    accessibility_needs: Optional[str] = None
    preferred_language: str = Field(default="en", pattern="^(en|ta|hi)$")
    floor_level: Optional[int] = None  # Relevant for flooding risk
    near_water_body: bool = False  # River, lake, coast — higher flood risk
