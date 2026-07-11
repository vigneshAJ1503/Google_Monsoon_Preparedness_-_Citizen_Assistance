"""
Unit tests for deterministic alert rules engine.
Tests boundaries: below, exact, and above thresholds.
"""

from datetime import datetime, timezone
from src.domain.rules.alert_rules import evaluate_all_rules, get_rule_by_id
from src.domain.models.weather import WeatherContext, WeatherObservation, WeatherForecast, WeatherCondition
from src.domain.models.alert import AlertSeverity


def create_mock_weather(rainfall_current: float = 0.0, rainfall_forecast: float = 0.0, wind_speed: float = 0.0, condition: str = "clear", is_stale: bool = False) -> WeatherContext:
    obs = WeatherObservation(
        latitude=11.0168,
        longitude=76.9558,
        observed_at=datetime.now(timezone.utc),
        condition=WeatherCondition(condition),
        rainfall={
            "current_mm": rainfall_current,
            "forecast_mm": rainfall_forecast,
            "hourly_forecast": []
        },
        wind={
            "speed_kmph": wind_speed,
            "gust_kmph": wind_speed * 1.2
        },
        source="Open-Meteo",
        data_age_seconds=120,
        is_stale=is_stale
    )
    
    forecast = WeatherForecast(
        latitude=11.0168,
        longitude=76.9558,
        generated_at=datetime.now(timezone.utc),
        days=[],
        source="Open-Meteo",
        data_age_seconds=120
    )
    
    return WeatherContext(
        current=obs,
        forecast=forecast,
        is_monsoon_season=True
    )


def test_heavy_rain_preparedness_boundaries():
    # Boundary: 49.9 mm (should not trigger)
    w_under = create_mock_weather(rainfall_forecast=49.9)
    evals = evaluate_all_rules(w_under)
    hr_eval = next(e for e in evals if e.rule_id == "HEAVY_RAIN_PREPAREDNESS")
    assert hr_eval.triggered is False

    # Boundary: 50.0 mm (should trigger)
    w_exact = create_mock_weather(rainfall_forecast=50.0)
    evals = evaluate_all_rules(w_exact)
    hr_eval = next(e for e in evals if e.rule_id == "HEAVY_RAIN_PREPAREDNESS")
    assert hr_eval.triggered is True
    assert hr_eval.severity == AlertSeverity.HIGH

    # Boundary: 50.1 mm (should trigger)
    w_above = create_mock_weather(rainfall_forecast=50.1)
    evals = evaluate_all_rules(w_above)
    hr_eval = next(e for e in evals if e.rule_id == "HEAVY_RAIN_PREPAREDNESS")
    assert hr_eval.triggered is True


def test_extreme_rain_emergency_boundaries():
    # Boundary: 124.4 mm (below threshold)
    w_under = create_mock_weather(rainfall_forecast=124.4)
    evals = evaluate_all_rules(w_under)
    ext_eval = next(e for e in evals if e.rule_id == "EXTREME_RAIN_EMERGENCY")
    assert ext_eval.triggered is False

    # Boundary: 124.5 mm (exact threshold)
    w_exact = create_mock_weather(rainfall_forecast=124.5)
    evals = evaluate_all_rules(w_exact)
    ext_eval = next(e for e in evals if e.rule_id == "EXTREME_RAIN_EMERGENCY")
    assert ext_eval.triggered is True
    assert ext_eval.severity == AlertSeverity.SEVERE


def test_stale_data_does_not_alert():
    # Stale data should NEVER trigger alerts
    w_stale = create_mock_weather(rainfall_forecast=150.0, is_stale=True)
    evals = evaluate_all_rules(w_stale)
    for e in evals:
        assert e.triggered is False
