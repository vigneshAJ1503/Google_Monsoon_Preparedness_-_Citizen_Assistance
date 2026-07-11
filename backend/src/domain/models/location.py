"""Location domain models."""


from pydantic import BaseModel, Field


class GeoCoordinates(BaseModel):
    """Geographic coordinates with validation per spec: lat -90..90, lng -180..180."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class Location(BaseModel):
    """Location with coordinates and optional name."""

    coordinates: GeoCoordinates
    name: str | None = None
    district: str | None = None
    state: str | None = None
    country: str = "India"
