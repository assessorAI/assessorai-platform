-- Migration: Add created_at timestamp to users
-- Date: 2025-01-16
-- Purpose: Enable temporal analysis and user registration tracking

-- Add created_at column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE users ADD COLUMN created_at TIMESTAMP;
    END IF;
END $$;

-- Backfill: set to current timestamp for existing records
UPDATE users 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

-- Make it NOT NULL with server default for new records
ALTER TABLE users ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
DO $$
BEGIN
    ALTER TABLE users ALTER COLUMN created_at SET NOT NULL;
EXCEPTION
    WHEN others THEN NULL; -- Column might already be NOT NULL
END $$;

-- Create index for temporal queries (most recent first)
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
