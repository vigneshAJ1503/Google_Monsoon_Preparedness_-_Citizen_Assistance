"""SQLAlchemy ORM models.
Maps database tables to Python objects.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Double,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.infrastructure.persistence.database import Base


class HouseholdModel(Base):
    __tablename__ = "households"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_lat = Column(Double, nullable=False)
    location_lng = Column(Double, nullable=False)
    location_name = Column(String(255), nullable=True)
    household_size = Column(Integer, default=1)
    has_children = Column(Boolean, default=False)
    has_elderly = Column(Boolean, default=False)
    has_pets = Column(Boolean, default=False)
    housing_type = Column(String(50), default="apartment")
    has_vehicle = Column(Boolean, default=False)
    accessibility_needs = Column(Text, nullable=True)
    preferred_language = Column(String(10), default="en")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow,
    )

    # Relationships
    checklist_items = relationship(
        "ChecklistItemModel", back_populates="household", cascade="all, delete-orphan",
    )
    chat_messages = relationship(
        "ChatMessageModel", back_populates="household", cascade="all, delete-orphan",
    )
    plans = relationship(
        "PreparednessPlanModel",
        back_populates="household",
        cascade="all, delete-orphan",
    )


class ChecklistItemModel(Base):
    __tablename__ = "checklist_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    household_id = Column(
        UUID(as_uuid=True),
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    status = Column(String(20), default="pending")
    priority = Column(Integer, default=0)
    weather_context = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow,
    )

    # Relationships
    household = relationship("HouseholdModel", back_populates="checklist_items")


class AlertModel(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    location_lat = Column(Double, nullable=True)
    location_lng = Column(Double, nullable=True)
    location_name = Column(String(255), nullable=True)
    source = Column(String(100), nullable=False)
    source_data = Column(JSONB, nullable=True)
    weather_data_age_seconds = Column(Integer, nullable=True)
    triggered_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    citizen_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index(
            "idx_alerts_rule_location",
            "rule_id",
            "location_lat",
            "location_lng",
            "triggered_at",
        ),
        Index("idx_alerts_active", "is_active", "expires_at"),
    )


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    household_id = Column(
        UUID(as_uuid=True),
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    household = relationship("HouseholdModel", back_populates="chat_messages")

    __table_args__ = (Index("idx_chat_household", "household_id", "created_at"),)


class PreparednessPlanModel(Base):
    __tablename__ = "preparedness_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    household_id = Column(
        UUID(as_uuid=True),
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
    )
    plan_data = Column(JSONB, nullable=False)
    weather_context = Column(JSONB, nullable=True)
    risk_level = Column(String(20), nullable=True)
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    household = relationship("HouseholdModel", back_populates="plans")

    __table_args__ = (Index("idx_plans_household", "household_id", "generated_at"),)
