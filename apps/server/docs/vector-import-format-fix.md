# Correção do Formato de Importação Vetorial

## Problema Identificado

O importador vetorial estava processando apenas 1 item e gerando 0 chunks quando recebia arquivos JSON no novo formato com wrapper `{"items": [...]}`.

### Causa Raiz

O parser do Streamlit (`client/pages/10_📥_Admin_Importador_Vetorial.py`) estava transformando o dict inteiro em uma lista com 1 elemento:

```python
if isinstance(data, dict):
    data = [data]  # <-- Transforma {"items": [...]} em [{"items": [...]}]
```

Isso fazia com que o backend recebesse:
```json
[
  {
    "items": [...650 items...],
    "export_info": {...}
  }
]
```

Ao invés de extrair os 650 itens dentro do campo `"items"`.

## Solução Implementada

### 1. Correção no Parser do Streamlit

**Arquivo**: `client/pages/10_📥_Admin_Importador_Vetorial.py`

A função `_parse_uploaded_json()` agora detecta e extrai automaticamente a lista de itens quando o JSON tem o formato `{"items": [...]}`:

```python
def _parse_uploaded_json(upload) -> Optional[List[Dict[str, Any]]]:
    # ... [código de parsing] ...
    
    # Se o JSON tem um campo "items", extrair a lista de items
    if isinstance(data, dict) and "items" in data:
        items = data["items"]
        if not isinstance(items, list):
            st.error("O campo 'items' deve ser uma lista.")
            return None
        data = items
    # Se for um dict sem "items", transformar em lista de 1 elemento (formato antigo)
    elif isinstance(data, dict):
        data = [data]
    
    # ... [validação] ...
    return data
```

**Compatibilidade**: Mantém suporte para os formatos antigos:
- Lista direta: `[{...}, {...}]`
- Dict único: `{...}`

### 2. Validação no Backend

**Arquivo**: `routers/vector_admin.py`

Adicionado validator no modelo `VectorImportItem` para detectar quando recebe o wrapper inteiro ao invés de um item:

```python
class VectorImportItem(BaseModel):
    # ... [campos] ...
    
    @model_validator(mode='before')
    @classmethod
    def _check_wrong_format(cls, data):
        """Detecta se recebeu um wrapper ao invés de um item"""
        if isinstance(data, dict) and "items" in data and len(data.keys()) <= 3:
            raise ValueError(
                "Formato incorreto: parece que você enviou o wrapper JSON inteiro. "
                "Envie apenas a lista de itens, não o objeto que contém 'items'."
            )
        return data
```

Essa validação previne erros futuros ao retornar uma mensagem clara se o formato incorreto for enviado.

## Formatos Suportados

O importador agora suporta 3 formatos:

### 1. Formato Novo (com wrapper)
```json
{
  "items": [
    {
      "title": "PL 101/2020",
      "house": "Câmara Municipal de São Paulo",
      "type": "PL",
      "number": 101,
      "year": 2020,
      "author": ["Ver. JOÃO SILVA"],
      "subject": "...",
      "full_text": "...",
      "metadata": {
        "pdf_files": ["..."],
        "uuid": "...",
        "status": []
      }
    },
    ...
  ],
  "export_info": {...}
}
```

### 2. Formato Antigo (lista direta)
```json
[
  {
    "title": "PL 101/2020",
    "full_text": "...",
    ...
  },
  ...
]
```

### 3. Formato Antigo (dict único)
```json
{
  "title": "PL 101/2020",
  "full_text": "...",
  ...
}
```

## Testes Adicionados

Foram adicionados 3 novos testes em `tests/test_vector_admin.py`:

1. **test_vector_import_item_valid**: Valida que items válidos são aceitos, incluindo metadata estruturada
2. **test_vector_import_item_rejects_wrapper**: Verifica que o validator detecta quando o wrapper inteiro é enviado
3. **test_vector_import_request_with_new_format**: Testa o endpoint com o novo formato (múltiplos items)
4. **test_vector_import_request_old_format**: Garante compatibilidade com formato antigo

## Resultado

Após a correção:
- ✅ Arquivos com 650 items são processados corretamente
- ✅ Todos os chunks são gerados a partir do `full_text` de cada item
- ✅ Metadata estruturada (`pdf_files`, `uuid`, etc.) é preservada
- ✅ Backward compatibility mantida
- ✅ Todos os 24 testes passam

## Como Usar

Basta fazer upload do arquivo JSON no formato novo via interface Streamlit:
1. Acesse **Admin • Importador de Referências Vetoriais**
2. Faça upload do arquivo `sp-sao-paulo2020-export.json`
3. Configure as opções de chunking (recomendado: chunk_size=3000, overlap=150)
4. Clique em "Iniciar importação"

O sistema agora processará todos os 650 items corretamente.

## Data da Correção

2025-12-10
