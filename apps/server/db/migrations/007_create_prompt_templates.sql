-- Migration 007: Create prompt_templates table for versioned prompt management
-- Allows admins to customize and version LLM prompts with fallback to file system

CREATE TABLE IF NOT EXISTS prompt_templates (
    id SERIAL PRIMARY KEY,
    template_type VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    content TEXT NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT,
    CONSTRAINT unique_template_version UNIQUE(template_type, version)
);

-- Index for fast lookup of default templates (most common query)
CREATE UNIQUE INDEX IF NOT EXISTS idx_prompt_templates_type_default 
ON prompt_templates(template_type) 
WHERE is_default = TRUE AND is_active = TRUE;

-- Index for listing active templates
CREATE INDEX IF NOT EXISTS idx_prompt_templates_active 
ON prompt_templates(is_active) 
WHERE is_active = TRUE;

-- Index for ordering by creation date
CREATE INDEX IF NOT EXISTS idx_prompt_templates_created_at 
ON prompt_templates(created_at DESC);

-- Index for filtering by type
CREATE INDEX IF NOT EXISTS idx_prompt_templates_type 
ON prompt_templates(template_type);

-- Comments for documentation
COMMENT ON TABLE prompt_templates IS 'Versioned storage for LLM prompt templates with admin customization';
COMMENT ON COLUMN prompt_templates.template_type IS 'Template identifier matching filename (e.g., generate_oficio)';
COMMENT ON COLUMN prompt_templates.version IS 'Auto-incremented version number per template_type';
COMMENT ON COLUMN prompt_templates.is_default IS 'Only one version per type can be default (enforced by unique index)';
COMMENT ON COLUMN prompt_templates.is_active IS 'Soft delete flag - inactive templates are hidden but preserved';
COMMENT ON COLUMN prompt_templates.content IS 'Template content in Markdown/Mustache format';
