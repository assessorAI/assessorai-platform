-- Migration: Create vector_import_jobs table for async import tracking
-- This table tracks the status of background vector document imports

CREATE TABLE IF NOT EXISTS vector_import_jobs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    total_items INTEGER DEFAULT 0,
    processed_chunks INTEGER DEFAULT 0,
    error_message TEXT,
    created_by INTEGER REFERENCES users(id)
);

-- Index for sorting by creation date (most recent first)
CREATE INDEX IF NOT EXISTS idx_vector_import_jobs_created_at ON vector_import_jobs(created_at DESC);

-- Index for filtering by status
CREATE INDEX IF NOT EXISTS idx_vector_import_jobs_status ON vector_import_jobs(status);

-- Index for user-specific queries
CREATE INDEX IF NOT EXISTS idx_vector_import_jobs_created_by ON vector_import_jobs(created_by);
