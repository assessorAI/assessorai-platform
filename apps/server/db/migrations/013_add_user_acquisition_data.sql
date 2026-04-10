-- Migration 013: Add user acquisition tracking via JSONB field
-- Date: 2026-01-16
-- Purpose: Track user acquisition sources (UTM params, custom query strings, etc)
--          Single JSONB field for maximum flexibility

-- Add acquisition_data column to users table (idempotent)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='users' AND column_name='acquisition_data') THEN
        ALTER TABLE users ADD COLUMN acquisition_data JSONB;
    END IF;
END $$;

-- Create GIN index for efficient JSONB queries (idempotent)
-- This allows fast queries like: WHERE acquisition_data->>'utm_source' = 'google'
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes 
                   WHERE tablename='users' AND indexname='idx_users_acquisition_data') THEN
        CREATE INDEX idx_users_acquisition_data ON users USING gin(acquisition_data);
    END IF;
END $$;

-- Add comment for documentation
COMMENT ON COLUMN users.acquisition_data IS 'Stores all query parameters from registration (UTM params, custom fields, etc). Structure: {"utm_source": "google", "utm_campaign": "campaign_name", "captured_at": "ISO timestamp", ...}';
