"""
Location domain models.
"""

from typing import Optional
from pydantic import BaseModel, Field


class GeoCoordinates(BaseModel):
    """Geographic coordinates with validation per spec: lat -90..90, lng -180..180."""
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class Location(BaseModel):
    """Location with coordinates and optional name."""
    coordinates: GeoCoordinates
    name: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
