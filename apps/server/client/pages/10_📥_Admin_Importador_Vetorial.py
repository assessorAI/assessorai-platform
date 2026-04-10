from __future__ import annotations

import json
import os
from io import StringIO
from math import ceil
from typing import Any, Dict, List, Optional

import streamlit as st

from client.admin import api, ui

ui.render_sidebar()
ui.require_admin_session()

st.title("Admin • Importador de Referências Vetoriais")

DEFAULT_CHUNK_MODEL = os.getenv("CHUNK_TOKEN_MODEL", "text-embedding-ada-002")
DEFAULT_EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "text-embedding-3-small"
)
IMPORT_BATCH_SIZE = max(1, int(os.getenv("VECTOR_BATCH_SIZE", "200")))


def _parse_uploaded_json(upload) -> Optional[List[Dict[str, Any]]]:
    if upload is None:
        return None
    try:
        decoded = upload.getvalue().decode("utf-8")
    except Exception as exc:  # pragma: no cover - streamlit safeguard
        st.error(f"Não foi possível ler o arquivo: {exc}")
        return None
    try:
        data = json.load(StringIO(decoded))
    except json.JSONDecodeError as exc:
        st.error(f"JSON inválido: {exc}")
        return None

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
    
    # Validar que é uma lista de dicts
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        st.error("Esperava uma lista de objetos JSON contendo os campos das proposições.")
        return None
    if not data:
        st.warning("O JSON não contém registros para importar.")
    return data


providers_payload = ui.call_api(api.list_embedding_providers)
stats_payload = ui.call_api(api.vector_stats) or {"projects": 0, "chunks": 0}

if not providers_payload:
    st.stop()

available_providers = providers_payload.get("providers", [])
if not available_providers:
    st.error("Nenhum provedor de embedding disponível. Configure as variáveis e recarregue a página.")
    st.stop()

provider_labels = {item["id"]: item.get("label", item["id"].title()) for item in available_providers}
provider_defaults = {item["id"]: item.get("default_model") for item in available_providers}
provider_ids = [item["id"] for item in available_providers]

current_provider = providers_payload.get("current_provider") or provider_ids[0]
if current_provider not in provider_ids:
    current_provider = provider_ids[0]
current_model = providers_payload.get("current_model") or provider_defaults.get(current_provider) or DEFAULT_EMBEDDING_MODEL

if "vector_embedding_provider" not in st.session_state:
    st.session_state["vector_embedding_provider"] = current_provider
if "vector_embedding_model" not in st.session_state:
    st.session_state["vector_embedding_model"] = current_model

stats_cols = st.columns(3)
stats_cols[0].metric("Projetos indexados", stats_payload.get("projects", 0))
stats_cols[1].metric("Chunks vetoriais", stats_payload.get("chunks", 0))
with stats_cols[2]:
    st.selectbox(
        "Provedor de embedding",
        options=provider_ids,
        index=provider_ids.index(st.session_state["vector_embedding_provider"]),
        key="vector_embedding_provider",
        format_func=lambda value: provider_labels.get(value, value),
    )
    previous_provider = st.session_state.get("vector_embedding_provider_previous")
    current_provider_value = st.session_state["vector_embedding_provider"]
    if previous_provider != current_provider_value:
        previous_default = provider_defaults.get(previous_provider)
        current_value = st.session_state.get("vector_embedding_model")
        if current_value in (None, "", previous_default):
            new_default = provider_defaults.get(current_provider_value)
            if new_default:
                st.session_state["vector_embedding_model"] = new_default
        st.session_state["vector_embedding_provider_previous"] = current_provider_value
    st.text_input(
        "Modelo de embedding",
        key="vector_embedding_model",
        value=st.session_state.get("vector_embedding_model", current_model),
    )
    if st.button(
        "Reindexar vetores",
        type="secondary",
        use_container_width=True,
        disabled=stats_payload.get("chunks", 0) == 0,
    ):
        provider_value = st.session_state.get("vector_embedding_provider")
        model_value = (st.session_state.get("vector_embedding_model") or "").strip() or None
        with st.spinner("Reindexando vetores existentes…"):
            summary = ui.call_api(
                api.reindex_vectors,
                {
                    "embedding_provider": provider_value,
                    "embedding_model": model_value,
                },
            )
        if summary:
            st.success(
                f"Reindexação concluída com {summary.get('chunks', 0)} chunks atualizados "
                f"(skipped: {summary.get('skipped', 0)})."
            )
            st.rerun()

uploaded_file = st.file_uploader("Arquivo JSON com proposições", type=["json"], accept_multiple_files=False)
records = _parse_uploaded_json(uploaded_file) if uploaded_file else None

# Check for duplicates when file is uploaded
duplicate_check = None
if records and len(records) > 0:
    with st.spinner("Verificando duplicatas..."):
        try:
            duplicate_check = ui.call_api(api.check_vector_duplicates, records[:5])
        except Exception as e:
            st.warning(f"Não foi possível verificar duplicatas: {e}")
    
    if duplicate_check and duplicate_check.get("existing_count", 0) > 0:
        st.warning(duplicate_check.get("warning_message", "Alguns documentos já existem no banco."))
        with st.expander("📋 Ver documentos existentes"):
            for doc in duplicate_check.get("existing_documents", []):
                st.write(f"- **{doc.get('title')}** ({doc.get('type')} {doc.get('number')}/{doc.get('year')}) - {doc.get('chunk_count')} chunks")

with st.expander("Configurações de importação", expanded=True):
    chunk_full_text = st.checkbox("Dividir texto completo em chunks", value=True)
    col_tokens, col_overlap = st.columns(2)
    chunk_size = col_tokens.number_input(
        "Tokens por chunk",
        min_value=128,
        max_value=8000,
        step=128,
        value=3000,
    )
    chunk_overlap = col_overlap.number_input(
        "Tokens de overlap",
        min_value=0,
        max_value=1000,
        step=25,
        value=150,
    )
    chunk_model = st.text_input(
        "Modelo para contagem de tokens",
        value=DEFAULT_CHUNK_MODEL,
        help="Usado apenas para o algoritmo de chunking",
    )
    truncate_before_insert = st.checkbox(
        "Substituir registros existentes",
        value=False,
        help="Executa TRUNCATE na tabela antes de inserir os novos vetores.",
    )
    st.caption(
        f"Provedor selecionado: **{provider_labels.get(st.session_state['vector_embedding_provider'])}**"
    )
    st.caption(f"Importação será enviada em lotes de **{IMPORT_BATCH_SIZE}** registros.")

if records:
    st.subheader("Prévia dos registros")
    preview_rows = min(len(records), 5)
    st.write(f"Total de registros detectados: {len(records)}")
    st.json(records[:preview_rows])

    import_name = st.text_input(
        "Nome da Importação",
        value=uploaded_file.name if uploaded_file else "",
        help="Identificador para acompanhar o status da importação.",
    )

col_actions = st.columns(2)

# Check for active jobs before allowing new import
jobs_list = ui.call_api(api.list_import_jobs, limit=50) or []
active_jobs = [j for j in jobs_list if j.get("status") in ["PENDING", "PROCESSING"]]

if active_jobs:
    st.warning(
        f"⚠️ Há {len(active_jobs)} importação(ões) em andamento. "
        "Aguarde a conclusão ou cancele os jobs ativos antes de iniciar uma nova importação."
    )
    with st.expander("Ver jobs ativos"):
        for job in active_jobs:
            st.write(f"- **{job.get('name')}** (ID: {job.get('id')}) - Status: {job.get('status')}")
    import_disabled = True
else:
    import_disabled = False

if col_actions[1].button("Iniciar importação", type="primary", disabled=import_disabled):
    if not records:
        st.error("Envie um arquivo JSON válido antes de iniciar a importação.")
    else:
        provider_value = st.session_state.get("vector_embedding_provider")
        model_value = (st.session_state.get("vector_embedding_model") or "").strip() or None
        
        with st.spinner("Iniciando importação em segundo plano…"):
            payload = {
                "items": records,
                "chunk_full_text": chunk_full_text,
                "chunk_size": int(chunk_size),
                "chunk_overlap": int(chunk_overlap),
                "chunk_token_model": chunk_model.strip() or None,
                "truncate_before_insert": truncate_before_insert,
                "embedding_provider": provider_value,
                "embedding_model": model_value,
                "name": import_name.strip() or None,
            }
            job = ui.call_api(api.import_vector_documents, payload)
        
        if job:
            st.success(f"Importação iniciada! Job ID: {job.get('id')} - Status: {job.get('status')}")
            st.rerun()

else:
    if col_actions[0].button("Limpar arquivo", type="secondary"):
        st.rerun()

st.divider()
st.subheader("Histórico de Importações")

if st.button("Atualizar lista"):
    st.rerun()

jobs = ui.call_api(api.list_import_jobs, limit=10)
if jobs:
    for job in jobs:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
            col1.markdown(f"**{job.get('name', 'Sem nome')}**")
            
            status = job.get('status')
            if status == "COMPLETED":
                col2.success(status)
            elif status == "FAILED":
                col2.error(status)
            elif status == "PROCESSING":
                col2.warning(status)
            else:
                col2.info(status)
                
            col3.caption(f"Items: {job.get('total_items')} | Chunks: {job.get('processed_chunks')}")
            col4.caption(job.get('created_at'))
            
            # Delete button
            if col5.button("🗑️", key=f"delete_{job.get('id')}", help="Deletar importação"):
                if ui.call_api(api.delete_import_job, job.get('id')):
                    st.success("Importação deletada com sucesso!")
                    st.rerun()
            
            # Collapsible error message
            if job.get('error_message'):
                with st.expander("⚠️ Ver erro"):
                    st.error(job.get('error_message'))
            st.divider()
else:
    st.info("Nenhuma importação recente encontrada.")

