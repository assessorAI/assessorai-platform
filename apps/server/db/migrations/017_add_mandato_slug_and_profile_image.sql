-- Migration 017: Add slug and profile_image_url to mandatos
-- slug: unique, auto-generated from nome_parlamentar if not provided
-- profile_image_url: URL to GCS-stored 400x400 profile image

-- Require unaccent extension for slug backfill
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Add columns (idempotent)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'mandatos' AND column_name = 'slug'
    ) THEN
        ALTER TABLE mandatos ADD COLUMN slug VARCHAR(120);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'mandatos' AND column_name = 'profile_image_url'
    ) THEN
        ALTER TABLE mandatos ADD COLUMN profile_image_url TEXT;
    END IF;
END $$;

-- Backfill slugs for existing mandatos
-- Strategy: lowercase + unaccent + replace non-alphanumeric with hyphens
-- Duplicate raw slugs get numeric suffixes (-2, -3, ...) ordered by id
UPDATE mandatos SET slug = sub.final_slug
FROM (
    WITH base AS (
        SELECT id,
               CASE
                   WHEN nome_parlamentar IS NOT NULL AND trim(nome_parlamentar) != ''
                   THEN regexp_replace(
                            regexp_replace(
                                lower(unaccent(trim(nome_parlamentar))),
                                '[^a-z0-9]+', '-', 'g'
                            ),
                            '^-+|-+$', '', 'g'
                        )
                   ELSE 'mandato-' || id::text
               END AS raw_slug
        FROM mandatos
    ),
    ranked AS (
        SELECT id, raw_slug,
               row_number() OVER (PARTITION BY raw_slug ORDER BY id) AS rn
        FROM base
    )
    SELECT id,
           CASE WHEN rn = 1 THEN raw_slug
                ELSE raw_slug || '-' || rn::text
           END AS final_slug
    FROM ranked
) sub
WHERE mandatos.id = sub.id;

-- Unique constraint and index
CREATE UNIQUE INDEX IF NOT EXISTS ix_mandatos_slug ON mandatos(slug);

COMMENT ON COLUMN mandatos.slug IS 'URL-friendly unique identifier, auto-generated from nome_parlamentar';
COMMENT ON COLUMN mandatos.profile_image_url IS 'GCS URL for 400x400 profile image';
