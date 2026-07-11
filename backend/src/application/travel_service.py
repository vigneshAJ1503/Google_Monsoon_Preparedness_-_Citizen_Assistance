"""
Travel Advisory Service.
Combines weather and alerts context from origin to destination to assess risks.
Never invents road closures; explicitly declares data limitations.
"""

from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.travel import TravelAdvisory, TravelRiskLevel
from src.application.weather_service import weather_service
from src.application.alert_service import alert_service
from src.infrastructure.geocoding.nominatim_client import nominatim_client
from src.infrastructure.llm.groq_client import groq_client
from src.infrastructure.llm.prompt_templates import SYSTEM_SAFETY_POLICY, TRAVEL_ADVISORY_PROMPT
from src.infrastructure.persistence.repositories import AlertRepository
from src.observability.logger import get_logger

logger = get_logger(__name__)


class TravelService:
    """Orchestrates travel safety assessments between coordinates."""

    async def get_travel_advisory(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        db: AsyncSession,
    ) -> TravelAdvisory:
        """Assess travel risks and construct a safe advisory."""
        # 1. Resolve location details
        origin_loc = await nominatim_client.reverse_geocode(origin_lat, origin_lng)
        dest_loc = await nominatim_client.reverse_geocode(dest_lat, dest_lng)
        
        origin_name = origin_loc.name if origin_loc else f"({origin_lat}, {origin_lng})"
        dest_name = dest_loc.name if dest_loc else f"({dest_lat}, {dest_lng})"

        # 2. Fetch Weather
        origin_weather = await weather_service.get_weather_context(origin_lat, origin_lng)
        dest_weather = await weather_service.get_weather_context(dest_lat, dest_lng)

        # 3. Fetch Alerts
        origin_alerts = await alert_service.get_alerts_for_location(origin_lat, origin_lng, db)
        dest_alerts = await alert_service.get_alerts_for_location(dest_lat, dest_lng, db)
        
        combined_alerts = list({a.id: a for a in (origin_alerts + dest_alerts) if a.id}.values())

        # 4. Deterministic Risk Classification
        risk_level = TravelRiskLevel.LOW
        reasons = []
        
        dest_rain = dest_weather.current.rainfall.forecast_mm
        dest_wind = dest_weather.current.wind.speed_kmph
        
        # Rainfall thresholds for travel
        if dest_rain >= 100.0 or any(a.severity.value == "SEVERE" for a in combined_alerts):
            risk_level = TravelRiskLevel.AVOID
            reasons.append("Extreme rainfall forecast or active severe alert along the route/destination.")
        elif dest_rain >= 50.0 or any(a.severity.value == "HIGH" for a in combined_alerts):
            risk_level = TravelRiskLevel.HIGH
            reasons.append("Heavy rainfall forecast or active warnings. Waterlogging of roads is highly likely.")
        elif dest_rain >= 25.0:
            risk_level = TravelRiskLevel.MODERATE
            reasons.append("Moderate rainfall expected. Watch out for slow traffic and minor water pooling.")

        if dest_wind >= 60.0:
            risk_level = max(risk_level, TravelRiskLevel.HIGH)
            reasons.append("High wind warnings. Risk of fallen tree branches or structural blockages.")

        # Default reason
        if risk_level == TravelRiskLevel.LOW:
            reasons.append("No active alerts or severe weather conditions reported along the route.")

        # 5. Groq-based personalized travel guidance
        llm_ready = groq_client._get_client() is not None
        recommendations = []
        limitations = [
            "Road-level flooding data is unavailable, so I cannot verify that this route is clear.",
            "Always avoid crossing waterlogged subways or underpasses."
        ]

        if llm_ready:
            try:
                alert_text = "; ".join(f"[{a.severity.value}] {a.title}" for a in combined_alerts) or "None"
                origin_w = f"{origin_weather.current.condition.value}, rain {origin_weather.current.rainfall.current_mm}mm"
                dest_w = f"{dest_weather.current.condition.value}, forecast rain {dest_weather.current.rainfall.forecast_mm}mm"

                prompt = TRAVEL_ADVISORY_PROMPT.format(
                    origin_name=origin_name,
                    destination_name=dest_name,
                    origin_weather=origin_w,
                    destination_weather=dest_w,
                    active_alerts=alert_text,
                )

                # Fetch structured recommendation points from LLM
                response_text = await groq_client.generate_text(
                    prompt=prompt + "\nProvide exactly 3 concise, safety-critical advice bullet points. Do not mention road status.",
                    system_instruction=SYSTEM_SAFETY_POLICY,
                )
                recommendations = [line.strip("- *").strip() for line in response_text.strip().split("\n") if line.strip()]
            except Exception as e:
                logger.error("travel_advisory_llm_failed", error=str(e))

        # Fallback recommendations if LLM fails/disabled
        if not recommendations:
            recommendations = [
                "Check local media or traffic updates before starting.",
                "Ensure vehicle tires and wipers are fully functional.",
                "Avoid low-lying routes and underpasses prone to flooding."
            ]

        return TravelAdvisory(
            origin_name=origin_name,
            destination_name=dest_name,
            risk_level=risk_level,
            risk_reasons=reasons,
            recommendations=recommendations,
            origin_weather_summary=(
                f"Condition: {origin_weather.current.condition.value}, "
                f"Rain: {origin_weather.current.rainfall.current_mm:.1f}mm"
            ),
            destination_weather_summary=(
                f"Condition: {dest_weather.current.condition.value}, "
                f"Forecast: {dest_weather.current.rainfall.forecast_mm:.1f}mm"
            ),
            active_alerts=[a.title for a in combined_alerts],
            limitations=limitations,
            data_sources=["Open-Meteo API", "NDMA Alerts", "Groq Llama 3.1 (Free)"],
            generated_at=datetime.utcnow().isoformat(),
        )


# Singleton
travel_service = TravelService()
