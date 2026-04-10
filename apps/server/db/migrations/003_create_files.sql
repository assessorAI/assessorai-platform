-- Create files table with embedding support
CREATE TABLE IF NOT EXISTS files (
    id SERIAL PRIMARY KEY,
    mandato_id INTEGER REFERENCES mandatos(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL DEFAULT 'document',
    file_path TEXT NOT NULL,
    file_size BIGINT,
    content_type VARCHAR(100),
    upload_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Embedding support
    extracted_text TEXT,
    embedding vector(1536),
    has_embeddings BOOLEAN NOT NULL DEFAULT FALSE,
    chunk_count INTEGER NOT NULL DEFAULT 0
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_files_mandato_id ON files (mandato_id);
CREATE INDEX IF NOT EXISTS ix_files_user_id ON files (user_id);
CREATE INDEX IF NOT EXISTS ix_files_file_type ON files (file_type);
CREATE INDEX IF NOT EXISTS ix_files_upload_date ON files (upload_date);

-- Create file_chunks table for large files with multiple embeddings
CREATE TABLE IF NOT EXISTS file_chunks (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
    chunk_number INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    token_count INTEGER
);

-- Create indexes for file_chunks
CREATE INDEX IF NOT EXISTS ix_file_chunks_file_id ON file_chunks (file_id);
CREATE INDEX IF NOT EXISTS ix_file_chunks_chunk_number ON file_chunks (file_id, chunk_number);