-- Migration 016: remove gerencie-related and objetivos schema pieces

-- Remove legacy evaluation cases for deprecated gerencie test types
DELETE FROM prompt_evaluation_cases
WHERE test_type IN ('objetivo_ano', 'objetivo_metas');

-- Remove deprecated prompt templates
DELETE FROM prompt_templates
WHERE template_type IN ('gerencie_objetivo_ano', 'gerencie_objetivo_metas');

-- Narrow allowed test_type values for prompt evaluation cases
ALTER TABLE prompt_evaluation_cases
    DROP CONSTRAINT IF EXISTS valid_test_type;

ALTER TABLE prompt_evaluation_cases
    ADD CONSTRAINT valid_test_type CHECK (test_type IN (
        'oficio',
        'criar_projeto_pl',
        'constitucionalidade',
        'criar_emenda',
        'sugestao_emendas',
        'sugestao_projetos'
    ));

-- Drop objetivos/metas tables (metas first due to FK)
DROP TABLE IF EXISTS metas;
DROP TABLE IF EXISTS objetivos;
