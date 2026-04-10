-- Migration 009: Refactor evaluation system for multi-mandato × multi-template permutations
-- Enables testing same case across multiple mandatos AND multiple template versions simultaneously

-- Add mandato_id and template_id to results table for N×M permutations
ALTER TABLE prompt_evaluation_results 
ADD COLUMN IF NOT EXISTS mandato_id INTEGER REFERENCES mandatos(id),
ADD COLUMN IF NOT EXISTS template_id INTEGER REFERENCES prompt_templates(id);

-- Add arrays to track which mandatos/templates were selected for the run
ALTER TABLE prompt_evaluation_runs
ADD COLUMN IF NOT EXISTS mandato_ids INTEGER[],
ADD COLUMN IF NOT EXISTS template_ids INTEGER[];

-- Indexes for efficient filtering and joins
CREATE INDEX IF NOT EXISTS idx_eval_results_mandato ON prompt_evaluation_results(mandato_id);
CREATE INDEX IF NOT EXISTS idx_eval_results_template ON prompt_evaluation_results(template_id);
CREATE INDEX IF NOT EXISTS idx_eval_runs_mandatos ON prompt_evaluation_runs USING GIN(mandato_ids);
CREATE INDEX IF NOT EXISTS idx_eval_runs_templates ON prompt_evaluation_runs USING GIN(template_ids);

-- Comments for documentation
COMMENT ON COLUMN prompt_evaluation_results.mandato_id IS 'Specific mandato used for this result (enables comparison across mandatos)';
COMMENT ON COLUMN prompt_evaluation_results.template_id IS 'Specific template version used for this result (enables A/B testing)';
COMMENT ON COLUMN prompt_evaluation_runs.mandato_ids IS 'Array of mandato IDs selected for this evaluation run';
COMMENT ON COLUMN prompt_evaluation_runs.template_ids IS 'Array of template IDs selected for this evaluation run';
