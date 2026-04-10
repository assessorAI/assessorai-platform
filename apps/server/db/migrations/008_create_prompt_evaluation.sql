-- Migration 008: Create prompt evaluation system tables
-- Allows admins to create test cases, run evaluations, and track results

-- Table 1: Evaluation test cases
CREATE TABLE IF NOT EXISTS prompt_evaluation_cases (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    test_type VARCHAR(100) NOT NULL,
    input_data JSONB NOT NULL,
    expected_output TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_test_type CHECK (test_type IN (
        'oficio',
        'criar_projeto_pl',
        'constitucionalidade',
        'criar_emenda',
        'sugestao_emendas',
        'sugestao_projetos',
        'objetivo_ano',
        'objetivo_metas'
    ))
);

-- Table 2: Evaluation runs (execution metadata)
CREATE TABLE IF NOT EXISTS prompt_evaluation_runs (
    id SERIAL PRIMARY KEY,
    run_name VARCHAR(200),
    template_id INTEGER REFERENCES prompt_templates(id) ON DELETE SET NULL,
    executed_by INTEGER REFERENCES users(id),
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_cases INTEGER DEFAULT 0,
    completed_cases INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'running',
    CONSTRAINT valid_status CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
);

-- Table 3: Individual evaluation results
CREATE TABLE IF NOT EXISTS prompt_evaluation_results (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES prompt_evaluation_runs(id) ON DELETE CASCADE,
    case_id INTEGER REFERENCES prompt_evaluation_cases(id) ON DELETE CASCADE,
    actual_output TEXT,
    execution_time_ms INTEGER,
    llm_evaluation_score INTEGER,
    llm_evaluation_analysis TEXT,
    human_evaluation TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_score CHECK (llm_evaluation_score IS NULL OR (llm_evaluation_score >= 0 AND llm_evaluation_score <= 100))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_eval_cases_type ON prompt_evaluation_cases(test_type);
CREATE INDEX IF NOT EXISTS idx_eval_cases_active ON prompt_evaluation_cases(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_eval_cases_created_at ON prompt_evaluation_cases(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_eval_runs_template ON prompt_evaluation_runs(template_id);
CREATE INDEX IF NOT EXISTS idx_eval_runs_executed_at ON prompt_evaluation_runs(executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_eval_runs_status ON prompt_evaluation_runs(status);

CREATE INDEX IF NOT EXISTS idx_eval_results_run ON prompt_evaluation_results(run_id);
CREATE INDEX IF NOT EXISTS idx_eval_results_case ON prompt_evaluation_results(case_id);
CREATE INDEX IF NOT EXISTS idx_eval_results_score ON prompt_evaluation_results(llm_evaluation_score);

-- Comments for documentation
COMMENT ON TABLE prompt_evaluation_cases IS 'Test cases with input/expected output for prompt validation';
COMMENT ON COLUMN prompt_evaluation_cases.test_type IS 'Type of endpoint to test (maps to API endpoints)';
COMMENT ON COLUMN prompt_evaluation_cases.input_data IS 'JSON structure matching the endpoint payload';
COMMENT ON COLUMN prompt_evaluation_cases.expected_output IS 'Expected result to compare against actual output';

COMMENT ON TABLE prompt_evaluation_runs IS 'Execution metadata for batch evaluation runs';
COMMENT ON COLUMN prompt_evaluation_runs.template_id IS 'Which prompt template version was used for this run';
COMMENT ON COLUMN prompt_evaluation_runs.status IS 'Current status: running, completed, failed, cancelled';

COMMENT ON TABLE prompt_evaluation_results IS 'Individual test results with LLM and human evaluation';
COMMENT ON COLUMN prompt_evaluation_results.llm_evaluation_score IS 'AI-generated quality score from 0-100';
COMMENT ON COLUMN prompt_evaluation_results.human_evaluation IS 'Human reviewer notes and assessment';
COMMENT ON COLUMN prompt_evaluation_results.error_message IS 'Error details if the test execution failed';
