-- Create table for vectorised legislative references
CREATE TABLE IF NOT EXISTS projetos_referencias (
    id SERIAL PRIMARY KEY,
    title TEXT,
    house TEXT,
    type TEXT,
    number INTEGER,
    presentation_date TEXT,
    year INTEGER,
    author TEXT[],
    subject TEXT,
    full_text TEXT,
    chunk_text TEXT NOT NULL,
    chunk_number INTEGER NOT NULL DEFAULT 0,
    length INTEGER,
    url TEXT,
    scraped_at TEXT,
    metadata_json JSONB,
    embedding vector(1536) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_projetos_referencias_chunk ON projetos_referencias (title, chunk_number);

-- Note: ivfflat requires `SET enable_seqscan = off;` for best performance and enough lists (tunable)
CREATE INDEX IF NOT EXISTS idx_projetos_referencias_embedding
    ON projetos_referencias USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);