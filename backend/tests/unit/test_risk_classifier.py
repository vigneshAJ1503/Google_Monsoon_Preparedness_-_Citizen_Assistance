"""
Unit tests for deterministic risk classifier.
Tests weather scores combined with household vulnerability factors.
"""

from src.domain.rules.risk_classifier import classify_risk
from src.domain.models.household import HouseholdProfile, HousingType
from src.domain.models.preparedness import RiskLevel
from tests.unit.test_alert_rules import create_mock_weather


def create_base_household(housing: HousingType = HousingType.APARTMENT, near_water: bool = False) -> HouseholdProfile:
    return HouseholdProfile(
        location_lat=11.0168,
        location_lng=76.9558,
        household_size=2,
        has_children=False,
        has_elderly=False,
        has_pets=False,
        housing_type=housing,
        has_vehicle=False,
        near_water_body=near_water
    )


def test_classify_risk_levels():
    # Low weather risk, safe apartment -> LOW
    weather = create_mock_weather(rainfall_forecast=5.0)
    hh = create_base_household()
    summary = classify_risk(weather, hh)
    assert summary.level == RiskLevel.LOW

    # Moderate weather risk, safe apartment -> MODERATE
    weather = create_mock_weather(rainfall_forecast=25.0)
    summary = classify_risk(weather, hh)
    assert summary.level == RiskLevel.MODERATE

    # High weather risk (heavy rain) -> HIGH
    weather = create_mock_weather(rainfall_forecast=75.0)
    summary = classify_risk(weather, hh)
    assert summary.level == RiskLevel.HIGH

    # Severe weather risk (extreme rain) -> SEVERE
    weather = create_mock_weather(rainfall_forecast=130.0)
    summary = classify_risk(weather, hh)
    assert summary.level == RiskLevel.SEVERE


def test_vulnerability_escalation():
    # Moderate rain forecast (15 points score)
    weather = create_mock_weather(rainfall_forecast=20.0)
    
    # Standard apartment (multiplier 1.0) -> MODERATE (final score 15)
    hh_standard = create_base_household()
    summary_std = classify_risk(weather, hh_standard)
    assert summary_std.level == RiskLevel.MODERATE

    # Kutcha house + near water body (multiplier 1.0 + 0.4 + 0.3 = 1.7) -> final score 25.5 -> MODERATE
    # (Not enough to escalate to HIGH; needs heavier rain or more vulnerability factors)
    hh_vulnerable = create_base_household(housing=HousingType.KUTCHA_HOUSE, near_water=True)
    summary_vuln = classify_risk(weather, hh_vulnerable)
    assert summary_vuln.level == RiskLevel.MODERATE
    
    # Heavy rain (35.6mm = 25 points) + vulnerable house -> 25 * 1.7 = 42.5 -> HIGH
    weather_heavy = create_mock_weather(rainfall_forecast=40.0)
    summary_heavy_vuln = classify_risk(weather_heavy, hh_vulnerable)
    assert summary_heavy_vuln.level == RiskLevel.HIGH
