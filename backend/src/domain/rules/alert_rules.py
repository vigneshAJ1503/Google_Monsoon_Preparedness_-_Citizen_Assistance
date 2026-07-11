"""Deterministic alert rules engine.
Per spec: 'The LLM must NOT decide whether an emergency alert should be triggered.'.

All alert decisions are made by evaluating weather data against fixed thresholds.
The LLM may only rewrite already-validated alerts into citizen-friendly language.
"""


from src.domain.models.alert import AlertEvaluation, AlertRule, AlertSeverity
from src.domain.models.weather import WeatherContext
from src.observability.logger import get_logger

logger = get_logger(__name__)

# --- IMD rainfall classification (India Meteorological Department standard) ---
# Light:           0.1 - 7.5 mm/day
# Moderate:        7.6 - 35.5 mm/day
# Heavy:           35.6 - 64.4 mm/day
# Very Heavy:      64.5 - 124.4 mm/day
# Extremely Heavy: >= 124.5 mm/day

ALERT_RULES: list[AlertRule] = [
    AlertRule(
        id="HEAVY_RAIN_PREPAREDNESS",
        name="Heavy Rain Preparedness",
        description="Heavy rainfall expected — prepare supplies and secure property",
        conditions={
            "forecast_rainfall_mm_gte": 50,
            "forecast_window_hours_lte": 24,
        },
        severity=AlertSeverity.HIGH,
        cooldown_minutes=180,
        message_template=(
            "Heavy rainfall of {forecast_mm}mm is forecast for your area in the next 24 hours. "
            "Prepare emergency supplies and secure outdoor items."
        ),
        requires_fields=["rainfall.forecast_mm"],
    ),
    AlertRule(
        id="EXTREME_RAIN_EMERGENCY",
        name="Extreme Rainfall Emergency",
        description="Extremely heavy rainfall — take immediate shelter",
        conditions={
            "forecast_rainfall_mm_gte": 124.5,
            "forecast_window_hours_lte": 24,
        },
        severity=AlertSeverity.SEVERE,
        cooldown_minutes=60,
        message_template=(
            "SEVERE: Extremely heavy rainfall of {forecast_mm}mm expected. "
            "Stay indoors. Avoid travel. Move to higher ground if in a flood-prone area."
        ),
        requires_fields=["rainfall.forecast_mm"],
    ),
    AlertRule(
        id="VERY_HEAVY_RAIN_WARNING",
        name="Very Heavy Rain Warning",
        description="Very heavy rainfall expected in the next 24 hours",
        conditions={
            "forecast_rainfall_mm_gte": 64.5,
            "forecast_window_hours_lte": 24,
        },
        severity=AlertSeverity.HIGH,
        cooldown_minutes=120,
        message_template=(
            "Very heavy rainfall of {forecast_mm}mm is expected. "
            "Avoid waterlogged areas and low-lying zones. Keep emergency contacts ready."
        ),
        requires_fields=["rainfall.forecast_mm"],
    ),
    AlertRule(
        id="HIGH_WIND_WARNING",
        name="High Wind Warning",
        description="Dangerous wind speeds detected",
        conditions={
            "wind_speed_kmph_gte": 60,
        },
        severity=AlertSeverity.HIGH,
        cooldown_minutes=180,
        message_template=(
            "High wind speeds of {wind_speed}km/h detected. "
            "Secure loose objects. Stay away from trees and signboards."
        ),
        requires_fields=["wind.speed_kmph"],
    ),
    AlertRule(
        id="STORM_WIND_EMERGENCY",
        name="Storm Wind Emergency",
        description="Storm-force winds — take shelter immediately",
        conditions={
            "wind_speed_kmph_gte": 90,
        },
        severity=AlertSeverity.SEVERE,
        cooldown_minutes=60,
        message_template=(
            "SEVERE: Storm-force winds of {wind_speed}km/h. "
            "Take shelter immediately. Do not go outside."
        ),
        requires_fields=["wind.speed_kmph"],
    ),
    AlertRule(
        id="MODERATE_RAIN_ADVISORY",
        name="Moderate Rain Advisory",
        description="Moderate rainfall expected — carry rain gear",
        conditions={
            "forecast_rainfall_mm_gte": 15,
            "forecast_window_hours_lte": 24,
        },
        severity=AlertSeverity.MODERATE,
        cooldown_minutes=360,
        message_template=(
            "Moderate rainfall of {forecast_mm}mm expected. "
            "Carry rain gear and avoid unnecessary travel during heavy spells."
        ),
        requires_fields=["rainfall.forecast_mm"],
    ),
    AlertRule(
        id="THUNDERSTORM_WARNING",
        name="Thunderstorm Warning",
        description="Thunderstorm conditions detected",
        conditions={
            "condition_is": "thunderstorm",
        },
        severity=AlertSeverity.HIGH,
        cooldown_minutes=120,
        message_template=(
            "Thunderstorm conditions in your area. "
            "Stay indoors. Unplug electrical appliances. Avoid open areas and tall structures."
        ),
        requires_fields=["condition"],
    ),
    AlertRule(
        id="SUSTAINED_RAIN_FLOOD_RISK",
        name="Sustained Rainfall Flood Risk",
        description="Prolonged rainfall increases flood risk",
        conditions={
            "current_rainfall_mm_gte": 30,
            "forecast_rainfall_mm_gte": 50,
        },
        severity=AlertSeverity.HIGH,
        cooldown_minutes=240,
        message_template=(
            "Ongoing rainfall ({current_mm}mm) with {forecast_mm}mm more expected. "
            "Flood risk is elevated. Monitor water levels and prepare to move to higher ground."
        ),
        requires_fields=["rainfall.current_mm", "rainfall.forecast_mm"],
    ),
]


def evaluate_rule(rule: AlertRule, weather: WeatherContext) -> AlertEvaluation:
    """Evaluate a single alert rule against weather data.
    This is PURE DETERMINISTIC logic — no AI, no guessing.
    """
    current = weather.current
    conditions = rule.conditions

    # Check data freshness first — stale data should not trigger alerts
    if current.is_stale:
        return AlertEvaluation(
            rule_id=rule.id,
            triggered=False,
            reason="Weather data is stale — cannot reliably evaluate alert",
        )

    triggered = True
    source_value = None
    threshold_value = None

    for condition_key, threshold in conditions.items():
        if condition_key == "forecast_rainfall_mm_gte":
            source_value = current.rainfall.forecast_mm
            threshold_value = threshold
            if source_value < threshold:
                triggered = False
                break

        elif condition_key == "current_rainfall_mm_gte":
            source_value = current.rainfall.current_mm
            threshold_value = threshold
            if source_value < threshold:
                triggered = False
                break

        elif condition_key == "wind_speed_kmph_gte":
            source_value = current.wind.speed_kmph
            threshold_value = threshold
            if source_value < threshold:
                triggered = False
                break

        elif condition_key == "condition_is":
            source_value = current.condition.value
            threshold_value = threshold
            if current.condition.value != threshold:
                triggered = False
                break

        elif condition_key == "forecast_window_hours_lte":
            # This is a context constraint, not a data check
            continue

        else:
            logger.warning(
                "unknown_alert_condition", rule_id=rule.id, condition=condition_key,
            )
            triggered = False
            break

    reason = None
    if triggered:
        reason = (
            f"Threshold met: {source_value} >= {threshold_value}"
            if threshold_value
            else "Condition matched"
        )

    return AlertEvaluation(
        rule_id=rule.id,
        triggered=triggered,
        severity=rule.severity if triggered else None,
        reason=reason,
        source_value=(
            float(source_value) if isinstance(source_value, (int, float)) else None
        ),
        threshold_value=(
            float(threshold_value)
            if isinstance(threshold_value, (int, float))
            else None
        ),
    )


def evaluate_all_rules(weather: WeatherContext) -> list[AlertEvaluation]:
    """Evaluate all alert rules against current weather.
    Returns list of evaluations (both triggered and not triggered).
    """
    if not weather.data_available:
        logger.info("alert_evaluation_skipped", reason="Weather data unavailable")
        return []

    evaluations = []
    for rule in ALERT_RULES:
        evaluation = evaluate_rule(rule, weather)
        evaluations.append(evaluation)

        if evaluation.triggered:
            logger.info(
                "alert_rule_evaluated",
                rule_id=rule.id,
                triggered=True,
                severity=rule.severity.value,
                source_value=evaluation.source_value,
                threshold_value=evaluation.threshold_value,
                weather_data_age_seconds=weather.current.data_age_seconds,
            )

    return evaluations


def get_rule_by_id(rule_id: str) -> AlertRule | None:
    """Get a rule definition by ID."""
    for rule in ALERT_RULES:
        if rule.id == rule_id:
            return rule
    return None


def format_alert_message(rule: AlertRule, weather: WeatherContext) -> str:
    """Format the alert message template with actual data."""
    return rule.message_template.format(
        forecast_mm=round(weather.current.rainfall.forecast_mm, 1),
        current_mm=round(weather.current.rainfall.current_mm, 1),
        wind_speed=round(weather.current.wind.speed_kmph, 1),
    )
