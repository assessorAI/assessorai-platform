# AssessorAI Server

Backend da plataforma AssessorAI para operacao legislativa assistida por IA. Este app concentra autenticacao, regras de negocio, geracao de documentos, busca vetorial, processamento de arquivos e endpoints administrativos usados pelo frontend web e pelo console Streamlit.

## Arquitetura

O `apps/server` e a camada central de servicos da plataforma.

- expõe a API principal em FastAPI
- organiza persistencia de dados com SQLAlchemy
- integra servicos externos de armazenamento, email e embeddings
- oferece fluxos administrativos e operacionais para mandatos e usuarios
- suporta um console administrativo em Streamlit para uso interno

### Componentes principais

- `main.py`: inicializacao da API e middlewares
- `routers/`: endpoints por dominio funcional
- `db/`: sessao, modelos e migrations SQL
- `services/`: integracoes e regras de negocio compartilhadas
- `tests/`: suite automatizada com `pytest`
- `client/`: console administrativo em Streamlit

### Integracoes externas

- OpenAI para embeddings e fluxos assistidos por IA
- Google Cloud Storage para arquivos
- SendGrid para emails transacionais
- PostgreSQL ou SQLite para persistencia

## Pre-requisitos

- Python 3.12
- `pip`
- Docker, para a suite de testes com PostgreSQL
- acesso aos servicos externos que deseja habilitar localmente

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

Se tambem quiser usar o console administrativo Streamlit:

```bash
pip install -e ".[client,test]"
```

## Configuracao de APIs e servicos

Este app pode operar com diferentes niveis de integracao externa. Para desenvolvimento basico, parte da suite usa mocks ou degradacao controlada.

### Banco de dados

- `DATABASE_URL`: obrigatoria para definir o banco principal
- `SQL_ECHO`: opcional para logar queries SQL

Exemplos:

```env
DATABASE_URL=sqlite:///./assessorai.db
DATABASE_URL=postgresql://user:password@localhost:5432/assessorai
```

### OpenAI e embeddings

- `OPENAI_API_KEY`: obrigatoria para features reais de embeddings
- `OPENAI_API_BASE`: opcional
- configuracoes avancadas de embedding podem permanecer nos defaults

### Google Cloud Storage

- `GOOGLE_APPLICATION_CREDENTIALS` ou `GOOGLE_APPLICATION_BASE64`
- `GCS_BUCKET_NAME`

Essas variaveis sao necessarias para upload e leitura de arquivos em GCS.

### Email transacional

- `SENDGRID_API_KEY`
- `SENDGRID_SENDER_EMAIL`
- `SENDGRID_SENDER_NAME`

Essas variaveis sao usadas para reset de senha e notificacoes por email.

### Aplicacao

- `FRONTEND_URL`: URL usada em links e redirects
- `CORS_ORIGINS`: origens liberadas para o frontend e o console admin
- `DEBUG`: ativa logs mais detalhados

## Configuracao do Ambiente Local

Use `.env-sample` como base:

```bash
cp .env-sample .env
```

Configuracao minima recomendada para desenvolvimento local:

```env
DATABASE_URL=sqlite:///./assessorai.db
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000,http://localhost:8501,http://localhost:8000
DEBUG=False
```

Para habilitar recursos de arquivos, email e embeddings, preencha tambem as variaveis dos servicos externos.

Observacoes:

- nao versione `.env`
- nao versione arquivos locais como `google-key.json`
- a publicacao do monorepo parte sempre de arquivos de exemplo

## Exemplo de Uso

### Subir a API localmente

```bash
cd apps/server
DEBUG=True python3 app.py
```

Com a API no ar, acesse localmente em `http://localhost:8000`.

### Rodar o console administrativo

```bash
streamlit run client/app.py
```

### Fluxo basico

1. iniciar a API
2. configurar o frontend para apontar para essa instancia
3. usar os endpoints de autenticacao, mandatos, documentos e producao legislativa

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

- a suite usa PostgreSQL via Docker durante os testes
- servicos externos nao configurados geram warnings esperados
- sem credenciais reais, alguns fluxos de GCS, email ou embeddings operam com mocks, falhas controladas ou escopo reduzido
- para detalhes adicionais da suite, consulte `tests/README.md`

## Licenca

Este app esta coberto pela licenca `GNU Affero General Public License v3.0` adotada no monorepo. Consulte `../../LICENSE`.
