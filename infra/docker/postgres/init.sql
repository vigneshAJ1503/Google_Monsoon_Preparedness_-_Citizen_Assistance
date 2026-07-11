-- Monsoon Preparedness Database Initialization
-- This runs on first container startup

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Household profiles
CREATE TABLE IF NOT EXISTS households (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_lat DOUBLE PRECISION NOT NULL,
    location_lng DOUBLE PRECISION NOT NULL,
    location_name VARCHAR(255),
    household_size INTEGER DEFAULT 1,
    has_children BOOLEAN DEFAULT FALSE,
    has_elderly BOOLEAN DEFAULT FALSE,
    has_pets BOOLEAN DEFAULT FALSE,
    housing_type VARCHAR(50) DEFAULT 'apartment',
    has_vehicle BOOLEAN DEFAULT FALSE,
    accessibility_needs TEXT,
    preferred_language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Checklist items
CREATE TABLE IF NOT EXISTS checklist_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    household_id UUID REFERENCES households(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'not_applicable')),
    priority INTEGER DEFAULT 0,
    weather_context TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alerts history
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('LOW', 'MODERATE', 'HIGH', 'SEVERE')),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    location_lat DOUBLE PRECISION,
    location_lng DOUBLE PRECISION,
    location_name VARCHAR(255),
    source VARCHAR(100) NOT NULL,
    source_data JSONB,
    weather_data_age_seconds INTEGER,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    citizen_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for alert deduplication and cooldown queries
CREATE INDEX IF NOT EXISTS idx_alerts_rule_location ON alerts(rule_id, location_lat, location_lng, triggered_at);
CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(is_active, expires_at);

-- Chat history (for assistant context)
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    household_id UUID REFERENCES households(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_household ON chat_messages(household_id, created_at DESC);

-- Preparedness plans (cached)
CREATE TABLE IF NOT EXISTS preparedness_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    household_id UUID REFERENCES households(id) ON DELETE CASCADE,
    plan_data JSONB NOT NULL,
    weather_context JSONB,
    risk_level VARCHAR(20),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_plans_household ON preparedness_plans(household_id, generated_at DESC);
