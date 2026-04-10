# Gerenciamento de Jobs de Importação Vetorial

## Problema: Importações Concorrentes

### O que acontece quando múltiplas importações são iniciadas?

Até a versão anterior, o sistema **não** possuía controle de concorrência para importações vetoriais. Isso causava problemas graves:

#### Problemas Identificados:

1. **Conflito de TRUNCATE**
   - Job 1 inicia → executa `TRUNCATE` (apaga tabela)
   - Job 1 começa a inserir dados...
   - Job 2 inicia → executa `TRUNCATE` (apaga dados do Job 1!)
   - Resultado: apenas o último job tem dados, os anteriores são perdidos

2. **Deadlock no Banco de Dados**
   - Múltiplas sessions SQLAlchemy tentando escrever simultaneamente
   - Locks de escrita conflitantes
   - Jobs ficam travados indefinidamente

3. **Race Conditions**
   - Múltiplas threads competindo pelos mesmos recursos
   - Possível corrupção de dados
   - Estado inconsistente no banco

4. **Rate Limits da API**
   - Múltiplos jobs chamando OpenAI API simultaneamente
   - Estouro de rate limits
   - Ambos jobs podem falhar

### Por que jobs ficavam "travados"?

Jobs com status `PENDING` ou `PROCESSING` podiam ficar nesse estado indefinidamente:

- ❌ **Não havia timeout automático**
- ❌ **Não havia detecção de deadlock**
- ❌ **Não havia sistema de fila**
- ❌ **Não havia mecanismo de recuperação**

---

## Solução Implementada

### 1. Validação de Concorrência no Backend

**Arquivo**: `routers/vector_admin.py`

O endpoint `/admin/vector/import` agora:

- ✅ Verifica se há jobs ativos (`PENDING` ou `PROCESSING`)
- ✅ Retorna HTTP 409 (Conflict) se houver job ativo
- ✅ Fornece lista de jobs ativos no erro
- ✅ Permite apenas 1 importação por vez

```python
# Exemplo de resposta de erro
{
  "detail": {
    "error": "concurrent_import_not_allowed",
    "message": "Já existe(m) 2 importação(ões) em andamento...",
    "active_jobs": [
      {
        "id": 1,
        "name": "sp-sao-paulo2020-export.json",
        "status": "PROCESSING",
        "created_at": "2025-12-10T22:18:29"
      }
    ]
  }
}
```

### 2. Bloqueio na Interface (Streamlit)

**Arquivo**: `client/pages/10_📥_Admin_Importador_Vetorial.py`

A interface agora:

- ✅ Consulta jobs ativos antes de mostrar botão
- ✅ Desabilita botão "Iniciar importação" se houver job ativo
- ✅ Mostra aviso claro com jobs em andamento
- ✅ Permite visualizar e cancelar jobs ativos

### 3. Script de Limpeza

**Arquivo**: `scripts/cleanup_stuck_jobs.py`

Utilitário para gerenciar jobs órfãos:

```bash
# Listar todos os jobs e estatísticas
python scripts/cleanup_stuck_jobs.py --list

# Ver jobs travados sem modificar (dry-run)
python scripts/cleanup_stuck_jobs.py --dry-run

# Marcar como FAILED jobs travados há mais de 30 minutos
python scripts/cleanup_stuck_jobs.py

# Customizar timeout (10 minutos)
python scripts/cleanup_stuck_jobs.py --timeout 10
```

O script:
- ✅ Identifica jobs com status `PENDING`/`PROCESSING` antigos
- ✅ Marca como `FAILED` com mensagem descritiva
- ✅ Suporta modo dry-run para preview
- ✅ Configurável via linha de comando

---

## Uso Recomendado

### Para Usuários

1. **Antes de importar:**
   - Verifique se não há importações em andamento
   - O sistema bloqueará automaticamente se houver

2. **Se aparecer aviso de job ativo:**
   - Aguarde a conclusão (verifique o histórico)
   - Ou cancele o job ativo se for órfão/travado

3. **Se um job travar:**
   - Use o botão 🗑️ no histórico para deletar
   - Ou execute o script de limpeza (administradores)

### Para Administradores

1. **Monitorar jobs:**
```bash
python scripts/cleanup_stuck_jobs.py --list
```

2. **Limpar jobs órfãos periodicamente:**
```bash
# Executar via cron, por exemplo
python scripts/cleanup_stuck_jobs.py --timeout 30
```

3. **Se o sistema travar:**
   - Reiniciar o servidor API (mata threads travadas)
   - Executar script de limpeza
   - Verificar logs para causa raiz

---

## Arquitetura

### Fluxo Atual (com proteção)

```
┌────────────────────────────────────────────┐
│ 1. Cliente envia requisição de importação │
└────────────────┬───────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────┐
│ 2. Backend verifica jobs ativos            │
│    ├─ Se houver ativo → HTTP 409 (Conflict)│
│    └─ Se livre → Cria job PENDING          │
└────────────────┬───────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────┐
│ 3. Background task agenda execução         │
│    Status: PENDING → PROCESSING            │
└────────────────┬───────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────┐
│ 4. Executa importação (pode demorar)       │
│    ├─ Sucesso → COMPLETED                  │
│    ├─ Erro → FAILED                        │
│    └─ Travou → fica PROCESSING (órfão)     │
└────────────────────────────────────────────┘
```

### Limitações Conhecidas

1. **Não há sistema de fila distribuída**
   - Jobs não são enfileirados para execução sequencial
   - Apenas bloqueia novas tentativas enquanto há job ativo
   - Para fila robusta, usar Celery/Redis no futuro

2. **Detecção de travamento manual**
   - Não há detecção automática de deadlock
   - Administrador precisa executar script de limpeza
   - Jobs órfãos ficam em PROCESSING até limpeza manual

3. **Reiniciar servidor deixa jobs órfãos**
   - Se servidor reinicia com job em PROCESSING
   - Job fica nesse estado indefinidamente
   - Solução: script de limpeza na inicialização

---

## Melhorias Futuras

Para ambientes de produção com alto volume, considerar:

### Opção A: Sistema de Fila (Celery + Redis)

```python
# Exemplo conceitual
@celery_app.task
def process_import(job_id):
    # Executa importação
    # Celery garante:
    # - Fila FIFO
    # - Retry automático
    # - Timeout configurável
    # - Workers distribuídos
```

**Vantagens:**
- ✅ Fila distribuída
- ✅ Retry automático
- ✅ Timeouts configuráveis
- ✅ Escalável horizontalmente

**Desvantagens:**
- ❌ Adiciona dependência (Redis/RabbitMQ)
- ❌ Mais complexo para deploy
- ❌ Requer infraestrutura adicional

### Opção B: Lock Distribuído (Redis)

```python
# Exemplo conceitual
with redis_lock.Lock(redis_client, "vector_import_lock"):
    # Apenas 1 importação por vez
    result = ingest_documents(...)
```

**Vantagens:**
- ✅ Simples de implementar
- ✅ Funciona em múltiplas instâncias
- ✅ Timeout automático (Redis TTL)

**Desvantagens:**
- ❌ Adiciona dependência (Redis)
- ❌ Não é uma fila (jobs não esperam)

### Opção C: PostgreSQL Advisory Locks

```python
# Exemplo conceitual
session.execute("SELECT pg_advisory_lock(hashtext('vector_import'))")
try:
    result = ingest_documents(...)
finally:
    session.execute("SELECT pg_advisory_unlock(hashtext('vector_import'))")
```

**Vantagens:**
- ✅ Sem dependências externas
- ✅ Funciona com PostgreSQL
- ✅ Transacional

**Desvantagens:**
- ❌ Não funciona com SQLite
- ❌ Limitado ao mesmo banco
- ❌ Não é uma fila

---

## Referências

- **Código**: 
  - `routers/vector_admin.py` - Validação de concorrência
  - `client/pages/10_📥_Admin_Importador_Vetorial.py` - Bloqueio UI
  - `scripts/cleanup_stuck_jobs.py` - Limpeza de jobs

- **Documentos Relacionados**:
  - `docs/vector-import-format-fix.md` - Correção do formato JSON
  - `docs/vector-import-example.md` - Exemplos de importação

- **Issues Relacionados**:
  - Jobs travados em PROCESSING
  - Importações concorrentes causando perda de dados
  - Deadlocks no banco de dados

---

**Data**: 2025-12-10  
**Versão**: 1.0
