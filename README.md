# AssessorAI Platform

Monorepo que centraliza os principais componentes da plataforma AssessorAI:

- `apps/server`: backend em FastAPI com console administrativo em Streamlit
- `apps/client`: frontend web em Next.js com BFF
- `apps/crawler`: infraestrutura de coleta legislativa com Scrapy/Scrapyd
- `docs/`: apresentação publica estatica para GitHub Pages

## Visao Geral

O AssessorAI e uma plataforma para apoiar equipes parlamentares em fluxos de trabalho legislativos, atendimento de demandas, pesquisa normativa e automacao operacional.

Neste monorepo, as tres bases de codigo ficam organizadas sob uma raiz unica para facilitar:

- documentacao centralizada
- onboarding tecnico
- evolucao coordenada entre frontend, backend e crawler
- publicacao de uma pagina institucional via GitHub Pages

## Estrutura

```text
assessorai-platform/
├── apps/
│   ├── client/
│   ├── crawler/
│   └── server/
├── docs/
│   ├── index.html
│   └── styles.css
└── .github/
    └── workflows/
        └── deploy-gh-pages.yml
```

## Status De Publicacao

| Componente | Status | Observacoes |
|---|---|---|
| `apps/server` | Publico sanitizado | Sem `.env` real ou arquivos locais sensiveis no monorepo |
| `apps/client` | Publico sanitizado | Configurado para partir de `.env.example` |
| `apps/crawler` | Publico sanitizado | Sem massa de dados gerada no monorepo |
| `docs/` | Publico | Site estatico para GitHub Pages |

## O Que Nao Esta Incluido

- credenciais reais e arquivos `.env`
- arquivos locais de credenciais, como `google-key.json`
- bancos locais e caches de desenvolvimento
- dados gerados pelo crawler, incluindo downloads, logs e outputs persistidos

## Componentes

### `apps/server`

API principal da plataforma. Baseada em FastAPI, concentra autenticacao, regras de negocio, geracao de documentos, fluxos assistidos por IA e console administrativo.

Tecnologias observadas:

- Python 3.12
- FastAPI
- SQLAlchemy
- Streamlit
- pytest

Veja tambem: `apps/server/README.md`

### `apps/client`

Frontend web da plataforma. Baseado em Next.js, funciona como interface principal de uso e tambem como BFF para consumo autenticado da API.

Tecnologias observadas:

- Next.js 15
- React 19
- Tailwind CSS
- Auth.js / NextAuth
- Jest

Veja tambem: `apps/client/README.md`

### `apps/crawler`

Servico de coleta automatizada de proposicoes legislativas em diferentes casas legislativas. Baseado em Scrapy, com operacao via Scrapyd, ScrapydWeb e Docker Compose.

Tecnologias observadas:

- Python
- Scrapy
- Scrapyd
- Docker Compose

Veja tambem: `apps/crawler/README.md`

## Como Trabalhar No Monorepo

Hoje este monorepo foi estruturado para consolidacao organizacional e documental. Cada aplicacao ainda preserva seu proprio ciclo de build, execucao e dependencias.

Exemplos:

```bash
# Backend
cd apps/server

# Frontend
cd apps/client

# Crawler
cd apps/crawler
```

## GitHub Pages

A apresentacao publica do projeto esta em `docs/` e o workflow `.github/workflows/deploy-gh-pages.yml` publica esse conteudo automaticamente no GitHub Pages.

Para usar:

1. Publique este diretorio como um repositório no GitHub.
2. Em `Settings > Pages`, mantenha a origem em `GitHub Actions`.
3. Ao fazer push na branch principal, o workflow fara o deploy da pasta `docs/`.

## Proximos Passos Sugeridos

1. Adicionar um `CONTRIBUTING.md` central com padroes do monorepo.
2. Criar uma estrategia comum de ambiente local, por exemplo via `flake.nix` ou `justfile`.
3. Definir convencoes de versao, release e integracao entre os tres projetos.
