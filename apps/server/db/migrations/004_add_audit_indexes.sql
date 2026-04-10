-- Migration: Add composite indexes for audit log queries
-- Date: 2025-01-18
-- Purpose: Optimize common audit log query patterns with composite indexes

-- Composite index for filtering by event type and sorting by date
CREATE INDEX IF NOT EXISTS idx_audit_event_created 
ON audit_logs(event_type, created_at DESC);

-- Composite index for user activity timeline
CREATE INDEX IF NOT EXISTS idx_audit_user_created 
ON audit_logs(actor_user_id, created_at DESC);

-- Composite index for mandato activity timeline
CREATE INDEX IF NOT EXISTS idx_audit_mandato_created 
ON audit_logs(actor_mandato_id, created_at DESC);

-- Composite index for event type + user queries
CREATE INDEX IF NOT EXISTS idx_audit_event_user 
ON audit_logs(event_type, actor_user_id, created_at DESC);

-- Composite index for event type + mandato queries
CREATE INDEX IF NOT EXISTS idx_audit_event_mandato 
ON audit_logs(event_type, actor_mandato_id, created_at DESC);
