"""
NDMA/SACHET RSS feed client for official government disaster warnings.
Per spec: 'invent API responses when an upstream service fails' -> MUST NOT.
Fail safely when data is unavailable.
"""

import httpx
import feedparser
from datetime import datetime, timezone
from typing import List, Dict, Any

from src.domain.models.alert import Alert, AlertSeverity, AlertSource
from src.observability.logger import get_logger

logger = get_logger(__name__)


class NDMAClient:
    """Client for pulling official government alerts from SACHET NDMA feeds."""

    def __init__(self):
        # SACHET RSS feeds URL
        self.feed_url = "https://sachet.ndma.gov.in/feed"
        self.client = httpx.AsyncClient(timeout=10.0)

    async def fetch_official_alerts(self) -> List[Alert]:
        """Fetch and parse current disaster alerts."""
        try:
            logger.info("fetching_sachet_alerts", url=self.feed_url)
            response = await self.client.get(self.feed_url)
            
            if response.status_code != 200:
                logger.warning("sachet_feed_http_error", status_code=response.status_code)
                return []

            # Parse RSS feed
            feed = feedparser.parse(response.text)
            alerts = []

            for entry in feed.entries:
                # Deduce severity from content or title keywords
                title = entry.get("title", "")
                summary = entry.get("summary", "") or entry.get("description", "")
                
                severity = AlertSeverity.LOW
                title_lower = title.lower()
                if "severe" in title_lower or "extreme" in title_lower or "red alert" in title_lower:
                    severity = AlertSeverity.SEVERE
                elif "heavy rain" in title_lower or "warning" in title_lower or "orange alert" in title_lower:
                    severity = AlertSeverity.HIGH
                elif "moderate" in title_lower or "yellow alert" in title_lower:
                    severity = AlertSeverity.MODERATE

                # Parse coordinates if available in feed tags (e.g. georss:point)
                lat, lng = None, None
                if "georss_point" in entry:
                    try:
                        lat_str, lng_str = entry["georss_point"].split()
                        lat = float(lat_str)
                        lng = float(lng_str)
                    except Exception:
                        pass

                alerts.append(
                    Alert(
                        rule_id="OFFICIAL_NDMA_ALERT",
                        severity=severity,
                        title=title,
                        description=summary,
                        location_lat=lat,
                        location_lng=lng,
                        location_name=entry.get("tags", [{}])[0].get("term") if entry.get("tags") else None,
                        source=AlertSource.NDMA,
                        source_data=dict(entry),
                        triggered_at=datetime.utcnow(),
                        expires_at=None,  # Handled by feed updates
                        is_active=True,
                    )
                )

            logger.info("sachet_alerts_fetched", count=len(alerts))
            return alerts

        except Exception as e:
            # Safe degradation: do not throw exception, just log and return empty
            logger.error("ndma_feed_parsing_failed_degrading_safely", error=str(e))
            return []

    async def close(self):
        """Close connection pools."""
        await self.client.aclose()


# Singleton
ndma_client = NDMAClient()
