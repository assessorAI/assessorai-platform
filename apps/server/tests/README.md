# Guia de Testes - AssessorAI

## Visão Geral

Este projeto utiliza **pytest** para testes automatizados. Os testes cobrem:
- Autenticação e gerenciamento de usuários
- CRUD de mandatos e oficios
- Funcionalidades de Expert PL (análise de projetos de lei)
- Busca vetorial e ingestão de documentos
- Auditoria e administração
- Validações de dados

## Requisitos Mínimos

### Obrigatórios (para rodar qualquer teste)

1. **Python 3.12+** e dependências instaladas:
   ```bash
   pip install -e ".[test]"
   ```

2. **Docker** rodando (para o banco PostgreSQL de testes):
   - A suite cria automaticamente um container `assessorai-test-postgres` na porta `5434`
   - Se você já tem PostgreSQL local na porta 5434, pare-o ou ajuste `conftest.py`

### Opcionais (para testes de integração completos)

Algumas funcionalidades dependem de serviços externos. **Os testes rodam sem essas configurações**, mas usarão mocks/stubs e alguns endpoints podem retornar respostas simplificadas.

#### 1. OpenAI (Embeddings e AI)

**Quando necessário:**
- Testes de Expert PL (`test_expert_pl.py`)
- Testes de busca vetorial (`test_vector_operations.py`)
- Validação de similaridade semântica

**Como configurar:**
```bash
export OPENAI_API_KEY=sk-...
export OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # opcional
```

**Sem configuração:** Os testes usarão embeddings dummy (vetores sequenciais fixos). Expert PL pode retornar respostas básicas.

#### 2. Google Cloud Storage (Armazenamento de Arquivos)

**Quando necessário:**
- Testes de upload de documentos (`test_upload.py`)
- Ingestão vetorial de PDFs (`test_vector_admin.py`)
- Oficios com anexos

**Como configurar:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/service-account.json
export GCS_BUCKET_NAME=nome-do-seu-bucket
```

**Sem configuração:** Uploads retornarão erro `400/422`. Os testes consideram isso aceitável com `assert status_code in (200, 400, 422)`.

#### 3. SendGrid (Notificações por Email)

**Quando necessário:**
- Testes de registro de usuário com envio de email
- Reset de senha
- Notificações administrativas

**Como configurar:**
```bash
export SENDGRID_API_KEY=SG.xxx
export SENDGRID_SENDER_EMAIL=no-reply@seudominio.com
export SENDGRID_SENDER_NAME="AssessorAI"
```

**Sem configuração:** Emails não serão enviados. Testes de fluxo de autenticação continuam funcionando.

## Rodando os Testes

### Todos os testes
```bash
pytest -q
```

### Teste específico
```bash
pytest tests/test_auth_flow.py::test_user_registration -v
```

### Arquivo completo
```bash
pytest tests/test_users.py -v
```

### Com coverage
```bash
pytest --cov=. --cov-report=html
```

### Ver warnings de configuração
```bash
pytest -v
```
Os warnings sobre serviços não configurados aparecerão no início da execução.

## Estrutura dos Testes

```
tests/
├── conftest.py                    # Fixtures compartilhadas e setup do banco
├── test_admin.py                  # Dashboard administrativo
├── test_audit.py                  # Logs de auditoria
├── test_auth_flow.py              # Login, registro, reset de senha
├── test_criar_projeto_referencias.py  # Criação de projetos com referências
├── test_expert_pl.py              # Análise de PL via IA
├── test_mandatos.py               # CRUD de mandatos
├── test_oficios.py                # Geração de oficios
├── test_upload.py                 # Upload de arquivos para GCS
├── test_user_management.py        # Gerenciamento de usuários
├── test_validation.py             # Validações de dados
├── test_vector_admin.py           # Admin de busca vetorial
└── test_vector_operations.py      # Operações de embeddings
```

## Fixtures Principais (conftest.py)

- **`test_db_container`**: Inicia PostgreSQL via Docker e aplica migrações
- **`client`**: Cliente HTTP para testes (FastAPI TestClient)
- **`db_session`**: Sessão de banco limpa (TRUNCATE entre testes)
- **`admin_user`**: Usuário admin pré-criado (email: `admin@example.com`)
- **`manager_token`**: Token JWT de um usuário Manager
- **`auth_headers`**: Headers com Bearer token de admin

## Comportamento dos Testes

### Status Codes Aceitos

Muitos testes aceitam múltiplos status codes devido a dependências externas:

```python
assert response.status_code in (200, 201)  # Sucesso ou criado
assert response.status_code in (200, 400, 422)  # Pode falhar sem GCS/LLM
```

Isso é **intencional** para permitir CI/CD sem configurar todos os serviços externos.

### Limpeza de Dados

A fixture `db_session` faz `TRUNCATE` em todas as tabelas entre testes, garantindo isolamento. O container PostgreSQL persiste entre execuções para velocidade.

### Embeddings Mock

Quando `OPENAI_API_KEY` não está configurada, o `conftest.py` substitui o provider real por `DummyEmbeddingProvider`, que retorna vetores sequenciais fixos `[1.0, 2.0, 3.0, ...]`.

## Troubleshooting

### "Database did not become ready in time"
- Docker não está rodando ou porta 5434 já está em uso
- Solução: `docker ps` para verificar, ou pare o PostgreSQL local

### "404 Client Error: Not Found for url: https://storage.googleapis.com/..."
- GCS não configurado ou bucket não existe
- Esperado: teste aceita `400/422` como válido

### "openai.AuthenticationError: No API key provided"
- `OPENAI_API_KEY` não configurada
- Esperado: testes de Expert PL usarão mock ou retornarão respostas simplificadas

### Testes lentos na primeira execução
- PostgreSQL container está sendo criado e migrado
- Execuções subsequentes reusam o container (muito mais rápido)

### "ImportError: cannot import name 'X' from 'assessorai.Y'"
- Instale as dependências: `pip install -e ".[test]"`
- Se usar `uv`: `uv pip install -e ".[test]"`

## Recomendações para Desenvolvedores

### Escrevendo Novos Testes

1. **Use as fixtures do conftest**: `client`, `db_session`, `admin_user`, `auth_headers`
2. **Aceite múltiplos status codes** para testes que dependem de serviços externos:
   ```python
   response = client.post("/upload", files={"file": ...}, headers=auth_headers)
   assert response.status_code in (200, 400, 422)
   ```
3. **Documente dependências** no docstring se o teste precisa de configurações específicas:
   ```python
   def test_expert_pl_analise_constitucional(client, auth_headers):
       """Testa análise de constitucionalidade. Requer OPENAI_API_KEY."""
       ...
   ```

### Antes de Comitar

```bash
pytest -q  # Deve passar sem erros
```

### CI/CD

Configure apenas as variáveis mínimas:
- `DATABASE_URL=postgresql://...` (se usar banco externo)
- Opcional: `OPENAI_API_KEY`, `GCS_BUCKET_NAME`, `GOOGLE_APPLICATION_CREDENTIALS` para testes completos

## Melhorias Futuras

- [ ] Completar testes de reset de senha em `test_auth_flow.py` (3 testes incompletos)
- [ ] Consolidar fixtures `admin_user` e `auth_headers` (atualmente duplicam criação do mesmo usuário)
- [ ] Otimizar `db_session` para fazer TRUNCATE seletivo (apenas tabelas usadas no teste)
- [ ] Adicionar testes de performance para busca vetorial
- [ ] Mock completo de SendGrid para validar conteúdo de emails

## Suporte

Para dúvidas ou problemas, veja:
- [README.md principal](../README.md) - Setup geral do projeto
- [GUIDELINES.md](../GUIDELINES.md) - Padrões de código
- Issues no repositório
