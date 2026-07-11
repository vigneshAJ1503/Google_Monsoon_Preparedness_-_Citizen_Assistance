"""Create initial tables

Revision ID: 001
Revises: 
Create Date: 2026-07-11 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Households table
    op.create_table(
        'households',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('location_lat', sa.Double(), nullable=False),
        sa.Column('location_lng', sa.Double(), nullable=False),
        sa.Column('location_name', sa.String(255), nullable=True),
        sa.Column('household_size', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('has_children', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_elderly', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_pets', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('housing_type', sa.String(50), nullable=False, server_default='apartment'),
        sa.Column('has_vehicle', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('accessibility_needs', sa.Text(), nullable=True),
        sa.Column('preferred_language', sa.String(10), nullable=False, server_default='en'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # Checklist items table
    op.create_table(
        'checklist_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('household_id', UUID(as_uuid=True), sa.ForeignKey('households.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('weather_context', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_checklist_household', 'checklist_items', ['household_id'])

    # Alerts table
    op.create_table(
        'alerts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('rule_id', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location_lat', sa.Double(), nullable=True),
        sa.Column('location_lng', sa.Double(), nullable=True),
        sa.Column('location_name', sa.String(255), nullable=True),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('source_data', JSONB(), nullable=True),
        sa.Column('weather_data_age_seconds', sa.Integer(), nullable=True),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('citizen_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_alerts_rule_location', 'alerts', ['rule_id', 'location_lat', 'location_lng', 'triggered_at'])
    op.create_index('idx_alerts_active', 'alerts', ['is_active', 'expires_at'])

    # Chat messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('household_id', UUID(as_uuid=True), sa.ForeignKey('households.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_chat_household', 'chat_messages', ['household_id', 'created_at'])

    # Preparedness plans table
    op.create_table(
        'preparedness_plans',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('household_id', UUID(as_uuid=True), sa.ForeignKey('households.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan_data', JSONB(), nullable=False),
        sa.Column('weather_context', JSONB(), nullable=True),
        sa.Column('risk_level', sa.String(20), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_plans_household', 'preparedness_plans', ['household_id', 'generated_at'])


def downgrade() -> None:
    op.drop_table('preparedness_plans')
    op.drop_table('chat_messages')
    op.drop_table('alerts')
    op.drop_table('checklist_items')
    op.drop_table('households')