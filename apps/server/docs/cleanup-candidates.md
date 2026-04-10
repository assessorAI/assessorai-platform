# Cleanup Conservador - Candidatos

Lista de candidatos identificados na revisao conservadora. Esta fase nao remove codigo automaticamente; apenas registra evidencias e decisao sugerida.

## Candidatos

| Item | Evidencia | Risco | Decisao sugerida |
|---|---|---|---|
| `utils.py` (raiz) | Funcoes `convert2pdf`/`convert2docx` nao sao usadas; uso ativo aponta para `utils/converters.py` | Medio (nome conflita com pacote `utils/`) | Removido no Lote C (2026-02-24), mantendo `utils/converters.py` como fonte unica |
| `scripts/manual/migrate.sh` | Wrapper simples para `python scripts/manage_db.py`; uso manual | Baixo | Movido da raiz para `scripts/manual/` no cleanup |
| `scripts/manual/local-database.sh` | Script utilitario local de Docker/Postgres; uso manual | Baixo | Movido da raiz para `scripts/manual/` no cleanup |
| `scripts/manual/check_email_config.py` | Script de diagnostico manual de email | Baixo | Movido da raiz para `scripts/manual/` no cleanup |
| `scripts/manual/manual_test_prompts.py` | Script de apoio manual para testes de prompts | Baixo | Movido da raiz para `scripts/manual/` no cleanup |

## Regras para remocao futura
- Confirmar ausencia de import/referencia no codigo e na documentacao.
- Validar com `pytest -q` e smoke da API.
- Realizar remocao em commit atomico separado.
