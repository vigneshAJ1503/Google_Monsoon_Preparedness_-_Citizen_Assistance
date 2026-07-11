"""Data access layer (Repositories) using SQLAlchemy async sessions."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models.alert import Alert, AlertSeverity, AlertSource
from src.domain.models.checklist import (
    ChecklistCategory,
    ChecklistItem,
    ChecklistStatus,
)
from src.domain.models.household import HouseholdProfile, HousingType
from src.infrastructure.persistence.models import (
    AlertModel,
    ChecklistItemModel,
    HouseholdModel,
    PreparednessPlanModel,
)


class HouseholdRepository:
    """Repository for managing Household data."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, id: UUID) -> HouseholdProfile | None:
        """Fetch household by UUID."""
        stmt = select(HouseholdModel).where(HouseholdModel.id == id)
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain(model)

    async def save(self, profile: HouseholdProfile) -> HouseholdProfile:
        """Create or update household profile."""
        if profile.id:
            household_id = UUID(profile.id)
            stmt = select(HouseholdModel).where(HouseholdModel.id == household_id)
            result = await self.db.execute(stmt)
            model = result.scalar_one_or_none()
        else:
            model = None

        if model:
            # Update
            model.location_lat = profile.location_lat
            model.location_lng = profile.location_lng
            model.location_name = profile.location_name
            model.household_size = profile.household_size
            model.has_children = profile.has_children
            model.has_elderly = profile.has_elderly
            model.has_pets = profile.has_pets
            model.housing_type = profile.housing_type.value
            model.has_vehicle = profile.has_vehicle
            model.accessibility_needs = profile.accessibility_needs
            model.preferred_language = profile.preferred_language
            model.updated_at = datetime.utcnow()
        else:
            # Insert
            model = HouseholdModel(
                location_lat=profile.location_lat,
                location_lng=profile.location_lng,
                location_name=profile.location_name,
                household_size=profile.household_size,
                has_children=profile.has_children,
                has_elderly=profile.has_elderly,
                has_pets=profile.has_pets,
                housing_type=profile.housing_type.value,
                has_vehicle=profile.has_vehicle,
                accessibility_needs=profile.accessibility_needs,
                preferred_language=profile.preferred_language,
            )
            self.db.add(model)

        await self.db.commit()
        await self.db.refresh(model)
        return self._to_domain(model)

    def _to_domain(self, model: HouseholdModel) -> HouseholdProfile:
        return HouseholdProfile(
            id=str(model.id),
            location_lat=model.location_lat,
            location_lng=model.location_lng,
            location_name=model.location_name,
            household_size=model.household_size,
            has_children=model.has_children,
            has_elderly=model.has_elderly,
            has_pets=model.has_pets,
            housing_type=HousingType(model.housing_type),
            has_vehicle=model.has_vehicle,
            accessibility_needs=model.accessibility_needs,
            preferred_language=model.preferred_language,
        )


class ChecklistRepository:
    """Repository for managing Checklist items."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_household(self, household_id: UUID) -> list[ChecklistItem]:
        """Fetch all checklist items for a household."""
        stmt = (
            select(ChecklistItemModel)
            .where(ChecklistItemModel.household_id == household_id)
            .order_index
        ) = ChecklistItemModel.priority.desc()
        # Fix ordering
        stmt = (
            select(ChecklistItemModel)
            .where(ChecklistItemModel.household_id == household_id)
            .order_by(
                ChecklistItemModel.priority.desc(), ChecklistItemModel.created_at.asc(),
            )
        )
        result = await self.db.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def save_all(self, items: list[ChecklistItem]) -> list[ChecklistItem]:
        """Save list of checklist items."""
        saved_items = []
        for item in items:
            if item.id:
                stmt = select(ChecklistItemModel).where(
                    ChecklistItemModel.id == UUID(item.id),
                )
                result = await self.db.execute(stmt)
                model = result.scalar_one_or_none()
            else:
                model = None

            if model:
                model.status = item.status.value
                model.title = item.title
                model.description = item.description
                model.category = item.category.value
                model.priority = item.priority
                model.weather_context = item.weather_context
                model.updated_at = datetime.utcnow()
            else:
                model = ChecklistItemModel(
                    household_id=UUID(item.household_id),
                    title=item.title,
                    description=item.description,
                    category=item.category.value,
                    status=item.status.value,
                    priority=item.priority,
                    weather_context=item.weather_context,
                )
                self.db.add(model)
            saved_items.append(model)

        await self.db.commit()
        for model in saved_items:
            await self.db.refresh(model)

        return [self._to_domain(m) for m in saved_items]

    async def delete_by_household_and_category(
        self, household_id: UUID, category: ChecklistCategory,
    ) -> None:
        """Delete all items matching category."""
        stmt = delete(ChecklistItemModel).where(
            ChecklistItemModel.household_id == household_id,
            ChecklistItemModel.category == category.value,
        )
        await self.db.execute(stmt)
        await self.db.commit()

    def _to_domain(self, model: ChecklistItemModel) -> ChecklistItem:
        return ChecklistItem(
            id=str(model.id),
            household_id=str(model.household_id),
            title=model.title,
            description=model.description,
            category=ChecklistCategory(model.category),
            status=ChecklistStatus(model.status),
            priority=model.priority,
            weather_context=model.weather_context,
        )


class AlertRepository:
    """Repository for managing Alerts."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_active_alerts(self) -> list[Alert]:
        """Get all currently active alerts."""
        now = datetime.utcnow()
        stmt = (
            select(AlertModel)
            .where(
                AlertModel.is_active,
                (AlertModel.expires_at is None) | (AlertModel.expires_at > now),
            )
            .order_by(AlertModel.triggered_at.desc())
        )
        result = await self.db.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_by_rule_and_location(
        self, rule_id: str, lat: float, lng: float, min_time: datetime,
    ) -> list[Alert]:
        """Fetch matching alerts for dedup/cooldown logic."""
        # Simple rounding for approximate spatial proximity within ~1km
        lat_rounded = round(lat, 2)
        lng_rounded = round(lng, 2)
        stmt = select(AlertModel).where(
            AlertModel.rule_id == rule_id, AlertModel.triggered_at >= min_time,
        )
        result = await self.db.execute(stmt)
        models = result.scalars().all()
        # Filter in Python for double precision proximity
        matched = []
        for m in models:
            if m.location_lat is not None and m.location_lng is not None:
                if (
                    round(m.location_lat, 2) == lat_rounded
                    and round(m.location_lng, 2) == lng_rounded
                ):
                    matched.append(self._to_domain(m))
        return matched

    async def save(self, alert: Alert) -> Alert:
        """Save a new alert to history."""
        model = AlertModel(
            rule_id=alert.rule_id,
            severity=alert.severity.value,
            title=alert.title,
            description=alert.description,
            location_lat=alert.location_lat,
            location_lng=alert.location_lng,
            location_name=alert.location_name,
            source=alert.source.value,
            source_data=alert.source_data,
            weather_data_age_seconds=alert.weather_data_age_seconds,
            triggered_at=alert.triggered_at,
            expires_at=alert.expires_at,
            is_active=alert.is_active,
            citizen_message=alert.citizen_message,
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_domain(model)

    def _to_domain(self, model: AlertModel) -> Alert:
        return Alert(
            id=str(model.id),
            rule_id=model.rule_id,
            severity=AlertSeverity(model.severity),
            title=model.title,
            description=model.description,
            location_lat=model.location_lat,
            location_lng=model.location_lng,
            location_name=model.location_name,
            source=AlertSource(model.source),
            source_data=model.source_data,
            weather_data_age_seconds=model.weather_data_age_seconds,
            triggered_at=model.triggered_at,
            expires_at=model.expires_at,
            is_active=model.is_active,
            citizen_message=model.citizen_message,
        )


class PreparednessPlanRepository:
    """Repository for cached Preparedness Plans."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_household(
        self, household_id: UUID,
    ) -> PreparednessPlanModel | None:
        """Fetch plan by household ID."""
        stmt = (
            select(PreparednessPlanModel)
            .where(PreparednessPlanModel.household_id == household_id)
            .order_by(PreparednessPlanModel.generated_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save(
        self,
        household_id: UUID,
        plan_data: dict,
        weather_context: dict,
        risk_level: str,
        ttl_hours: int = 1,
    ):
        """Save a generated preparedness plan."""
        # Expire older plans
        stmt = delete(PreparednessPlanModel).where(
            PreparednessPlanModel.household_id == household_id,
        )
        await self.db.execute(stmt)

        now = datetime.utcnow()
        expires = now + timedelta(hours=ttl_hours) if ttl_hours else None
        model = PreparednessPlanModel(
            household_id=household_id,
            plan_data=plan_data,
            weather_context=weather_context,
            risk_level=risk_level,
            generated_at=now,
            expires_at=expires,
        )
        self.db.add(model)
        await self.db.commit()
        return model
