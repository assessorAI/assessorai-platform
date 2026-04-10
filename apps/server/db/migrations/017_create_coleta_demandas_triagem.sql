-- Create triagem table for AI processing of public demandas
CREATE TABLE IF NOT EXISTS coleta_demandas_triagem (
    id SERIAL PRIMARY KEY,
    mandato_id INTEGER NOT NULL REFERENCES mandatos(id),
    coleta_demanda_id INTEGER REFERENCES coleta_demandas(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    tipo TEXT,
    categoria TEXT,

    descricao_original TEXT NOT NULL,
    descricao_processada TEXT,
    descricao_embedding vector(1536),

    local_texto TEXT,

    origem TEXT,

    solicitante_nome TEXT,
    solicitante_email TEXT,
    solicitante_telefone TEXT
);

CREATE INDEX IF NOT EXISTS idx_coleta_demandas_triagem_mandato_id
    ON coleta_demandas_triagem(mandato_id);

CREATE INDEX IF NOT EXISTS idx_coleta_demandas_triagem_coleta_demanda_id
    ON coleta_demandas_triagem(coleta_demanda_id);

CREATE INDEX IF NOT EXISTS idx_coleta_demandas_triagem_created_at
    ON coleta_demandas_triagem(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_coleta_demandas_triagem_tipo
    ON coleta_demandas_triagem(tipo);

CREATE INDEX IF NOT EXISTS idx_coleta_demandas_triagem_categoria
    ON coleta_demandas_triagem(categoria);
