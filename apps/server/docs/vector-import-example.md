# Documentação: Formato JSON para Importação de Referências Vetoriais

Este documento descreve o formato JSON esperado pelo **Admin Importador Vetorial** do AssessorAI para importação de bases de referências legislativas.

## Visão Geral

O importador vetorial processa documentos legislativos (projetos de lei, emendas, etc.) e os transforma em embeddings vetoriais para busca semântica. O arquivo JSON deve conter uma lista de objetos representando proposições legislativas.

## Acesso ao Importador

- **Interface Admin**: Streamlit Admin Console → `📥 Admin Importador Vetorial`
- **Endpoint API**: `POST /admin/vector/import`
- **Requisitos**: Permissão de administrador (`Admin`)

## Formato do Arquivo JSON

### Estrutura Básica

```json
[
  {
    "title": "Projeto de Lei nº 123/2024",
    "house": "Câmara dos Deputados",
    "type": "PL",
    "number": 123,
    "presentation_date": "2024-03-15",
    "year": 2024,
    "author": ["Deputado João Silva", "Deputada Maria Santos"],
    "subject": "Dispõe sobre políticas públicas de educação digital",
    "full_text": "Texto completo do projeto de lei...",
    "length": 5420,
    "url": "https://www.camara.leg.br/proposicoes/123456",
    "scraped_at": "2024-03-20T10:30:00Z",
    "metadata": {
      "status": "Em tramitação",
      "comissao": "CEDU",
      "relator": "Deputado Carlos Oliveira"
    }
  },
  {
    "title": "Emenda nº 45 ao PL 123/2024",
    "type": "EMC",
    "number": 45,
    "year": 2024,
    "author": "Senadora Ana Costa",
    "subject": "Altera dispositivo sobre financiamento de programas educacionais",
    "full_text": "Texto da emenda..."
  }
]
```

## Campos Disponíveis

Todos os campos são **opcionais**, mas recomenda-se fornecer o máximo de informações possível para melhor qualidade das buscas.

### Campos Principais

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `title` | `string` | Título da proposição | `"Projeto de Lei nº 123/2024"` |
| `house` | `string` | Casa legislativa de origem | `"Câmara dos Deputados"`, `"Senado Federal"`, `"Câmara Municipal de São Paulo"` |
| `type` | `string` | Tipo da proposição | `"PL"`, `"PEC"`, `"EMC"`, `"PDC"`, `"PLS"` |
| `number` | `integer` | Número da proposição | `123` |
| `presentation_date` | `string` | Data de apresentação (ISO 8601) | `"2024-03-15"` ou `"2024-03-15T14:30:00Z"` |
| `year` | `integer` | Ano da proposição | `2024` |
| `author` | `string` ou `array` | Autor(es) da proposição | `"Deputado João Silva"` ou `["Dep. João", "Dep. Maria"]` |
| `subject` | `string` | Ementa ou assunto resumido | `"Dispõe sobre políticas de educação digital"` |
| `full_text` | `string` | Texto completo da proposição | `"Art. 1º Esta lei estabelece..."` |
| `length` | `integer` | Tamanho do texto em caracteres | `5420` |
| `url` | `string` | URL da fonte original | `"https://www.camara.leg.br/proposicoes/123456"` |
| `scraped_at` | `string` | Timestamp da coleta (ISO 8601) | `"2024-03-20T10:30:00Z"` |
| `metadata` | `object` ou `string` | Metadados adicionais (JSON) | `{"status": "Em tramitação", "relator": "..."}` |

### Detalhes dos Campos

#### `author`
- Aceita **string simples** ou **array de strings**
- Automaticamente normalizado para lista internamente
- Exemplos válidos:
  ```json
  "author": "Deputado João Silva"
  "author": ["Deputado João Silva", "Deputada Maria Santos"]
  ```

#### `metadata`
- Aceita **objeto JSON** ou **string JSON**
- Se for string, será parseada como JSON
- Pode conter qualquer estrutura de dados adicional
- Exemplos:
  ```json
  "metadata": {"status": "Aprovado", "urgencia": "Sim"}
  "metadata": "{\"status\": \"Aprovado\"}"
  ```

#### `full_text`
- Campo mais importante para busca semântica
- Será automaticamente dividido em chunks (pedaços) para processamento
- Se ausente, usa o campo `subject` como fallback
- Sem limite de tamanho (será chunkeado automaticamente)

## Configurações de Importação

Ao fazer upload do JSON na interface admin, você pode configurar:

### Parâmetros de Chunking

| Parâmetro | Descrição | Padrão | Limites |
|-----------|-----------|--------|---------|
| **Dividir texto em chunks** | Ativa divisão automática de textos longos | `true` | — |
| **Tokens por chunk** | Tamanho máximo de cada pedaço | `3000` | 128 - 8000 |
| **Tokens de overlap** | Sobreposição entre chunks consecutivos | `150` | 0 - 1000 |
| **Modelo para contagem** | Modelo usado para tokenização | `text-embedding-ada-002` | — |

### Parâmetros de Processamento

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| **Substituir registros existentes** | Limpa a base antes de importar | `true` |
| **Provedor de embedding** | Serviço de embeddings | `OpenAI Embeddings` |
| **Modelo de embedding** | Modelo específico | `text-embedding-3-small` |
| **Nome da Importação** | Identificador do job | Nome do arquivo |

## Exemplos Práticos

### Exemplo 1: Projeto de Lei Completo

```json
[
  {
    "title": "PL 2547/2024 - Marco Legal da Inteligência Artificial",
    "house": "Câmara dos Deputados",
    "type": "PL",
    "number": 2547,
    "presentation_date": "2024-05-10",
    "year": 2024,
    "author": ["Deputado Carlos Tech", "Deputada Ana Digital"],
    "subject": "Estabelece princípios, direitos e deveres para o uso de inteligência artificial no Brasil",
    "full_text": "PROJETO DE LEI Nº 2547, DE 2024\n\nDispõe sobre o uso de inteligência artificial no Brasil.\n\nO CONGRESSO NACIONAL decreta:\n\nArt. 1º Esta Lei estabelece princípios, regras, direitos e deveres para o desenvolvimento e a aplicação de sistemas de inteligência artificial (IA) no Brasil.\n\nArt. 2º Para os fins desta Lei, considera-se:\nI - inteligência artificial: sistema baseado em processo computacional que pode, para um determinado conjunto de objetivos definidos pelo ser humano, fazer previsões e recomendações ou tomar decisões que influenciam ambientes reais ou virtuais;\nII - sistema de IA de alto risco: sistema de IA que apresenta risco significativo de causar danos à saúde, segurança ou direitos fundamentais das pessoas.\n\n[...texto continua...]",
    "length": 15420,
    "url": "https://www.camara.leg.br/proposicoes/2024/pl-2547",
    "scraped_at": "2024-05-15T18:30:00Z",
    "metadata": {
      "status": "Aguardando Designação de Relator",
      "regime_tramitacao": "Ordinário",
      "forma_apreciacao": "Conclusiva",
      "comissoes": ["CTASP", "CDC", "CCJC"],
      "tags": ["IA", "Tecnologia", "Direitos Digitais"],
      "indexacao": "Inteligência artificial, IA, algoritmos, direitos fundamentais"
    }
  }
]
```

### Exemplo 2: Múltiplas Proposições Municipais

```json
[
  {
    "title": "Projeto de Lei nº 42/2024",
    "house": "Câmara Municipal de São Paulo",
    "type": "PL",
    "number": 42,
    "year": 2024,
    "author": "Vereador Pedro Souza",
    "subject": "Institui o Programa Municipal de Hortas Urbanas",
    "full_text": "Cria programa de incentivo à agricultura urbana em terrenos públicos ociosos...",
    "url": "https://www.saopaulo.sp.leg.br/proposicoes/42-2024"
  },
  {
    "title": "Emenda nº 3 ao PL 42/2024",
    "house": "Câmara Municipal de São Paulo",
    "type": "EMC",
    "number": 3,
    "year": 2024,
    "author": "Vereadora Maria Lima",
    "subject": "Inclui parcerias com ONGs no programa de hortas urbanas",
    "full_text": "Dê-se ao art. 5º a seguinte redação: Art. 5º O programa poderá estabelecer parcerias...",
    "metadata": {
      "pl_origem": "PL 42/2024",
      "tipo_emenda": "Modificativa"
    }
  },
  {
    "title": "Indicação nº 128/2024",
    "house": "Câmara Municipal de São Paulo",
    "type": "IND",
    "number": 128,
    "year": 2024,
    "author": "Vereador João Ambiental",
    "subject": "Sugere criação de horta comunitária no Parque da Juventude",
    "full_text": "Sugere ao Executivo a implantação de horta comunitária..."
  }
]
```

### Exemplo 3: Formato Mínimo Válido

```json
[
  {
    "subject": "Resumo da proposição",
    "full_text": "Texto completo para indexação vetorial"
  }
]
```

## Processo de Importação

### 1. Upload do Arquivo
1. Acesse **Admin Importador Vetorial**
2. Faça upload do arquivo `.json`
3. Visualize a prévia dos 5 primeiros registros
4. Ajuste as configurações de chunking e embedding

### 2. Processamento em Background
- A importação é processada em **segundo plano** (background job)
- Não bloqueia a interface do usuário
- Status disponível em **Histórico de Importações**

### 3. Acompanhamento
- **Job ID**: Identificador único da importação
- **Status**: `PENDING` → `PROCESSING` → `COMPLETED` / `FAILED`
- **Métricas**: Total de items, chunks processados
- **Timestamp**: Data/hora da criação

## Estados de Importação

| Status | Descrição |
|--------|-----------|
| `PENDING` | Job criado, aguardando processamento |
| `PROCESSING` | Importação em andamento |
| `COMPLETED` | Concluído com sucesso |
| `FAILED` | Erro durante processamento |

## Solução de Problemas

### JSON Inválido
```
Erro: "JSON inválido: Expecting property name enclosed in double quotes"
```
**Solução**: Valide o JSON em https://jsonlint.com antes do upload

### Lista Vazia
```
Erro: "O JSON não contém registros para importar"
```
**Solução**: Certifique-se de que o array contém ao menos 1 objeto

### Timeout na Importação
```
Erro: "Conexão falhou após 3 tentativas"
```
**Solução**: 
- Divida o arquivo em lotes menores (máx 200 registros por arquivo)
- Reduza o tamanho do campo `full_text` de cada item
- Verifique a variável `VECTOR_BATCH_SIZE` (padrão: 200)

### Campos com Caracteres Especiais
- Use UTF-8 encoding no arquivo JSON
- Escape caracteres especiais em strings JSON: `\"`, `\n`, `\t`

## Limites e Recomendações

### Limites Técnicos
- **Chunk size**: 128 - 8000 tokens
- **Chunk overlap**: 0 - 1000 tokens
- **Batch size**: Configurável via `VECTOR_BATCH_SIZE` (padrão: 200)
- **Timeout**: 180 segundos para operações de importação

### Recomendações
- **Tamanho de arquivo**: Máximo 1000 registros por arquivo para melhor performance
- **Qualidade dos dados**: Quanto mais campos preenchidos, melhor a busca
- **Campo `full_text`**: Essencial para busca semântica de qualidade
- **Metadados estruturados**: Facilita filtragens e análises futuras

## API Endpoint

### POST `/admin/vector/import`

**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Body:**
```json
{
  "items": [
    {
      "title": "...",
      "full_text": "...",
      ...
    }
  ],
  "chunk_full_text": true,
  "chunk_size": 3000,
  "chunk_overlap": 150,
  "chunk_token_model": "text-embedding-ada-002",
  "truncate_before_insert": true,
  "embedding_provider": "openai",
  "embedding_model": "text-embedding-3-small",
  "name": "Importação PLs 2024"
}
```

**Response:**
```json
{
  "id": 123,
  "name": "Importação PLs 2024",
  "status": "PENDING",
  "created_at": "2024-12-03T22:30:00Z",
  "completed_at": null,
  "total_items": 50,
  "processed_chunks": 0,
  "error_message": null,
  "created_by": 1
}
```

## Verificação de Importação

### Via Interface Admin
1. Acesse **Admin Importador Vetorial**
2. Role até **Histórico de Importações**
3. Verifique o status do job
4. Em caso de erro, expanda **⚠️ Ver erro**

### Via API
```bash
# Listar jobs
GET /admin/vector/jobs?limit=10&offset=0

# Status da importação
GET /admin/vector/stats
```

### Via Busca
```bash
# Testar busca vetorial
GET /search/query?query=educação+digital&limit=5
```

## Próximos Passos

Após importação bem-sucedida:
1. **Teste a busca**: Acesse `🔎 Admin Busca Referencias`
2. **Verifique estatísticas**: Veja métricas em `📊 Admin Dashboard`
3. **Use no Expert PL**: Referências disponíveis em `🧠 Admin Expert PL`

## Suporte

Para problemas ou dúvidas:
- Verifique logs em **Admin Dashboard** → **Health**
- Consulte `HISTORY.md` para mudanças recentes
- Contate o administrador do sistema
