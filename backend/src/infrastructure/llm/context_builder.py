"""Context builder for grounding LLM prompts.
Assembles user contexts, weather context, and safety knowledge into a single bundle.
"""


from src.domain.models.alert import Alert
from src.domain.models.household import HouseholdProfile
from src.domain.models.weather import WeatherContext


def build_preparedness_plan_prompt_vars(
    weather: WeatherContext,
    household: HouseholdProfile,
    risk_level: str,
    risk_reasons: list[str],
    active_alerts: list[Alert],
) -> dict:
    """Build variable dictionary for PREPAREDNESS_PLAN_PROMPT."""
    alert_text = "No verified severe weather alerts currently active for this location."
    if active_alerts:
        alert_text = "\n".join(
            f"- [{a.severity.value}] {a.title}: {a.description} (Source: {a.source.value})"
            for a in active_alerts
        )

    return {
        "location_name": household.location_name or "Unknown location",
        "latitude": round(household.location_lat, 4),
        "longitude": round(household.location_lng, 4),
        "household_size": household.household_size,
        "has_children": "Yes" if household.has_children else "No",
        "has_elderly": "Yes" if household.has_elderly else "No",
        "has_pets": "Yes" if household.has_pets else "No",
        "pet_details": household.pet_details or "None",
        "housing_type": household.housing_type.value,
        "has_vehicle": "Yes" if household.has_vehicle else "No",
        "vehicle_type": household.vehicle_type or "None",
        "accessibility_needs": household.accessibility_needs or "None",
        "weather_condition": weather.current.condition.value,
        "temperature": weather.current.temperature_celsius or "N/A",
        "rainfall_current_mm": weather.current.rainfall.current_mm,
        "rainfall_forecast_mm": weather.current.rainfall.forecast_mm,
        "wind_speed_kmph": weather.current.wind.speed_kmph,
        "is_monsoon_season": "Yes" if weather.is_monsoon_season else "No",
        "monsoon_phase": weather.monsoon_phase or "None",
        "risk_level": risk_level,
        "risk_reasons": ", ".join(risk_reasons),
        "active_alerts": alert_text,
    }


def build_assistant_qna_prompt_vars(
    weather: WeatherContext,
    household: HouseholdProfile | None,
    active_alerts: list[Alert],
    trusted_knowledge: str,
    user_question: str,
) -> dict:
    """Build variable dictionary for ASSISTANT_QNA_PROMPT."""
    current_weather = (
        f"Condition: {weather.current.condition.value}, "
        f"Temp: {weather.current.temperature_celsius}°C, "
        f"Recent rain: {weather.current.rainfall.current_mm}mm, "
        f"Forecast rain: {weather.current.rainfall.forecast_mm}mm, "
        f"Wind: {weather.current.wind.speed_kmph}km/h"
    )

    forecast_days = []
    for day in weather.forecast.days[:3]:  # Next 3 days forecast summary
        forecast_days.append(
            f"{day.date}: {day.condition.value}, max temp {day.temp_max_celsius}°C, rain {day.rainfall_mm}mm",
        )
    forecast_summary = " | ".join(forecast_days)

    alert_text = "No active severe weather alerts."
    if active_alerts:
        alert_text = "; ".join(
            f"[{a.severity.value}] {a.title}: {a.description}" for a in active_alerts
        )

    household_info = "Unknown"
    location_name = "Unknown Location"
    if household:
        location_name = (
            household.location_name
            or f"({household.location_lat}, {household.location_lng})"
        )
        household_info = (
            f"Type: {household.housing_type.value}, Size: {household.household_size}, "
            f"Children: {household.has_children}, Elderly: {household.has_elderly}, Pets: {household.has_pets}"
        )

    return {
        "current_weather": current_weather,
        "forecast": forecast_summary,
        "active_alerts": alert_text,
        "monsoon_phase": weather.monsoon_phase or "N/A",
        "trusted_knowledge": trusted_knowledge,
        "location_name": location_name,
        "household_info": household_info,
        "user_question": user_question,
    }
