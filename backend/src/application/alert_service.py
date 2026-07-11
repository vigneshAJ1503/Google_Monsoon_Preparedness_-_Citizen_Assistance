"""Alert Service.
Manages deterministic alert rules execution, deduplication, cooldowns,
NDMA integrations, and optional citizen-friendly rewrites.
"""

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.weather_service import weather_service
from src.domain.models.alert import Alert, AlertSource
from src.domain.rules.alert_rules import (
    evaluate_all_rules,
    format_alert_message,
    get_rule_by_id,
)
from src.infrastructure.alerts.ndma_client import ndma_client
from src.infrastructure.llm.gemini_client import gemini_client
from src.infrastructure.llm.prompt_templates import SYSTEM_SAFETY_POLICY
from src.infrastructure.persistence.repositories import AlertRepository
from src.observability.logger import get_logger

logger = get_logger(__name__)


class AlertService:
    """Orchestrates alerts evaluation, dedup, cooldown and NDMA syncing."""

    async def get_alerts_for_location(
        self, lat: float, lng: float, db: AsyncSession,
    ) -> list[Alert]:
        """Evaluate alert rules against location weather and return active alerts.
        Steps:
        1. Fetch weather context
        2. Evaluate deterministic rules
        3. Dedup & enforce cooldown checks
        4. Sync current NDMA alerts
        5. Returns active alerts (with LLM-friendly descriptions if active).
        """
        # 1. Fetch weather
        weather = await weather_service.get_weather_context(lat, lng)
        if not weather.data_available:
            # Degrade gracefully
            return []

        repo = AlertRepository(db)
        active_alerts = []

        # 2. Evaluate deterministic rules
        evaluations = evaluate_all_rules(weather)

        for ev in evaluations:
            if not ev.triggered:
                continue

            rule = get_rule_by_id(ev.rule_id)
            if not rule:
                continue

            # 3. Deduplication and Cooldown checks
            min_time = datetime.utcnow() - timedelta(minutes=rule.cooldown_minutes)
            recent_alerts = await repo.get_by_rule_and_location(
                rule_id=rule.id, lat=lat, lng=lng, min_time=min_time,
            )

            if recent_alerts:
                # Active cooldown: do not save or log new alert
                logger.info(
                    "alert_cooldown_active",
                    rule_id=rule.id,
                    latitude=lat,
                    longitude=lng,
                    cooldown_minutes=rule.cooldown_minutes,
                )
                active_alerts.append(recent_alerts[0])
                continue

            # Compile fresh alert
            title = rule.name
            description = format_alert_message(rule, weather)

            alert = Alert(
                rule_id=rule.id,
                severity=rule.severity,
                title=title,
                description=description,
                location_lat=lat,
                location_lng=lng,
                location_name=weather.current.location_name,
                source=AlertSource.WEATHER_RULES,
                source_data=ev.model_dump(),
                weather_data_age_seconds=weather.current.data_age_seconds,
                expires_at=datetime.utcnow() + timedelta(hours=6),
                is_active=True,
            )

            # Optional citizen-friendly rewrite using LLM (if configured)
            llm_ready = gemini_client._get_client() is not None
            if llm_ready:
                try:
                    rewrite_prompt = (
                        f"Rewrite the following technical weather warning alert into direct, citizen-friendly advice:\n"
                        f"Alert: {alert.title}\nDetail: {alert.description}\n"
                        f"Ensure the severity, measurements (e.g. rain in mm) and critical directions (e.g. stay indoors) are fully preserved. "
                        f"Make it sound urgent but calm. Limit to 2 short sentences."
                    )
                    friendly_text = await gemini_client.generate_text(
                        prompt=rewrite_prompt,
                        system_instruction=SYSTEM_SAFETY_POLICY,
                    )
                    alert.citizen_message = friendly_text.strip()
                except Exception as e:
                    logger.warning("alert_rewrite_failed_using_base_msg", error=str(e))
                    alert.citizen_message = alert.description

            # Save to repository
            saved = await repo.save(alert)
            active_alerts.append(saved)

        # 4. Integrate NDMA official alerts
        ndma_alerts = await ndma_client.fetch_official_alerts()
        for ndma in ndma_alerts:
            # Filter by matching coordinates roughly (approx ~30km for general warning zones)
            if ndma.location_lat is not None and ndma.location_lng is not None:
                if (
                    abs(ndma.location_lat - lat) < 0.3
                    and abs(ndma.location_lng - lng) < 0.3
                ):
                    active_alerts.append(ndma)
            # If geolocated alert doesn't list coords but has region/state matching, we add it
            # For simplicity, we add it if matches the state we got from reverse geocoding
            elif weather.current.location_name and ndma.location_name and (
                ndma.location_name.lower()
                in weather.current.location_name.lower()
            ):
                active_alerts.append(ndma)

        return active_alerts


# Singleton
alert_service = AlertService()
