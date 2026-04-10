# Plano de Revisao Conservadora para Cleanup

## Objetivo
Executar uma revisao segura do repositório, focada em reduzir ruido de arquivos e melhorar organizacao sem alterar comportamento funcional da API ou do console admin.

## Principios
- Priorizar baixo risco: remover apenas o que estiver 100% comprovadamente sem uso.
- Manter compatibilidade: evitar refatoracoes de logica nesta fase.
- Trabalhar em lotes pequenos e verificaveis.
- Registrar decisoes para facilitar revisao posterior.

## Escopo da Fase Conservadora
1. Higiene de repositorio
   - Garantir que artefatos locais nao aparecam como mudancas pendentes.
   - Consolidar regras de ignore para ambiente local e cache.

2. Inventario de arquivos
   - Classificar pastas/arquivos em: codigo ativo, scripts operacionais, documentacao, artefatos locais.
   - Criar lista de candidatos para mover/remover com justificativa.

3. Deteccao de redundancia segura
   - Verificar duplicidades de modulo/pasta (ex.: arquivos com nomes sobrepostos).
   - Confirmar referencias por import, entrypoints, Docker e testes antes de qualquer remocao.

4. Reorganizacao minima
   - Manter a raiz enxuta, movendo apenas itens de baixa controversia para `docs/` ou `scripts/`.
   - Sem alterar contrato de endpoints ou estrutura de dados.

## Critérios de Decisao (Manter vs Remover)
- **Manter** quando houver referencia por:
  - import direto em codigo Python;
  - execucao por scripts de bootstrap/deploy;
  - uso documentado em README/AGENTS;
  - cobertura por testes ativos.
- **Remover/Mover** apenas quando:
  - nao houver referencia cruzada no projeto;
  - nao fizer parte do fluxo de deploy/operacao;
  - impacto puder ser validado por testes/smoke.

## Sequencia de Execucao Recomendada
1. Lote A: `.gitignore` e artefatos locais.
2. Lote B: consolidacao de docs e scripts sem alterar logica.
3. Lote C: remocao de arquivos orfaos comprovados.
4. Lote D: ajustes finais de referencias e validacao.

## Validacao por Lote
- `pytest -q`
- Smoke da API com `DEBUG=True python3 app.py`
- Revisao de `git status` para garantir apenas mudancas esperadas.

## Primeiro Diagnostico (Snapshot)
- Ha artefatos locais esperados para ignore (ex.: `.nix-postgres/`).
- A raiz contem arquivos de documentacao e utilitarios candidatos a consolidacao.
- Existe possivel redundancia estrutural entre `utils.py` e pacote `utils/`, que deve ser tratada apenas apos confirmacao de uso.
