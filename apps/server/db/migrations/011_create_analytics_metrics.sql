-- Migration: Create materialized analytics metrics table
-- Date: 2025-12-10
-- Purpose: Pre-calculated metrics for performance

CREATE TABLE IF NOT EXISTS analytics_metrics (
    id SERIAL PRIMARY KEY,
    
    -- Scope
    entity_type VARCHAR(20) NOT NULL, -- 'mandato' or 'user'
    entity_id INTEGER NOT NULL,
    
    -- Time window
    reference_date DATE NOT NULL, -- YYYY-MM-01 for monthly aggregation
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Status indicators
    status VARCHAR(20), -- 'ativo' or 'inativo'
    risk_level VARCHAR(20), -- 'ok', 'baixo', 'medio', 'alto'
    
    -- Activity metrics
    ultimo_login TIMESTAMP,
    dias_sem_login INTEGER,
    logs_7d INTEGER DEFAULT 0,
    logs_30d INTEGER DEFAULT 0,
    logs_total INTEGER DEFAULT 0,
    
    -- Funcionalidades (JSONB for flexibility)
    funcionalidades_count JSONB, -- {"expert_pl": 10, "oficios": 5, ...}
    
    -- Constraints
    UNIQUE(entity_type, entity_id, reference_date)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_analytics_entity ON analytics_metrics(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics_metrics(reference_date DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_status ON analytics_metrics(entity_type, status, reference_date);
CREATE INDEX IF NOT EXISTS idx_analytics_risk ON analytics_metrics(entity_type, risk_level, reference_date);

-- Composite index for common query pattern
CREATE INDEX IF NOT EXISTS idx_analytics_entity_date ON analytics_metrics(entity_type, entity_id, reference_date DESC);
