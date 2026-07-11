"""
Checklist Service.
Generates, persists, and updates context-aware emergency checklists.
Per spec: 'Do not reset user progress on page refresh. Persist checklist state.'
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.household import HouseholdProfile, HousingType
from src.domain.models.checklist import Checklist, ChecklistItem, ChecklistStatus, ChecklistCategory
from src.application.weather_service import weather_service
from src.infrastructure.persistence.repositories import ChecklistRepository
from src.observability.logger import get_logger

logger = get_logger(__name__)

# Base template checklist items mapped to conditions
BASE_CHECKLIST_TEMPLATES = [
    # Essentials
    {"title": "Charge all mobile phones and power banks to full capacity.", "category": ChecklistCategory.ESSENTIALS, "priority": 10},
    {"title": "Keep emergency flashlights/torches and spare batteries ready.", "category": ChecklistCategory.ESSENTIALS, "priority": 9},
    {"title": "Keep a physical copy of important emergency contact numbers.", "category": ChecklistCategory.COMMUNICATION, "priority": 8},
    
    # Food & Water
    {"title": "Store clean drinking water (at least 4 liters per person per day for 3 days).", "category": ChecklistCategory.FOOD_WATER, "priority": 9},
    {"title": "Stock up on dry, ready-to-eat foodstuffs (biscuits, parched rice).", "category": ChecklistCategory.FOOD_WATER, "priority": 8},
    
    # Medical
    {"title": "Check and replenish first-aid kit supplies and personal prescription medicines.", "category": ChecklistCategory.MEDICAL, "priority": 9},
    {"title": "Keep ORS (Oral Rehydration Salts) packets and chlorine tablets on hand.", "category": ChecklistCategory.MEDICAL, "priority": 7},
    
    # Documents
    {"title": "Put identification cards, insurance cards, and deeds in a zip-lock waterproof pouch.", "category": ChecklistCategory.DOCUMENTS, "priority": 8},
    
    # Property
    {"title": "Check gutters and clean local courtyard drain channels.", "category": ChecklistCategory.PROPERTY, "priority": 7},
]

WEATHER_CHECKLIST_TEMPLATES = [
    {
        "title": "Move dry food and critical electronics to higher floors/elevated shelves.",
        "category": ChecklistCategory.PROPERTY,
        "priority": 9,
        "min_forecast_rain_mm": 50.0,
    },
    {
        "title": "Unplug household appliances from wall sockets to prevent damage from power surges.",
        "category": ChecklistCategory.ESSENTIALS,
        "priority": 8,
        "min_forecast_rain_mm": 40.0,
        "conditions": ["thunderstorm"],
    },
    {
        "title": "Close and bolt all windows, ventilators, and external doors tightly.",
        "category": ChecklistCategory.PROPERTY,
        "priority": 8,
        "min_wind_speed_kmph": 45.0,
    },
]

VULNERABILITY_CHECKLIST_TEMPLATES = [
    {
        "title": "Stock up on baby food, diapers, and baby formula milk powder.",
        "category": ChecklistCategory.CHILDREN,
        "priority": 9,
        "flag": "has_children",
    },
    {
        "title": "Set up a checklist of prescriptions and ensure mobility aids are easily reachable.",
        "category": ChecklistCategory.ELDERLY,
        "priority": 9,
        "flag": "has_elderly",
    },
    {
        "title": "Store pet food, prepare pet carrier box, and keep a strong collar/leash handy.",
        "category": ChecklistCategory.PETS,
        "priority": 8,
        "flag": "has_pets",
    },
    {
        "title": "Identify and map the route to the nearest safe municipal concrete shelter.",
        "category": ChecklistCategory.EVACUATION,
        "priority": 10,
        "housing_types": [HousingType.KUTCHA_HOUSE, HousingType.SLUM, HousingType.TEMPORARY_SHELTER],
    },
    {
        "title": "Move two-wheeler or car to higher ground to avoid tailpipe water entry.",
        "category": ChecklistCategory.VEHICLE,
        "priority": 7,
        "flag": "has_vehicle",
    },
]


class ChecklistService:
    """Orchestrates checklist lifecycle, generation and persistence."""

    async def get_or_create_checklist(
        self, household: HouseholdProfile, db: AsyncSession
    ) -> Checklist:
        """
        Fetch existing checklist or compile one based on context.
        Ensures user progress is not reset on refresh.
        """
        household_id = UUID(household.id)
        repo = ChecklistRepository(db)
        
        # 1. Fetch current items
        items = await repo.get_by_household(household_id)
        
        # 2. If empty, generate initial list
        if not items:
            items = await self.generate_initial_items(household, db)
            items = await repo.save_all(items)

        # 3. Calculate summary metrics
        total = len(items)
        completed = sum(1 for i in items if i.status == ChecklistStatus.COMPLETED)
        pct = (completed / total * 100) if total > 0 else 0.0

        return Checklist(
            household_id=str(household_id),
            items=items,
            total_items=total,
            completed_items=completed,
            completion_percent=round(pct, 1),
        )

    async def generate_initial_items(
        self, household: HouseholdProfile, db: AsyncSession
    ) -> list[ChecklistItem]:
        """Compile a list of target items based on household & weather conditions."""
        items = []

        # Get weather details for threshold evaluations
        weather = await weather_service.get_weather_context(
            household.location_lat, household.location_lng
        )
        forecast_rain = weather.current.rainfall.forecast_mm
        wind_speed = weather.current.wind.speed_kmph
        condition = weather.current.condition.value

        # 1. Add base templates
        for t in BASE_CHECKLIST_TEMPLATES:
            items.append(
                ChecklistItem(
                    title=t["title"],
                    category=t["category"],
                    status=ChecklistStatus.PENDING,
                    priority=t["priority"],
                    household_id=household.id,
                )
            )

        # 2. Add weather-dependent templates
        for t in WEATHER_CHECKLIST_TEMPLATES:
            triggered = False
            reasons = []
            
            if "min_forecast_rain_mm" in t and forecast_rain >= t["min_forecast_rain_mm"]:
                triggered = True
                reasons.append(f"forecast rainfall is {forecast_rain:.1f}mm")
            
            if "min_wind_speed_kmph" in t and wind_speed >= t["min_wind_speed_kmph"]:
                triggered = True
                reasons.append(f"forecast wind speed is {wind_speed:.0f}km/h")
                
            if "conditions" in t and condition in t["conditions"]:
                triggered = True
                reasons.append(f"forecast weather is {condition}")

            if triggered:
                items.append(
                    ChecklistItem(
                        title=t["title"],
                        category=t["category"],
                        status=ChecklistStatus.PENDING,
                        priority=t["priority"],
                        weather_context=f"Triggered because {', '.join(reasons)}",
                        household_id=household.id,
                    )
                )

        # 3. Add household context-dependent templates
        for t in VULNERABILITY_CHECKLIST_TEMPLATES:
            match = False
            
            if "flag" in t and getattr(household, t["flag"], False):
                match = True
            
            if "housing_types" in t and household.housing_type in t["housing_types"]:
                match = True

            if match:
                items.append(
                    ChecklistItem(
                        title=t["title"],
                        category=t["category"],
                        status=ChecklistStatus.PENDING,
                        priority=t["priority"],
                        household_id=household.id,
                    )
                )

        return items

    async def update_item_status(
        self, household_id: str, item_id: str, status: ChecklistStatus, db: AsyncSession
    ) -> ChecklistItem:
        """Update single checklist item status."""
        repo = ChecklistRepository(db)
        items = await repo.get_by_household(UUID(household_id))
        
        target = next((i for i in items if i.id == item_id), None)
        if not target:
            raise ValueError("Checklist item not found")

        target.status = status
        saved = await repo.save_all([target])
        logger.info("checklist_item_status_updated", item_id=item_id, status=status.value)
        return saved[0]


# Singleton
checklist_service = ChecklistService()
