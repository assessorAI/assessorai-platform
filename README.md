# AssessorAI Platform

Monorepo publico historico da plataforma AssessorAI, criada pela [Legisla Brasil](https://legislabrasil.org/) para apoiar equipes parlamentares e instituicoes em rotinas legislativas, atendimento de demandas, pesquisa normativa e producao documental assistida por inteligencia artificial.

Este repositorio consolida os principais componentes tecnicos do projeto em uma unica base aberta para consulta, estudo, reuso e manutencao comunitaria em regime de melhor esforco.

## Visao Geral

O AssessorAI foi concebido como uma infraestrutura digital para organizar fluxos de trabalho legislativo e institucional. A plataforma combina:

- interface web para operacao cotidiana de equipes;
- API principal para autenticacao, regras de negocio, documentos, arquivos, demandas e recursos assistidos por IA;
- coleta automatizada de dados legislativos publicos;
- pagina estatica de apresentacao publica via GitHub Pages.

O codigo e publicado como registro historico do desenvolvimento e como base aberta para quem quiser estudar, adaptar ou manter novas evolucoes nos termos da licenca.

## Estrutura

```text
assessorai-platform/
├── apps/
│   ├── client/   # frontend web em Next.js
│   ├── crawler/  # coleta legislativa com Scrapy/Scrapyd
│   └── server/   # backend FastAPI e console Streamlit
├── docs/         # site estatico para GitHub Pages
└── .github/      # automacoes do repositorio
```

## Status Publico

| Componente | Status | Observacoes |
|---|---|---|
| `apps/server` | Publico historico sanitizado | Sem `.env` real, credenciais locais ou bancos locais versionados |
| `apps/client` | Publico historico sanitizado | Configurado para partir de `.env.example` |
| `apps/crawler` | Publico historico sanitizado | Sem massa operacional de dados, downloads ou logs versionados |
| `docs/` | Publico | Site estatico de apresentacao do projeto |

Este repositorio nao promete SLA, suporte operacional ou continuidade de roadmap. Issues e pull requests podem ser avaliados em melhor esforco, especialmente para documentacao, seguranca, reproducibilidade e manutencao comunitaria.

Notas complementares da preparacao para publicacao estao em `docs/publication-notes.md`.

## O Que Nao Esta Incluido

- credenciais reais e arquivos `.env`;
- arquivos locais de credenciais, como `google-key.json`;
- bancos locais, caches de desenvolvimento e artefatos de build;
- dados operacionais gerados pelo crawler, incluindo downloads, logs, bases locais e outputs persistidos;
- garantia de ambiente hospedado ou demo funcional publica.

## Componentes

### `apps/server`

Backend da plataforma. Baseado em FastAPI, concentra autenticacao, regras de negocio, geracao de documentos, fluxos assistidos por IA, arquivos, demandas, auditoria, analytics e console administrativo em Streamlit.

Tecnologias principais:

- Python 3.12
- FastAPI
- SQLAlchemy
- Streamlit
- pytest

Veja: `apps/server/README.md`

### `apps/client`

Frontend web da plataforma. Baseado em Next.js, funciona como interface principal de uso e tambem como BFF para consumo autenticado da API.

Tecnologias principais:

- Next.js 15
- React 19
- Tailwind CSS
- Auth.js / NextAuth
- Jest

Veja: `apps/client/README.md`

### `apps/crawler`

Servico de coleta automatizada de proposicoes, metadados e arquivos legislativos publicos. Baseado em Scrapy, com operacao local via Scrapyd, ScrapydWeb e Docker Compose.

Tecnologias principais:

- Python
- Scrapy
- Scrapyd
- Docker Compose

Veja: `apps/crawler/README.md`

## Como Executar Localmente

Cada aplicacao preserva seu proprio ciclo de instalacao, execucao e testes.

Backend:

```bash
cd apps/server
pip install -e ".[test]"
cp .env-sample .env
DEBUG=True python3 app.py
```

Frontend:

```bash
cd apps/client
npm install
cp .env.example .env.local
npm run dev
```

Crawler:

```bash
cd apps/crawler
cp .env.example .env
mkdir -p storage/{logs,items,dbs,downloads}
docker compose up -d
```

Consulte o README de cada app para variaveis de ambiente, integracoes opcionais e comandos de validacao.

## GitHub Pages

A apresentacao publica do projeto esta em `docs/`. O workflow `.github/workflows/deploy-gh-pages.yml` publica esse conteudo automaticamente no GitHub Pages quando a origem estiver configurada em `Settings > Pages > GitHub Actions`.

## Licenca

Este monorepo e distribuido sob a licenca `GNU Affero General Public License v3.0`.

- O texto completo esta em `LICENSE`.
- A licenca se aplica ao monorepo como um todo, incluindo `apps/server`, `apps/client` e `apps/crawler`.
- Aplicacoes derivadas, modificacoes e disponibilizacoes em rede devem observar os termos da AGPL v3.0.

## Creditos

Criado pela [Legisla Brasil](https://legislabrasil.org/).

Desenvolvimento:

- Pedro Markun, maintainer: <https://github.com/pmarkun>
- Carolina Borges
- Nicole Oliveira: <https://github.com/nicoleoliveira>
