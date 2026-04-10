# Otimização de Performance para Importações Vetoriais

## Problema: Out of Memory (OOM) em Importações Grandes

### Sintomas

- Servidor trava durante importação
- Processo Python morto pelo sistema
- Log mostra "Killed" ou "Out of Memory"
- Importação de arquivos com 500+ documentos falha

### Causas Identificadas

#### 1. Processamento em Memória (Original)

O código original carregava **todos** os documentos na memória de uma vez:

```python
# ❌ PROBLEMA: Carrega tudo na memória
items_list = list(items)  # 650 documentos
documents = prepare_documents(items_list, ...)  # Todos os chunks
assign_embeddings(documents, ...)  # Todos os embeddings
store.bulk_insert(documents)  # Tudo de uma vez
```

**Exemplo de consumo de memória:**
- 650 documentos
- Média 3000 tokens por documento
- Dividido em chunks de ~1000 tokens = ~2 chunks/doc
- Total: ~1300 chunks
- Cada chunk tem embedding de 1536 dimensões (float32)
- Memória: 1300 × 1536 × 4 bytes = **~8 MB apenas embeddings**
- Soma texto + metadados + overhead Python: **~50-100 MB por importação**

#### 2. Importações Concorrentes (Pior Cenário)

Se múltiplas importações acontecem simultaneamente:
- 2 importações × 100 MB = 200 MB
- 3 importações × 100 MB = 300 MB
- Mais overhead do Python, SQLAlchemy, etc.
- Total pode ultrapassar 500 MB facilmente

**Agravantes:**
- Deadlocks no banco de dados
- Rate limits da API OpenAI
- Contenção de recursos
- Race conditions

---

## Solução Implementada: Processamento em Lotes

### Mudança no Código

Arquivo: `services/vector_ingestion.py`

```python
# ✅ SOLUÇÃO: Processa em lotes
BATCH_SIZE = 50  # Configurável via VECTOR_IMPORT_BATCH_SIZE

for batch in batches(items, BATCH_SIZE):
    documents = prepare_documents(batch, ...)  # Apenas 50 por vez
    assign_embeddings(documents, ...)  # Apenas 50 embeddings
    store.bulk_insert(documents)  # Insere e libera memória
```

### Benefícios

1. **Memória Constante**
   - Independente do tamanho do arquivo
   - Máximo: BATCH_SIZE × tamanho_médio_chunk
   - Exemplo: 50 itens = ~5-10 MB por vez

2. **Progress Tracking**
   - Log a cada lote processado
   - Usuário vê progresso em arquivos grandes

3. **Resiliência**
   - Se falhar no lote 5, lotes 1-4 já foram salvos
   - Pode retomar de onde parou

4. **Predictable**
   - Consumo de memória previsível
   - Não depende do tamanho do arquivo

---

## Variáveis de Ambiente

### `VECTOR_IMPORT_BATCH_SIZE`

**Descrição**: Número de documentos processados por vez durante importação.

**Valor padrão**: `50`

**Como configurar:**
```bash
# .env
VECTOR_IMPORT_BATCH_SIZE=50
```

**Quando ajustar:**

- **Aumentar (100-200)** se:
  - Servidor tem muita RAM (16GB+)
  - Documentos são pequenos (< 1000 tokens)
  - Quer importação mais rápida

- **Diminuir (25-30)** se:
  - Servidor tem pouca RAM (< 4GB)
  - Documentos são grandes (> 5000 tokens)
  - Ocorrem erros OOM

**Cálculo estimado:**
```
Memória por lote ≈ BATCH_SIZE × tokens_médios × 0.01 MB
Exemplo: 50 × 3000 × 0.01 = 1.5 MB (seguro)
```

### `EMBEDDING_BATCH_SIZE`

**Descrição**: Número de chunks enviados por vez para a API de embeddings (OpenAI).

**Valor padrão**: `100`

**Como configurar:**
```bash
# .env
EMBEDDING_BATCH_SIZE=100
```

**Quando ajustar:**

- **Aumentar (200-500)** se:
  - Tem rate limit alto na OpenAI
  - Quer importação mais rápida
  - Não há problemas de timeout

- **Diminuir (50)** se:
  - Ocorrem timeouts da OpenAI
  - Rate limits estão sendo atingidos
  - Chunks são muito grandes

### `VECTOR_BATCH_SIZE`

**Descrição**: Número de chunks inseridos por vez no PostgreSQL.

**Valor padrão**: `200`

**Como configurar:**
```bash
# .env
VECTOR_BATCH_SIZE=200
```

**Quando ajustar:**

- **Aumentar (500)** se:
  - PostgreSQL tem boa performance
  - Quer inserção mais rápida

- **Diminuir (100)** se:
  - Ocorrem timeouts no PostgreSQL
  - Banco está em servidor remoto lento

---

## Fluxo de Processamento Otimizado

```
┌─────────────────────────────────────────────┐
│ 1. Arquivo JSON (650 documentos)           │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ 2. Divide em lotes de VECTOR_IMPORT_BATCH_  │
│    SIZE (padrão: 50)                        │
│    - Lote 1: docs 1-50                      │
│    - Lote 2: docs 51-100                    │
│    - ...                                    │
│    - Lote 13: docs 601-650                  │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ Para cada lote:                             │
│   3. prepare_documents() - chunk de texto   │
│   4. assign_embeddings() - gera vetores     │
│      (em sub-lotes de EMBEDDING_BATCH_SIZE) │
│   5. bulk_insert() - salva no PostgreSQL    │
│      (em sub-lotes de VECTOR_BATCH_SIZE)    │
│   6. Libera memória                         │
└─────────────────────────────────────────────┘
```

---

## Monitoramento

### Logs de Progresso

Para importações grandes (> 50 itens), o sistema loga progresso:

```
[vector_ingestion] Processed 50/650 items (7.7%) - 125 chunks inserted
[vector_ingestion] Processed 100/650 items (15.4%) - 245 chunks inserted
[vector_ingestion] Processed 150/650 items (23.1%) - 378 chunks inserted
...
[vector_ingestion] Processed 650/650 items (100.0%) - 1625 chunks inserted
```

### Verificar Consumo de Memória

#### Durante importação:
```bash
# Linux
ps aux | grep python | grep assessorai

# Ou com detalhes
top -p $(pgrep -f assessorai)
```

#### Estatísticas do job:
```python
# Via API ou Streamlit
GET /admin/vector/jobs/{job_id}

# Retorna:
{
  "total_items": 650,
  "processed_chunks": 1625,
  "status": "PROCESSING",
  "created_at": "...",
  ...
}
```

---

## Resolução de Problemas

### OOM ainda ocorre com lotes pequenos

**Possíveis causas:**
1. Servidor realmente tem pouca RAM
2. Outros processos consumindo memória
3. Memory leak no código

**Soluções:**
```bash
# 1. Reduzir todos os batch sizes
VECTOR_IMPORT_BATCH_SIZE=25
EMBEDDING_BATCH_SIZE=50
VECTOR_BATCH_SIZE=100

# 2. Aumentar swap do sistema (Linux)
sudo swapon --show
sudo fallocate -l 2G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 3. Monitorar memória durante importação
watch -n 1 free -h
```

### Importação muito lenta

**Possíveis causas:**
1. Batch sizes muito pequenos
2. Rate limits da OpenAI
3. PostgreSQL lento

**Soluções:**
```bash
# 1. Aumentar batch sizes (se houver RAM)
VECTOR_IMPORT_BATCH_SIZE=100
EMBEDDING_BATCH_SIZE=200

# 2. Verificar rate limits OpenAI
# (logs mostrarão erros 429)

# 3. Otimizar PostgreSQL
# - Adicionar índices
# - Ajustar shared_buffers
# - Usar SSD
```

### Jobs ficam travados

**Causa:** Concorrência ou deadlock

**Solução:** Veja `docs/vector-import-concurrency.md`

```bash
# Limpar jobs travados
python scripts/cleanup_stuck_jobs.py
```

---

## Recomendações por Tamanho

| Documentos | IMPORT_BATCH | EMBEDDING_BATCH | VECTOR_BATCH | RAM Mínima |
|-----------|--------------|-----------------|--------------|------------|
| < 100     | 50 (padrão)  | 100 (padrão)    | 200 (padrão) | 2 GB       |
| 100-500   | 50           | 100             | 200          | 4 GB       |
| 500-1000  | 30           | 75              | 150          | 4 GB       |
| 1000+     | 25           | 50              | 100          | 8 GB       |

**Nota:** Estes valores são estimativas. Teste e ajuste conforme necessário.

---

## Melhorias Futuras

### 1. Processamento Assíncrono (Celery)

- Permite pausar/retomar importações
- Melhor controle de recursos
- Retry automático em falhas

### 2. Streaming Real

- Processar linha a linha do JSON
- Não carregar arquivo inteiro na memória
- Ideal para arquivos gigantes (10k+ docs)

### 3. Compressão de Embeddings

- Quantização (float32 → float16)
- Reduz uso de memória em 50%
- PostgreSQL pgvector suporta halfvec

### 4. Cache de Embeddings

- Não recalcular embeddings duplicados
- Armazenar hash do texto → embedding
- Economiza chamadas à API OpenAI

---

## Referências

- **Código:**
  - `services/vector_ingestion.py` - Lógica de importação em lotes
  - `services/vector_store.py` - Inserção no banco
  - `routers/vector_admin.py` - API endpoints

- **Documentos Relacionados:**
  - `docs/vector-import-concurrency.md` - Proteção contra concorrência
  - `docs/vector-import-format-fix.md` - Formato JSON correto
  - `docs/vector-import-example.md` - Exemplos de uso

---

**Data:** 2025-12-10  
**Versão:** 1.0
