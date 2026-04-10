-- Migration: Add last_login fields to users and mandatos
-- Date: 2026-01-26
-- Purpose: Persist last login timestamps for cheap list ordering/filtering

-- dialect: postgresql
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'last_login_at'
    ) THEN
        ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;
    END IF;
END $$;

-- dialect: postgresql
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'mandatos' AND column_name = 'last_login_at'
    ) THEN
        ALTER TABLE mandatos ADD COLUMN last_login_at TIMESTAMP;
    END IF;
END $$;

-- dialect: postgresql
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'mandatos' AND column_name = 'last_login_user_id'
    ) THEN
        ALTER TABLE mandatos ADD COLUMN last_login_user_id INTEGER;
    END IF;
END $$;

-- dialect: postgresql
DO $$
BEGIN
    -- Add FK if not exists (best-effort)
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints tc
        WHERE tc.table_name = 'mandatos'
          AND tc.constraint_type = 'FOREIGN KEY'
          AND tc.constraint_name = 'fk_mandatos_last_login_user_id'
    ) THEN
        ALTER TABLE mandatos
            ADD CONSTRAINT fk_mandatos_last_login_user_id
            FOREIGN KEY (last_login_user_id) REFERENCES users(id);
    END IF;
EXCEPTION
    WHEN others THEN NULL;
END $$;

-- dialect: postgresql
CREATE INDEX IF NOT EXISTS idx_users_last_login_at ON users(last_login_at DESC);
-- dialect: postgresql
CREATE INDEX IF NOT EXISTS idx_mandatos_last_login_at ON mandatos(last_login_at DESC);
-- dialect: postgresql
CREATE INDEX IF NOT EXISTS idx_mandatos_last_login_user_id ON mandatos(last_login_user_id);

-- dialect: sqlite
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at DATETIME;

-- dialect: sqlite
ALTER TABLE mandatos ADD COLUMN IF NOT EXISTS last_login_at DATETIME;

-- dialect: sqlite
ALTER TABLE mandatos ADD COLUMN IF NOT EXISTS last_login_user_id INTEGER;

-- dialect: sqlite
CREATE INDEX IF NOT EXISTS idx_users_last_login_at ON users(last_login_at);

-- dialect: sqlite
CREATE INDEX IF NOT EXISTS idx_mandatos_last_login_at ON mandatos(last_login_at);

-- dialect: sqlite
CREATE INDEX IF NOT EXISTS idx_mandatos_last_login_user_id ON mandatos(last_login_user_id);
