"""
Integration tests for Alert Service.
Verifies rules evaluation, deduplication, and active alert cooldown logic.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta

from src.application.alert_service import alert_service
from src.domain.models.alert import Alert, AlertSeverity, AlertSource
from tests.unit.test_alert_rules import create_mock_weather


@pytest.mark.asyncio
async def test_alerts_triggered_successfully():
    # Mock weather containing Extreme Rain (150mm) -> should trigger EXTREME_RAIN_EMERGENCY
    weather_ctx = create_mock_weather(rainfall_forecast=150.0)
    db_mock = MagicMock()

    with patch("src.application.alert_service.weather_service.get_weather_context", new_callable=AsyncMock) as mock_weather, \
         patch("src.application.alert_service.AlertRepository.get_by_rule_and_location", new_callable=AsyncMock) as mock_get_recent, \
         patch("src.application.alert_service.AlertRepository.save", new_callable=AsyncMock) as mock_save, \
         patch("src.application.alert_service.ndma_client.fetch_official_alerts", new_callable=AsyncMock) as mock_ndma, \
         patch("src.application.alert_service.gemini_client._get_client") as mock_gemini_client:
         
        mock_weather.return_value = weather_ctx
        mock_get_recent.return_value = []  # No recent alerts in database
        mock_ndma.return_value = []
        mock_gemini_client.return_value = None  # Disable LLM rewrite

        # Setup save mock to return the input alert
        async def mock_save_side_effect(alert):
            alert.id = "alert-id-123"
            return alert
        mock_save.side_effect = mock_save_side_effect

        alerts = await alert_service.get_alerts_for_location(11.0168, 76.9558, db_mock)
        
        # Verify extreme rain alert is generated
        assert len(alerts) >= 1
        extreme_alert = next((a for a in alerts if a.rule_id == "EXTREME_RAIN_EMERGENCY"), None)
        assert extreme_alert is not None
        assert extreme_alert.severity == AlertSeverity.SEVERE
        assert extreme_alert.source == AlertSource.WEATHER_RULES
        
        mock_save.assert_called()


@pytest.mark.asyncio
async def test_alert_cooldown_dedup():
    # Weather context triggering High Winds (70kmph) -> wind warning
    weather_ctx = create_mock_weather(wind_speed=70.0)
    db_mock = MagicMock()

    # Pre-existing alert to trigger cooldown
    existing_alert = Alert(
        id="prev-alert-id",
        rule_id="HIGH_WIND_WARNING",
        severity=AlertSeverity.HIGH,
        title="High Wind Warning",
        description="High winds observed",
        location_lat=11.0168,
        location_lng=76.9558,
        source=AlertSource.WEATHER_RULES,
        triggered_at=datetime.utcnow() - timedelta(minutes=10),
        is_active=True,
    )

    with patch("src.application.alert_service.weather_service.get_weather_context", new_callable=AsyncMock) as mock_weather, \
         patch("src.application.alert_service.AlertRepository.get_by_rule_and_location", new_callable=AsyncMock) as mock_get_recent, \
         patch("src.application.alert_service.AlertRepository.save", new_callable=AsyncMock) as mock_save, \
         patch("src.application.alert_service.ndma_client.fetch_official_alerts", new_callable=AsyncMock) as mock_ndma, \
         patch("src.application.alert_service.gemini_client._get_client") as mock_gemini_client:
         
        mock_weather.return_value = weather_ctx
        mock_get_recent.return_value = [existing_alert]  # Pre-existing alert active
        mock_ndma.return_value = []
        mock_gemini_client.return_value = None

        alerts = await alert_service.get_alerts_for_location(11.0168, 76.9558, db_mock)
        
        # Verify that because of cooldown, NO NEW alert was saved
        mock_save.assert_not_called()
        # Returns the cached existing alert instead of generating duplicate
        assert len(alerts) >= 1
        assert alerts[0].id == "prev-alert-id"
