"""
Nominatim (OpenStreetMap) geocoding client.
Resolves address/city names to lat/lng coordinates and vice versa.
No API key required. User-Agent header is mandatory.
"""

import httpx
from typing import Dict, Any, Optional
import json

from src.config import settings
from src.domain.models.location import Location, GeoCoordinates
from src.infrastructure.cache.redis_client import redis_manager
from src.observability.logger import get_logger

logger = get_logger(__name__)


class NominatimClient:
    """Async client for OSM Nominatim geocoding services."""

    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org"
        self.headers = {"User-Agent": settings.nominatim_user_agent}
        self.client = httpx.AsyncClient(headers=self.headers, timeout=10.0)

    async def geocode(self, query: str) -> Optional[Location]:
        """Convert address/city name to Location coordinates."""
        cache_key = f"geocode:{query.lower().strip()}"
        cached = await redis_manager.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                logger.info("geocode_cache_hit", query=query)
                return Location(**data)
            except Exception:
                pass

        params = {
            "q": query,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }

        try:
            logger.info("fetching_nominatim_geocode", query=query)
            response = await self.client.get(f"{self.base_url}/search", params=params)
            
            if response.status_code == 200:
                results = response.json()
                if not results:
                    return None

                res = results[0]
                addr = res.get("address", {})
                
                location = Location(
                    coordinates=GeoCoordinates(
                        latitude=float(res["lat"]),
                        longitude=float(res["lon"]),
                    ),
                    name=res.get("display_name"),
                    district=addr.get("district") or addr.get("city_district") or addr.get("county"),
                    state=addr.get("state"),
                    country=addr.get("country", "India"),
                )

                # Cache search results
                await redis_manager.set(
                    cache_key,
                    location.model_dump_json(),
                    ttl=settings.geocoding_cache_ttl_seconds,
                )
                return location

            logger.error("nominatim_geocode_failed", status_code=response.status_code)
            return None

        except Exception as e:
            logger.error("nominatim_geocode_error", query=query, error=str(e))
            return None

    async def reverse_geocode(self, lat: float, lng: float) -> Optional[Location]:
        """Convert lat/lng coordinates to a human-readable Location."""
        cache_key = f"reverse_geocode:{round(lat, 4)}:{round(lng, 4)}"
        cached = await redis_manager.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                logger.info("reverse_geocode_cache_hit", lat=lat, lng=lng)
                return Location(**data)
            except Exception:
                pass

        params = {
            "lat": lat,
            "lon": lng,
            "format": "json",
            "addressdetails": 1,
        }

        try:
            logger.info("fetching_nominatim_reverse", lat=lat, lng=lng)
            response = await self.client.get(f"{self.base_url}/reverse", params=params)
            
            if response.status_code == 200:
                res = response.json()
                addr = res.get("address", {})
                
                # Deduce name
                name = res.get("display_name")
                
                location = Location(
                    coordinates=GeoCoordinates(latitude=lat, longitude=lng),
                    name=name,
                    district=addr.get("district") or addr.get("city") or addr.get("county"),
                    state=addr.get("state"),
                    country=addr.get("country", "India"),
                )

                # Cache
                await redis_manager.set(
                    cache_key,
                    location.model_dump_json(),
                    ttl=settings.geocoding_cache_ttl_seconds,
                )
                return location

            logger.error("nominatim_reverse_failed", status_code=response.status_code)
            return None

        except Exception as e:
            logger.error("nominatim_reverse_error", lat=lat, lng=lng, error=str(e))
            return None

    async def close(self):
        """Close connection pools."""
        await self.client.aclose()


# Singleton
nominatim_client = NominatimClient()
