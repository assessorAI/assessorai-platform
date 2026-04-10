-- Create final base tables for the application

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone VARCHAR(30),
    permission_level VARCHAR(20),
    lgpd_check BOOLEAN DEFAULT FALSE,
    role VARCHAR(50),
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

-- Mandatos table
CREATE TABLE IF NOT EXISTS mandatos (
    id SERIAL PRIMARY KEY,
    nome_parlamentar VARCHAR(50),
    casa_legislativa VARCHAR(50),
    cargo_parlamentar VARCHAR(50),
    esfera VARCHAR(50),
    municipio VARCHAR(50),
    ue VARCHAR(2),
    temas_interesse TEXT,
    perfil_parlamentar TEXT,
    espectro_politico TEXT,
    partido VARCHAR(50),
    data TEXT
);

CREATE INDEX IF NOT EXISTS ix_mandatos_cargo_parlamentar ON mandatos (cargo_parlamentar);

-- Association table for mandato-user many-to-many
CREATE TABLE IF NOT EXISTS mandato_user_link (
    mandato_id INTEGER REFERENCES mandatos(id),
    user_id INTEGER REFERENCES users(id),
    PRIMARY KEY (mandato_id, user_id)
);

-- Objetivos table
CREATE TABLE IF NOT EXISTS objetivos (
    id SERIAL PRIMARY KEY,
    mandato_id INTEGER REFERENCES mandatos(id),
    titulo VARCHAR(255) NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_objetivos_mandato_id ON objetivos (mandato_id);

-- Metas table
CREATE TABLE IF NOT EXISTS metas (
    id SERIAL PRIMARY KEY,
    objetivo_id INTEGER REFERENCES objetivos(id),
    descricao TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_metas_objetivo_id ON metas (objetivo_id);

-- Auth tokens table
CREATE TABLE IF NOT EXISTS auth_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR UNIQUE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_auth_tokens_token ON auth_tokens (token);
CREATE INDEX IF NOT EXISTS ix_auth_tokens_user_id ON auth_tokens (user_id);

-- Password reset tokens table
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR UNIQUE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_token ON password_reset_tokens (token);
CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_user_id ON password_reset_tokens (user_id);

-- User activation tokens table
CREATE TABLE IF NOT EXISTS user_activation_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR UNIQUE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    mandato_id INTEGER REFERENCES mandatos(id) ON DELETE CASCADE,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS ix_user_activation_tokens_token ON user_activation_tokens (token);
CREATE INDEX IF NOT EXISTS ix_user_activation_tokens_user_id ON user_activation_tokens (user_id);
CREATE INDEX IF NOT EXISTS ix_user_activation_tokens_mandato_id ON user_activation_tokens (mandato_id);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    subject_id TEXT,
    actor_user_id INTEGER,
    actor_mandato_id INTEGER,
    actor_permission_level TEXT,
    request_id TEXT,
    payload JSONB,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type_created_at ON audit_logs (event_type, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_user_created_at ON audit_logs (actor_user_id, created_at);