# Contribuindo com o Assessoraí

Obrigado pelo interesse em contribuir.

## Estado do projeto

Este projeto esta em modo de descontinuacao. Aceitamos contribuicoes em regime
de melhor esforco, sem SLA.

## Fluxo de branches

- `main`: referencia publica estavel
- `dev`: mudancas novas
- `staging`: validacao interna
- `production`: linha historica de deploy

Se a contribuicao for de documentacao ou higiene open source, abra PR para
`main`. Se for feature/ajuste funcional novo, abra PR para `dev`.

## Como abrir uma PR

1. Crie branch a partir da branch alvo (`main` ou `dev`).
2. Faça mudancas pequenas e focadas.
3. Rode `pytest -q` quando alterar codigo Python.
4. Atualize documentacao relevante.
5. Abra PR explicando o motivo da mudanca.

## Padroes

- Python: PEP 8, `snake_case`, tipagem em funcoes publicas.
- Commits: prefira Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`).
- Nao inclua segredos, dados pessoais reais, nem arquivos `.env`.
