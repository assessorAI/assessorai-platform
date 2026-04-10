# Assessoraí

Assessoraí é uma API FastAPI com console administrativo em Streamlit para apoio a
processos legislativos, geração de documentos e fluxos de análise assistidos por IA.

## Status do Projeto

Este repositório está em modo de descontinuação (sunset).

- `main`: referência pública estável (prioridade de documentação)
- `dev`: evolução e mudanças novas que ainda não foram promovidas para a referência
- `staging` e `production`: branches legadas do fluxo interno

Para contexto de branches, novidades de dev e operacao, consulte
`docs/project.md` e `docs/operations.md`.

## Sumário

- [Status do Projeto](#status-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Fluxo de Branches](#fluxo-de-branches)
- [Configuração do Google Cloud](#configuração-do-google-cloud)
  - [1. Criar um Projeto no Google Cloud](#1-criar-um-projeto-no-google-cloud)
  - [2. Habilitar as APIs Necessárias](#2-habilitar-as-apis-necessárias)
  - [3. Criar um Bucket no Google Cloud Storage](#3-criar-um-bucket-no-google-cloud-storage)
  - [4. Gerar Credenciais JSON com Conta de Serviço](#4-gerar-credenciais-json-com-conta-de-serviço)
- [Configuração do Ambiente Local](#configuração-do-ambiente-local)
- [Exemplo de Uso](#exemplo-de-uso)
 - [Testes](#testes)

## Pré-requisitos

- Conta no [Google Cloud](https://cloud.google.com/)
- Python 3.12
- [Git](https://git-scm.com/)

## Instalação

1. **Entre no diretório do app dentro do monorepo:**

   ```bash
   cd apps/server
   ```

2. **Instale as dependências:**

    ```bash
    pip install -e .
    ```

3. **Crie o arquivo de ambiente a partir do exemplo:**

   ```bash
   cp .env-sample .env
   ```

## Fluxo de Branches

Este projeto mantém quatro trilhas:

- `main`: branch pública de referência.
- `dev`: desenvolvimento contínuo.
- `staging`: validação antes de produção.
- `production`: linha histórica de deploy.

Quando necessário publicar estado estável para a comunidade, promovemos mudanças de
`production` para `main` e atualizamos a documentação em `main`.

## Configuração do Google Cloud

### 1. Criar um Projeto no Google Cloud

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2. No menu superior, clique no seletor de projetos e escolha **"Novo Projeto"**.
3. Preencha os dados necessários (nome, organização, etc.) e clique em **"Criar"**.

### 2. Habilitar as APIs Necessárias

#### 2.1 Habilitar a Vertex AI API

1. No menu lateral, acesse **"APIs e Serviços"** > **"Biblioteca"**.
2. Pesquise por **"Vertex AI"**.
3. Selecione a API e clique em **"Ativar"**.

#### 2.2 Habilitar a Google Cloud Storage API

1. Ainda em **"APIs e Serviços"** > **"Biblioteca"**, pesquise por **"Google Cloud Storage"**.
2. Selecione a API e clique em **"Ativar"**.

### 3. Criar um Bucket no Google Cloud Storage

1. No Console do Google Cloud, vá em **"Storage"** > **"Navegador"**.
2. Clique em **"Criar Bucket"**.
3. Configure:
   - **Nome:** Escolha um nome único globalmente.
   - **Localização:** Selecione a região ou multi-região desejada.
   - **Classe de Armazenamento e Controle de Acesso:** Configure conforme sua necessidade.
4. Clique em **"Criar"**.

> **Dica:** Certifique-se de que o nome do bucket siga as regras de nomenclatura do Google Cloud Storage.

### 4. Gerar Credenciais JSON com Conta de Serviço

#### 4.1 Criar uma Conta de Serviço

1. No Console, acesse **"IAM e Administração"** > **"Contas de Serviço"**.
2. Clique em **"Criar Conta de Serviço"**.
3. Preencha os campos:
   - **Nome da Conta de Serviço:** Exemplo, `python-project-account`.
   - **ID da Conta de Serviço:** Gerado automaticamente ou personalizado.
4. Clique em **"Criar"**.

#### 4.2 Conceder Permissões à Conta de Serviço

1. Durante a criação, adicione as funções necessárias, como:
   - **Editor** (para testes; em produção, prefira conceder o mínimo necessário).
   - **Vertex AI User**
   - **Storage Admin**
2. Clique em **"Continuar"** e finalize a criação.

#### 4.3 Gerar a Chave JSON

1. Selecione a conta de serviço criada e vá para a aba **"Chaves"**.
2. Clique em **"Adicionar Chave"** > **"Criar nova chave"**.
3. Escolha o formato **JSON** e clique em **"Criar"**.
4. O arquivo JSON será baixado automaticamente.

> **Importante:** Mantenha esse arquivo em local seguro, pois ele contém credenciais para acessar os recursos do seu projeto.

## Configuração do Ambiente Local

Como o projeto já existe, basta configurar as variáveis de ambiente através de um arquivo `.env` na raiz do projeto. Use `.env-sample` como ponto de partida e ajuste os valores conforme necessário:

```env
# Caminho para o arquivo de credenciais JSON gerado
GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/seu/arquivo.json

# Nome do bucket do Google Cloud Storage criado
GCS_BUCKET_NAME=nome-do-seu-bucket

# Credenciais do SendGrid
SENDGRID_API_KEY=chave-da-sua-conta-sendgrid
SENDGRID_SENDER_EMAIL=contato@seu-dominio.com
# Opcional: nome exibido e diretório customizado para templates markdown
SENDGRID_SENDER_NAME=AssessorAI
# EMAIL_TEMPLATE_DIR=/caminho/customizado/para/templates

Variáveis do banco de dados:
- DATABASE_URL (ex: `sqlite:///./assessorai.db` ou `postgresql+psycopg://user:pass@host/db`)
- SQL_ECHO (`True` para logar SQL)

# Configuração de embeddings (OpenAI)
OPENAI_API_KEY=chave-da-openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
# OPENAI_API_BASE=https://api.openai.com/v1  # opcional
# EMBEDDING_BATCH_SIZE=100  # lote enviado à API de embeddings OpenAI
# VECTOR_BATCH_SIZE=200  # lote unificado para importação vetorial e bulk inserts PostgreSQL
```

> **Observação:**  
> - **Linux/macOS:** Utilize o caminho padrão, como `/home/usuario/caminho/para/arquivo.json`.  
> - **Windows:** Utilize o caminho no formato, por exemplo, `C:\caminho\para\arquivo.json`.

Para carregar essas variáveis automaticamente no seu projeto Python, você pode usar bibliotecas como [python-dotenv](https://pypi.org/project/python-dotenv/).

## Exemplo de Uso

Um exemplo simples para verificar se a variável de ambiente está configurada corretamente:

```python
import os

# Verifica o caminho do arquivo de credenciais
print("Credenciais:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

# Verifica o nome do bucket
print("Bucket:", os.getenv("GCS_BUCKET_NAME"))
```

Este exemplo imprime os valores configurados no arquivo `.env`, garantindo que seu ambiente esteja corretamente configurado para interagir com o Google Cloud.

---

Para mais detalhes sobre a configuração dos serviços do Google Cloud, consulte a [documentação oficial](https://cloud.google.com/docs).

## Testes

Este projeto usa `pytest` com uma suíte completa de testes automatizados em `tests/`.

### Execução Rápida

```bash
pip install -e .
pytest -q
```

Os testes utilizam um banco **PostgreSQL em Docker** (criado automaticamente na porta 5433) e rodam com serviços mockados por padrão. **Não é necessário configurar serviços externos** (OpenAI, GCS, SendGrid) para rodar os testes básicos.

## Status de publicação

Esta copia dentro do monorepo foi preparada para publicacao sem arquivos locais sensiveis:

- nenhum `.env` real deve ser versionado
- arquivos como `google-key.json` devem permanecer fora do repositório
- o fluxo de CI instala dependencias a partir de `pyproject.toml`

### Avisos de Configuração

Ao rodar os testes, você verá warnings informativos sobre serviços externos não configurados:

```
OPENAI_API_KEY not set - AI features will use mock embeddings
GCS_BUCKET_NAME not set - File storage tests will fail
...
```

Isso é **normal e esperado**. Os testes rodarão com mocks onde possível. Para testes de integração completos com serviços reais, veja `tests/README.md`.

### Comandos Úteis

```bash
# Todos os testes (modo silencioso)
pytest -q

# Ver detalhes e warnings
pytest -v

# Teste específico
pytest tests/test_auth_flow.py::test_user_registration -v

# Com coverage (relatório terminal + HTML)
pytest --cov=. --cov-report=term-missing --cov-report=html

# Coverage apenas no terminal
pytest --cov=. --cov-report=term-missing

# Ver relatório HTML (após gerar)
# Abra htmlcov/index.html no navegador
```

### Documentação Completa

Para detalhes sobre:
- Configuração de serviços externos (OpenAI, GCS, SendGrid)
- Estrutura dos testes e fixtures disponíveis
- Troubleshooting de erros comuns
- Como escrever novos testes

Consulte **[tests/README.md](tests/README.md)**.
