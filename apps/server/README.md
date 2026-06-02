# AssessorAI Server

Backend historico da plataforma AssessorAI, criada pela [Legisla Brasil](https://legislabrasil.org/). Este app concentra autenticacao, regras de negocio, geracao de documentos, busca vetorial, processamento de arquivos, demandas, auditoria, analytics e endpoints administrativos usados pelo frontend web e pelo console Streamlit.

## Arquitetura

O `apps/server` e a camada central de servicos da plataforma.

- expoe a API principal em FastAPI;
- organiza persistencia de dados com SQLAlchemy;
- integra servicos externos de armazenamento, email e embeddings;
- oferece fluxos administrativos e operacionais para mandatos e usuarios;
- inclui um console administrativo em Streamlit para operacao interna ou local.

### Componentes principais

- `main.py`: inicializacao da API e middlewares;
- `routers/`: endpoints por dominio funcional;
- `db/`: sessao, modelos e migrations SQL;
- `services/`: integracoes e regras de negocio compartilhadas;
- `tests/`: suite automatizada com `pytest`;
- `client/`: console administrativo em Streamlit.

### Integracoes externas

- OpenAI para embeddings e fluxos assistidos por IA;
- Google Cloud Storage para arquivos;
- SendGrid para emails transacionais;
- PostgreSQL ou SQLite para persistencia.

## Pre-requisitos

- Python 3.12;
- `pip`;
- Docker, para a suite de testes com PostgreSQL;
- acesso aos servicos externos que deseja habilitar localmente.

Em NixOS, entre primeiro no ambiente do projeto:

```bash
nix develop
```

## Instalacao

```bash
cd apps/server
pip install -e ".[test]"
cp .env-sample .env
```

Para usar tambem o console administrativo Streamlit:

```bash
pip install -e ".[client,test]"
```

## Configuracao Local

Use `.env-sample` como base. O arquivo `.env` local nao deve ser versionado.

Configuracao minima para desenvolvimento local:

```env
DATABASE_URL=sqlite:///./assessorai.db
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000,http://localhost:8501,http://localhost:8000
DEBUG=False
```

### Banco de dados

- `DATABASE_URL`: obrigatoria para definir o banco principal;
- `SQL_ECHO`: opcional para logar queries SQL.

Exemplos:

```env
DATABASE_URL=sqlite:///./assessorai.db
DATABASE_URL=postgresql://user:password@localhost:5432/assessorai
```

### OpenAI e embeddings

- `OPENAI_API_KEY`: necessaria para features reais de embeddings;
- `OPENAI_API_BASE`: opcional.

Sem credenciais reais, alguns fluxos operam com mocks, falhas controladas ou escopo reduzido.

### Google Cloud Storage

- `GOOGLE_APPLICATION_CREDENTIALS` ou `GOOGLE_APPLICATION_BASE64`;
- `GCS_BUCKET_NAME`.

Essas variaveis sao necessarias para upload e leitura de arquivos em GCS.

### Email transacional

- `SENDGRID_API_KEY`;
- `SENDGRID_SENDER_EMAIL`;
- `SENDGRID_SENDER_NAME`.

Essas variaveis sao usadas para reset de senha e notificacoes por email.

### Aplicacao

- `FRONTEND_URL`: URL usada em links e redirects;
- `CORS_ORIGINS`: origens liberadas para o frontend e o console admin;
- `DEBUG`: ativa logs mais detalhados.

## Execucao

Subir a API localmente:

```bash
cd apps/server
DEBUG=True python3 app.py
```

Com a API no ar, acesse `http://localhost:8000`.

Rodar o console administrativo:

```bash
streamlit run client/app.py
```

Fluxo basico:

1. iniciar a API;
2. configurar o frontend para apontar para essa instancia;
3. usar os endpoints de autenticacao, mandatos, documentos e producao legislativa.

## Testes

Comando principal:

```bash
pytest -q
```

Comandos uteis:

```bash
pytest -v
pytest tests/test_auth_flow.py::test_user_registration -v
pytest --cov=. --cov-report=term-missing
pytest --cov=. --cov-report=term-missing --cov-report=html
```

Observacoes:

- a suite usa PostgreSQL via Docker durante parte dos testes;
- servicos externos nao configurados podem gerar warnings esperados;
- para detalhes adicionais da suite, consulte `tests/README.md`.

## Publicacao E Dados Locais

Este app foi publicado como parte de um monorepo historico sanitizado. O repositorio nao inclui:

- arquivos `.env` reais;
- credenciais locais como `google-key.json`;
- bancos SQLite locais;
- dados privados ou operacionais;
- caches e relatorios de cobertura gerados localmente.

## Licenca

Este app esta coberto pela licenca `GNU Affero General Public License v3.0` adotada no monorepo. Consulte `../../LICENSE`.

## Creditos

Criado pela [Legisla Brasil](https://legislabrasil.org/).

Desenvolvimento:

- Pedro Markun, maintainer: <https://github.com/pmarkun>
- Carolina Borges
- Nicole Oliveira: <https://github.com/nicoleoliveira>
