"""
Risk classification logic.
Combines weather context + household profile to determine risk level.
This is deterministic — no LLM involvement.
"""

from src.domain.models.weather import WeatherContext, WeatherCondition
from src.domain.models.household import HouseholdProfile, HousingType
from src.domain.models.preparedness import RiskLevel, RiskSummary


def classify_risk(weather: WeatherContext, household: HouseholdProfile) -> RiskSummary:
    """
    Determine risk level based on weather and household context.
    Risk is escalated by vulnerability factors.
    """
    if not weather.data_available:
        return RiskSummary(
            level=RiskLevel.MODERATE,
            reasons=["Weather data unavailable — defaulting to moderate risk as a precaution"],
        )

    base_score = 0
    reasons = []
    current = weather.current
    forecast_24h_mm = current.rainfall.forecast_mm

    # --- Weather-based risk scoring ---
    # IMD classification thresholds
    if forecast_24h_mm >= 124.5:
        base_score += 50
        reasons.append(f"Extremely heavy rainfall forecast: {forecast_24h_mm:.1f}mm in 24h")
    elif forecast_24h_mm >= 64.5:
        base_score += 35
        reasons.append(f"Very heavy rainfall forecast: {forecast_24h_mm:.1f}mm in 24h")
    elif forecast_24h_mm >= 35.6:
        base_score += 25
        reasons.append(f"Heavy rainfall forecast: {forecast_24h_mm:.1f}mm in 24h")
    elif forecast_24h_mm >= 15:
        base_score += 15
        reasons.append(f"Moderate rainfall forecast: {forecast_24h_mm:.1f}mm in 24h")

    # Current ongoing rainfall
    if current.rainfall.current_mm >= 30:
        base_score += 15
        reasons.append(f"Heavy ongoing rainfall: {current.rainfall.current_mm:.1f}mm")

    # Wind
    if current.wind.speed_kmph >= 90:
        base_score += 30
        reasons.append(f"Storm-force winds: {current.wind.speed_kmph:.0f}km/h")
    elif current.wind.speed_kmph >= 60:
        base_score += 20
        reasons.append(f"High winds: {current.wind.speed_kmph:.0f}km/h")
    elif current.wind.speed_kmph >= 40:
        base_score += 10
        reasons.append(f"Strong winds: {current.wind.speed_kmph:.0f}km/h")

    # Thunderstorm
    if current.condition == WeatherCondition.THUNDERSTORM:
        base_score += 15
        reasons.append("Active thunderstorm conditions")

    # --- Household vulnerability multipliers ---
    vulnerability_multiplier = 1.0

    # Housing type vulnerability
    if household.housing_type in (HousingType.KUTCHA_HOUSE, HousingType.TEMPORARY_SHELTER):
        vulnerability_multiplier += 0.4
        reasons.append(f"High vulnerability: {household.housing_type.value} housing")
    elif household.housing_type == HousingType.GROUND_FLOOR:
        vulnerability_multiplier += 0.2
        reasons.append("Elevated flood risk: ground floor residence")
    elif household.housing_type == HousingType.SLUM:
        vulnerability_multiplier += 0.5
        reasons.append("High vulnerability: slum area — limited drainage infrastructure")

    # Near water body
    if household.near_water_body:
        vulnerability_multiplier += 0.3
        reasons.append("Near water body — elevated flood risk")

    # Vulnerable people
    if household.has_children:
        vulnerability_multiplier += 0.1
        reasons.append("Household has children — extra precaution needed")
    if household.has_elderly:
        vulnerability_multiplier += 0.15
        reasons.append("Household has elderly members — mobility considerations")
    if household.accessibility_needs:
        vulnerability_multiplier += 0.15
        reasons.append("Household has accessibility requirements")

    # Floor level (lower floors = higher flood risk)
    if household.floor_level is not None and household.floor_level == 0:
        vulnerability_multiplier += 0.15
        reasons.append("Ground floor — higher flood risk")

    # Apply multiplier
    final_score = base_score * vulnerability_multiplier

    # --- Classify risk level ---
    if final_score >= 50:
        level = RiskLevel.SEVERE
    elif final_score >= 30:
        level = RiskLevel.HIGH
    elif final_score >= 15:
        level = RiskLevel.MODERATE
    else:
        level = RiskLevel.LOW

    # Add positive note for low risk
    if level == RiskLevel.LOW and not reasons:
        reasons.append("No severe weather conditions detected for your area")

    return RiskSummary(level=level, reasons=reasons)
