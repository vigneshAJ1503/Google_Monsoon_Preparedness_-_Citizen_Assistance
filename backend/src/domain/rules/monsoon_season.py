"""
Monsoon season detection for India.
Determines the current phase of the Indian monsoon based on date and region.

Indian Monsoon Timeline:
- Pre-monsoon:    March – May (heat buildup, thunderstorms)
- Southwest Monsoon onset: Kerala ~June 1, progresses northward
- Active Monsoon: June – September (peak rainfall)
- Retreating:     October – November (northeast monsoon for Tamil Nadu)
- Post-monsoon:   December – February (dry, winter)

Tamil Nadu exception: Gets most rain during northeast monsoon (Oct-Dec).
"""

from datetime import date, datetime
from typing import Optional
from enum import Enum


class MonsoonPhase(str, Enum):
    PRE_MONSOON = "pre_monsoon"
    ONSET = "onset"
    ACTIVE = "active"
    PEAK = "peak"
    RETREATING = "retreating"
    NORTHEAST_MONSOON = "northeast_monsoon"  # Tamil Nadu special
    POST_MONSOON = "post_monsoon"
    DRY_SEASON = "dry_season"


# Indian state groupings by monsoon pattern
SOUTH_INDIA_STATES = {"Kerala", "Tamil Nadu", "Karnataka", "Andhra Pradesh", "Telangana", "Puducherry", "Goa"}
NORTHEAST_MONSOON_STATES = {"Tamil Nadu", "Puducherry", "Andhra Pradesh (coastal)"}
NORTH_INDIA_STATES = {"Delhi", "Uttar Pradesh", "Bihar", "Rajasthan", "Madhya Pradesh", "Punjab", "Haryana"}


def get_monsoon_phase(
    check_date: Optional[date] = None,
    state: Optional[str] = None,
    latitude: Optional[float] = None,
) -> MonsoonPhase:
    """
    Determine the current monsoon phase for a given date and region.

    Uses latitude as a rough proxy when state is not provided.
    South India (lat < 15): earlier onset, northeast monsoon relevance.
    North India (lat > 23): later onset, drier retreat.
    """
    if check_date is None:
        check_date = date.today()

    month = check_date.month
    day = check_date.day

    # Determine region
    is_south = False
    is_tamil_nadu_region = False

    if state:
        is_south = state in SOUTH_INDIA_STATES
        is_tamil_nadu_region = state in NORTHEAST_MONSOON_STATES
    elif latitude is not None:
        is_south = latitude < 15.0
        is_tamil_nadu_region = 8.0 <= latitude <= 13.5  # Tamil Nadu latitude range

    # --- Tamil Nadu / Southeast coast: Northeast monsoon (Oct-Dec) ---
    if is_tamil_nadu_region:
        if month in (10, 11, 12):
            return MonsoonPhase.NORTHEAST_MONSOON
        elif month in (6, 7, 8, 9):
            return MonsoonPhase.ACTIVE  # SW monsoon still brings some rain
        elif month in (3, 4, 5):
            return MonsoonPhase.PRE_MONSOON
        else:
            return MonsoonPhase.DRY_SEASON

    # --- Rest of India: Southwest monsoon pattern ---
    if month in (3, 4, 5):
        return MonsoonPhase.PRE_MONSOON

    elif month == 6:
        if is_south and day <= 10:
            return MonsoonPhase.ONSET
        elif not is_south and day <= 20:
            return MonsoonPhase.ONSET
        return MonsoonPhase.ACTIVE

    elif month in (7, 8):
        return MonsoonPhase.PEAK

    elif month == 9:
        if day <= 15:
            return MonsoonPhase.ACTIVE
        return MonsoonPhase.RETREATING

    elif month in (10, 11):
        return MonsoonPhase.RETREATING

    else:
        return MonsoonPhase.DRY_SEASON


def is_monsoon_season(
    check_date: Optional[date] = None,
    state: Optional[str] = None,
    latitude: Optional[float] = None,
) -> bool:
    """Check if the current date falls within any active monsoon phase."""
    phase = get_monsoon_phase(check_date, state, latitude)
    return phase in (
        MonsoonPhase.ONSET,
        MonsoonPhase.ACTIVE,
        MonsoonPhase.PEAK,
        MonsoonPhase.NORTHEAST_MONSOON,
    )


def get_monsoon_context(
    check_date: Optional[date] = None,
    state: Optional[str] = None,
    latitude: Optional[float] = None,
) -> dict:
    """Get human-readable monsoon context for LLM grounding."""
    phase = get_monsoon_phase(check_date, state, latitude)
    is_active = is_monsoon_season(check_date, state, latitude)

    phase_descriptions = {
        MonsoonPhase.PRE_MONSOON: "Pre-monsoon season. Hot weather with occasional thunderstorms. Monsoon expected to arrive soon.",
        MonsoonPhase.ONSET: "Monsoon onset period. Initial monsoon rains arriving. Expect increasing rainfall.",
        MonsoonPhase.ACTIVE: "Active monsoon season. Regular rainfall expected. Stay prepared.",
        MonsoonPhase.PEAK: "Peak monsoon period. Heavy and sustained rainfall likely. Highest flood risk.",
        MonsoonPhase.RETREATING: "Monsoon retreating. Rainfall decreasing but sporadic heavy spells possible.",
        MonsoonPhase.NORTHEAST_MONSOON: "Northeast monsoon active (Tamil Nadu/southeast coast). Heavy rainfall expected.",
        MonsoonPhase.POST_MONSOON: "Post-monsoon period. Rainfall subsiding.",
        MonsoonPhase.DRY_SEASON: "Dry season. Minimal rainfall expected.",
    }

    return {
        "phase": phase.value,
        "is_monsoon_active": is_active,
        "description": phase_descriptions.get(phase, ""),
        "date": check_date.isoformat() if check_date else date.today().isoformat(),
    }
