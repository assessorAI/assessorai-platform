-- Migration: Add created_at timestamp to mandatos
-- Date: 2025-12-10
-- Purpose: Enable temporal analysis and "mandato ativo" calculation

-- Add created_at column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'mandatos' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE mandatos ADD COLUMN created_at TIMESTAMP;
    END IF;
END $$;

-- Backfill: set to current timestamp for existing records
-- Admin can manually backfill if historical dates are needed
UPDATE mandatos 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

-- Make it NOT NULL with server default for new records
ALTER TABLE mandatos ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
DO $$
BEGIN
    ALTER TABLE mandatos ALTER COLUMN created_at SET NOT NULL;
EXCEPTION
    WHEN others THEN NULL; -- Column might already be NOT NULL
END $$;

-- Create index for temporal queries (most recent first)
CREATE INDEX IF NOT EXISTS idx_mandatos_created_at ON mandatos(created_at DESC);

-- Keep 'data' field for backward compatibility but mark as deprecated
COMMENT ON COLUMN mandatos.data IS 'DEPRECATED: Use created_at instead';
