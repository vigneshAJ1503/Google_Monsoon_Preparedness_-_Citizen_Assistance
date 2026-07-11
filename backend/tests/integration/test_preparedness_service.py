"""
Integration tests for Preparedness Service.
Verifies LLM generation and fallback plan routing.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.application.preparedness_service import preparedness_service
from src.domain.models.household import HouseholdProfile, HousingType
from src.domain.models.preparedness import PreparednessePlan, RiskLevel
from tests.unit.test_alert_rules import create_mock_weather


@pytest.mark.asyncio
async def test_generate_plan_deterministic_fallback():
    # Mock weather context (Very Heavy Rain -> 70mm forecast)
    weather_ctx = create_mock_weather(rainfall_forecast=70.0)
    
    # Mock database session
    db_mock = MagicMock()
    
    # Setup household
    hh = HouseholdProfile(
        id="12345678-1234-5678-1234-567812345678",
        location_lat=11.0168,
        location_lng=76.9558,
        household_size=3,
        has_children=True,
        has_elderly=False,
        has_pets=True,
        housing_type=HousingType.APARTMENT,
        has_vehicle=True
    )

    # Patch weather_service & alert_repo & gemini_client
    with patch("src.application.preparedness_service.weather_service.get_weather_context", new_callable=AsyncMock) as mock_weather, \
         patch("src.application.preparedness_service.AlertRepository.get_active_alerts", new_callable=AsyncMock) as mock_alerts, \
         patch("src.application.preparedness_service.PreparednessPlanRepository.save", new_callable=AsyncMock) as mock_save, \
         patch("src.application.preparedness_service.PreparednessPlanRepository.get_by_household", new_callable=AsyncMock) as mock_get_cache, \
         patch("src.application.preparedness_service.gemini_client._get_client") as mock_gemini_client:
         
        mock_weather.return_value = weather_ctx
        mock_alerts.return_value = []
        mock_get_cache.return_value = None
        
        # Disable Gemini to force fallback
        mock_gemini_client.return_value = None

        plan = await preparedness_service.generate_plan(hh, db_mock, bypass_cache=True)
        
        assert isinstance(plan, PreparednessePlan)
        assert plan.risk_summary.level == RiskLevel.HIGH
        
        # Verify that pet and children checklist items exist in fallback items
        actions = [a.action for a in plan.household_specific_actions]
        assert any("children" in a.lower() for a in actions)
        assert any("pets" in a.lower() for a in actions)
        
        # Check fallback tag
        assert "static safety rules" in plan.limitations[0]
        mock_save.assert_called_once()
