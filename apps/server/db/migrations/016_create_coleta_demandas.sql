-- Migration: create coleta demandas public intake tables
-- Date: 2026-02-24

CREATE TABLE IF NOT EXISTS coleta_demandas_contacts (
    id INTEGER PRIMARY KEY,
    mandato_id INTEGER NOT NULL,
    nome_completo VARCHAR(255) NOT NULL,
    telefone_normalizado VARCHAR(20) NOT NULL,
    telefone_exibicao VARCHAR(30) NOT NULL,
    bairro VARCHAR(120) NOT NULL,
    data_nascimento DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (mandato_id) REFERENCES mandatos(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_coleta_contacts_mandato_phone
    ON coleta_demandas_contacts(mandato_id, telefone_normalizado);

CREATE INDEX IF NOT EXISTS idx_coleta_contacts_mandato
    ON coleta_demandas_contacts(mandato_id);

CREATE TABLE IF NOT EXISTS coleta_demandas (
    id INTEGER PRIMARY KEY,
    mandato_id INTEGER NOT NULL,
    contact_id INTEGER,
    descricao TEXT NOT NULL,
    endereco VARCHAR(255),
    nao_sei_endereco BOOLEAN NOT NULL DEFAULT FALSE,
    ponto_referencia VARCHAR(255),
    nome_completo VARCHAR(255) NOT NULL,
    telefone_normalizado VARCHAR(20) NOT NULL,
    telefone_exibicao VARCHAR(30) NOT NULL,
    bairro VARCHAR(120) NOT NULL,
    data_nascimento DATE NOT NULL,
    nome_responsavel VARCHAR(255),
    telefone_responsavel VARCHAR(30),
    salvar_dados BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (mandato_id) REFERENCES mandatos(id),
    FOREIGN KEY (contact_id) REFERENCES coleta_demandas_contacts(id)
);

CREATE INDEX IF NOT EXISTS idx_coleta_demandas_mandato
    ON coleta_demandas(mandato_id, created_at);

CREATE INDEX IF NOT EXISTS idx_coleta_demandas_phone
    ON coleta_demandas(telefone_normalizado);

CREATE TABLE IF NOT EXISTS coleta_demandas_attachments (
    id INTEGER PRIMARY KEY,
    demanda_id INTEGER NOT NULL,
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    size_bytes BIGINT NOT NULL,
    storage_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (demanda_id) REFERENCES coleta_demandas(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_coleta_demandas_attachments_demanda
    ON coleta_demandas_attachments(demanda_id);
