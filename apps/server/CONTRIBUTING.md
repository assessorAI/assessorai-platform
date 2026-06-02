# Contribuindo com o AssessorAI Server

Obrigado pelo interesse em contribuir.

Este componente faz parte de um monorepo publico historico da plataforma AssessorAI, criada pela [Legisla Brasil](https://legislabrasil.org/). Contribuicoes sao avaliadas em regime de melhor esforco, sem SLA.

## Escopo De Contribuicao

Contribuicoes mais adequadas para este repositorio:

- melhorias de documentacao;
- correcao de instrucoes de instalacao e testes;
- ajustes de seguranca;
- remocao de referencias internas residuais;
- manutencao comunitaria que preserve compatibilidade sempre que possivel.

Mudancas funcionais amplas devem explicar claramente motivacao, impacto e forma de validacao.

## Fluxo De Branches

- `main`: referencia publica historica;
- `dev`, `staging` e `production`: branches legadas do ciclo de desenvolvimento original, quando existirem.

Para documentacao, seguranca e manutencao pontual, abra pull requests contra `main`, salvo orientacao diferente dos mantenedores.

## Como Abrir Uma Pull Request

1. Crie uma branch com nome descritivo.
2. Faca mudancas pequenas e focadas.
3. Rode `pytest -q` quando alterar codigo Python.
4. Atualize documentacao relevante.
5. Abra a pull request explicando o motivo da mudanca e a validacao realizada.

## Padroes

- Python: PEP 8, `snake_case`, tipagem em funcoes publicas quando aplicavel.
- Commits: prefira Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`).
- Nao inclua segredos, dados pessoais reais, arquivos `.env`, bancos locais ou credenciais.

## Creditos

Criado pela [Legisla Brasil](https://legislabrasil.org/).

Desenvolvimento:

- Pedro Markun, maintainer: <https://github.com/pmarkun>
- Carolina Borges
- Nicole Oliveira: <https://github.com/nicoleoliveira>
