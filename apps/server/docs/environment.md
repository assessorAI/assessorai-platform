# Environment Variables Reference

Referência completa de todas as variáveis de ambiente utilizadas no AssessorAI.

---

## 📋 Índice

- [Variáveis Críticas (Obrigatórias)](#variáveis-críticas-obrigatórias)
- [Variáveis de Configuração](#variáveis-de-configuração)
- [Variáveis Opcionais / Performance](#variáveis-opcionais--performance)
- [Variáveis de Deploy](#variáveis-de-deploy)
- [Variáveis do Cliente Streamlit](#variáveis-do-cliente-streamlit)
- [Variáveis Internas / Debug](#variáveis-internas--debug)

---

## Variáveis Críticas (Obrigatórias)

### `OPENAI_API_KEY`
- **Obrigatória para:** Embeddings e chamadas LLM
- **Tipo:** String (chave de API)
- **Exemplo:** `sk-proj-...`
- **Usado em:** `services/embeddings/factory.py`, `tests/conftest.py`
- **Nota:** Sem esta chave, a aplicação não consegue gerar embeddings ou usar modelos OpenAI

### `DATABASE_URL`
- **Obrigatória para:** Conexão com banco de dados
- **Tipo:** String (connection string)
- **Default:** `sqlite:///./assessorai.db`
- **Exemplo PostgreSQL:** `postgresql://user:password@localhost:5432/assessorai`
- **Usado em:** `db/session.py`
- **Nota:** SQLite para dev local, PostgreSQL recomendado para produção

### `SENDGRID_API_KEY`
- **Obrigatória para:** Envio de emails (registro, reset de senha, etc.)
- **Tipo:** String (chave de API)
- **Exemplo:** `SG.xxx...`
- **Usado em:** `services/sendgrid_service.py`

### `SENDGRID_SENDER_EMAIL`
- **Obrigatória para:** Email do remetente
- **Tipo:** String (email)
- **Exemplo:** `noreply@assessorai.com`
- **Usado em:** `services/sendgrid_service.py`

### `GOOGLE_APPLICATION_CREDENTIALS`
- **Obrigatória para:** Acesso ao Google Cloud Storage
- **Tipo:** String (path para arquivo JSON)
- **Exemplo:** `/path/to/google-key.json`
- **Usado em:** `utils/google_creds.py`, `services/admin_dashboard.py`
- **Alternativa:** Use `GOOGLE_APPLICATION_BASE64` em containers

### `GOOGLE_APPLICATION_BASE64`
- **Alternativa a:** `GOOGLE_APPLICATION_CREDENTIALS`
- **Tipo:** String (base64 do JSON de credenciais)
- **Exemplo:** `ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsC...`
- **Usado em:** `utils/google_creds.py`, `services/admin_dashboard.py`
- **Nota:** Útil em ambientes containerizados (Railway, Fly.io) onde não há sistema de arquivos persistente

### `GCS_BUCKET_NAME`
- **Obrigatória para:** Upload de arquivos para GCS
- **Tipo:** String (nome do bucket)
- **Exemplo:** `assessorai-uploads-prod`
- **Usado em:** `routers/upload.py`, `tests/conftest.py`

---

## Variáveis de Configuração

### `FRONTEND_URL`
- **Tipo:** String (URL)
- **Default:** `http://localhost:8000`
- **Exemplo:** `https://app.assessorai.com`
- **Usado em:** `utils/config.py`
- **Nota:** URL base do frontend, usado em links de emails e redirects

### `DEBUG`
- **Tipo:** Boolean (`True`/`False`)
- **Default:** `False`
- **Usado em:** `main.py`, `app.py`
- **Nota:** Ativa logs detalhados e stack traces completos

### `SQL_ECHO`
- **Tipo:** Boolean (`True`/`False`)
- **Default:** `False`
- **Usado em:** `db/session.py`
- **Nota:** Quando `True`, imprime todas as queries SQL no console

### `SENDGRID_SENDER_NAME`
- **Tipo:** String
- **Default:** `AssessorAI`
- **Usado em:** `services/sendgrid_service.py`
- **Nota:** Nome do remetente exibido nos emails

### `ACCESS_TOKEN_EXPIRE_MINUTES`
- **Tipo:** Integer (minutos)
- **Default:** `30`
- **Usado em:** `utils/security.py`, `tests/conftest.py`
- **Nota:** Tempo de expiração dos tokens JWT de autenticação

---

## Variáveis Opcionais / Performance

### `EMBEDDING_PROVIDER`
- **Tipo:** String (`openai`, etc.)
- **Default:** `openai`
- **Usado em:** `services/embeddings/factory.py`, `routers/vector_admin.py`
- **Nota:** Provider de embeddings (atualmente apenas OpenAI é suportado)

### `EMBEDDING_MODEL`
- **Tipo:** String (nome do modelo)
- **Default:** `text-embedding-3-small`
- **Exemplo:** `text-embedding-3-large`, `text-embedding-ada-002`
- **Usado em:** `services/embeddings/factory.py`, `routers/vector_admin.py`
- **Nota:** Modelo OpenAI a ser usado para gerar embeddings

### `OPENAI_EMBEDDING_MODEL`
- **Tipo:** String (alias de `EMBEDDING_MODEL`)
- **Usado em:** `services/embeddings/factory.py`
- **Nota:** Alias específico do OpenAI, `EMBEDDING_MODEL` tem precedência

### `EMBEDDING_DIMENSION`
- **Tipo:** Integer (dimensões do vetor)
- **Default:** `1536`
- **Usado em:** `db/models.py`
- **Nota:** Dimensão dos vetores de embedding (1536 para ada-002, 1536 para 3-small, 3072 para 3-large)

### `EMBEDDING_DIM`
- **Tipo:** Integer (alias de `EMBEDDING_DIMENSION`)
- **Usado em:** `services/embeddings/factory.py`

### `OPENAI_API_BASE`
- **Tipo:** String (URL)
- **Default:** `https://api.openai.com/v1`
- **Usado em:** `services/embeddings/factory.py`
- **Nota:** URL base da API OpenAI (útil para proxies ou endpoints alternativos)

### `OPENAI_TIMEOUT`
- **Tipo:** Integer (segundos)
- **Default:** Gerenciado pelo cliente OpenAI
- **Usado em:** `services/embeddings/factory.py`
- **Nota:** Timeout para requisições à API OpenAI

### `EMBEDDING_BATCH_SIZE`
- **Tipo:** Integer (quantidade de documentos)
- **Default:** `100`
- **Usado em:** `services/vector_ingestion.py`
- **Nota:** Número de documentos processados por lote nas chamadas à API OpenAI para geração de embeddings

### `VECTOR_SEARCH_PROBES`
- **Tipo:** Integer
- **Default:** Auto-calculado baseado no tamanho do dataset
- **Usado em:** `services/vector_store.py`
- **Nota:** Número de probes para busca vetorial IVFFlat (mais probes = mais preciso, mais lento)

### `MAX_EMBEDDING_FILE_SIZE`
- **Tipo:** Integer (bytes)
- **Default:** `10000000` (10MB)
- **Usado em:** `services/file_processing.py`
- **Nota:** Tamanho máximo de arquivo aceito para processamento de embeddings

### `EMAIL_TEMPLATE_DIR`
- **Tipo:** String (path)
- **Default:** `services/templates/emails/`
- **Usado em:** `services/sendgrid_service.py`
- **Nota:** Diretório dos templates de email Markdown

### `MANDATO_CARGOS_FILE`
- **Tipo:** String (path)
- **Default:** `config/mandato_cargos.json`
- **Usado em:** `utils/config.py`
- **Nota:** Arquivo JSON com configuração de cargos de mandatos

---

## Variáveis de Deploy

### `DB_REFRESH_MODE`
- **Tipo:** String (`incremental`, `rebuild`, `full`, `wipe`)
- **Default:** `incremental`
- **Usado em:** `scripts/manage_db.py`
- **Descrição:**
  - `incremental`: Aplica apenas migrations pendentes (seguro para produção)
  - `rebuild` / `full` / `wipe`: Remove todas as tabelas e recria do zero (⚠️ destrói dados!)
- **Nota:** Executado automaticamente no deploy via `scripts/entrypoint.sh`

### `DB_REFRESH_LOG_LEVEL`
- **Tipo:** String (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- **Default:** `INFO`
- **Usado em:** `scripts/manage_db.py`
- **Nota:** Nível de logging do script de migrations

### Database avançado (PostgreSQL)
Estas variáveis são usadas apenas quando `DATABASE_URL` não está definida ou precisa ser construída dinamicamente:

- `DATABASE_USER` (default: `postgres`)
- `DATABASE_PASSWORD` (default: `postgres`)
- `DATABASE_HOSTNAME` (default: `localhost`)
- `DATABASE_PORT` (default: `5432`)
- `DATABASE_NAME` (default: `assessorai`)

**Usado em:** `db/session.py`

---

## Variáveis do Cliente Streamlit

Estas variáveis são usadas apenas no console admin Streamlit (`client/`):

### `ASSESSORAI_API_URL`
- **Tipo:** String (URL)
- **Default:** `http://localhost:8000`
- **Exemplo:** `https://api.assessorai.com`
- **Usado em:** `client/admin/api.py`
- **Nota:** URL da API backend que o Streamlit deve consumir

### `CHUNK_TOKEN_MODEL`
- **Tipo:** String (nome do modelo)
- **Default:** `text-embedding-ada-002`
- **Usado em:** `client/pages/10_📥_Admin_Importador_Vetorial.py`
- **Nota:** Modelo usado para calcular chunks de tokens na importação vetorial

### `VECTOR_BATCH_SIZE`
- **Tipo:** Integer (quantidade de documentos)
- **Default:** `200`
- **Usado em:** `client/pages/10_📥_Admin_Importador_Vetorial.py`, `services/vector_store.py`
- **Nota:** Número de documentos processados por chunk nas requisições HTTP da interface Streamlit e nos bulk inserts PostgreSQL. Valor de 200 mantém cada query SQL em ~1.2MB, prevenindo erros de "out of memory" no PostgreSQL com datasets grandes (200 docs × 6KB embeddings = ~1.2MB por chunk)

---

## Variáveis Internas / Debug

### `PYTEST_CURRENT_TEST`
- **Tipo:** String (auto-gerenciada pelo pytest)
- **Usado em:** `main.py`
- **Nota:** Variável interna do pytest, não deve ser configurada manualmente. Usada para detectar se a aplicação está rodando em ambiente de testes.

---

## 🚀 Quick Start

### Desenvolvimento Local Mínimo

Crie um arquivo `.env` com:

```bash
OPENAI_API_KEY=sk-proj-...
DATABASE_URL=sqlite:///./assessorai.db
GOOGLE_APPLICATION_CREDENTIALS=/path/to/google-key.json
GCS_BUCKET_NAME=seu-bucket-dev
SENDGRID_API_KEY=SG.xxx...
SENDGRID_SENDER_EMAIL=dev@example.com
FRONTEND_URL=http://localhost:8000
```

### Deploy Produção (Railway/Fly.io)

Variáveis essenciais no painel de configuração:

```bash
OPENAI_API_KEY=sk-proj-...
DATABASE_URL=postgresql://user:pass@host:5432/db
GOOGLE_APPLICATION_BASE64=ewogICJ0eXBlI...  # Base64 do JSON
GCS_BUCKET_NAME=assessorai-prod
SENDGRID_API_KEY=SG.xxx...
SENDGRID_SENDER_EMAIL=noreply@assessorai.com
FRONTEND_URL=https://app.assessorai.com
DB_REFRESH_MODE=incremental
DEBUG=False
```

---

## 📚 Referências

- **Migrations:** Ver `GUIDELINES.md` seção "Database Refresh Workflow"
- **Testes:** Ver `tests/conftest.py` para variáveis mockadas automaticamente
- **Setup:** Ver `.env-sample` para template com valores padrão
