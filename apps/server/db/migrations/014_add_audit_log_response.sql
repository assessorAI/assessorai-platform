-- Add response column to audit_logs table to separate LLM outputs from metadata
-- This migration creates a dedicated JSONB column for storing LLM-generated responses
-- separately from the payload which contains request metadata and context.

-- Add response column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'audit_logs' AND column_name = 'response'
    ) THEN
        ALTER TABLE audit_logs ADD COLUMN response JSONB;
    END IF;
END $$;

-- Add GIN index for efficient queries on response content (if it doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'audit_logs' AND indexname = 'idx_audit_logs_response'
    ) THEN
        CREATE INDEX idx_audit_logs_response ON audit_logs USING gin(response);
    END IF;
END $$;

-- Add documentation comment
COMMENT ON COLUMN audit_logs.response IS 'LLM-generated response or operation output (separate from payload metadata)';
