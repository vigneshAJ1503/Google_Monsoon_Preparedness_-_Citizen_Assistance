"""
Unit tests for Indian monsoon season detection.
"""

from datetime import date
from src.domain.rules.monsoon_season import get_monsoon_phase, is_monsoon_season, MonsoonPhase


def test_monsoon_southwest_pattern():
    # North India (e.g. Delhi) Southwest monsoon timeline
    lat_north = 28.6139

    # March: Pre-monsoon
    assert get_monsoon_phase(date(2026, 3, 15), latitude=lat_north) == MonsoonPhase.PRE_MONSOON
    assert is_monsoon_season(date(2026, 3, 15), latitude=lat_north) is False

    # July: Active Southwest Peak
    assert get_monsoon_phase(date(2026, 7, 15), latitude=lat_north) == MonsoonPhase.PEAK
    assert is_monsoon_season(date(2026, 7, 15), latitude=lat_north) is True

    # October: Retreating
    assert get_monsoon_phase(date(2026, 10, 15), latitude=lat_north) == MonsoonPhase.RETREATING
    assert is_monsoon_season(date(2026, 10, 15), latitude=lat_north) is False


def test_northeast_monsoon_pattern():
    # Tamil Nadu (e.g. Chennai) northeast monsoon timeline
    lat_chennai = 13.0827
    state_tn = "Tamil Nadu"

    # July: Active Southwest Monsoon also brings rain
    assert get_monsoon_phase(date(2026, 7, 15), state=state_tn) == MonsoonPhase.ACTIVE
    assert is_monsoon_season(date(2026, 7, 15), state=state_tn) is True

    # November: Peak Northeast Monsoon (Tamil Nadu's main rain)
    assert get_monsoon_phase(date(2026, 11, 15), state=state_tn) == MonsoonPhase.NORTHEAST_MONSOON
    assert is_monsoon_season(date(2026, 11, 15), state=state_tn) is True

    # February: Dry season
    assert get_monsoon_phase(date(2026, 2, 15), state=state_tn) == MonsoonPhase.DRY_SEASON
    assert is_monsoon_season(date(2026, 2, 15), state=state_tn) is False
