from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Dict

import pandas as pd
import streamlit as st

try:
    from client.admin import api, ui
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from client.admin import api, ui  # type: ignore  # noqa: E402

ui.render_sidebar()
ui.require_admin_session()

st.title("Admin • Busca de referências")

# Display summary statistics
summary_data = ui.call_api(api.vector_summary)
if summary_data:
    st.subheader("📊 Resumo da Base Vetorial")
    
    houses = summary_data.get("houses", [])
    total_projects = summary_data.get("total_projects", 0)
    
    if houses:
        # Create columns for each house
        cols = st.columns(len(houses))
        
        for idx, house_data in enumerate(houses):
            with cols[idx]:
                house_name = house_data.get("house", "Sem casa")
                years = house_data.get("years", [])
                
                # Calculate total for this house
                house_total = sum(y.get("count", 0) for y in years)
                
                st.metric(f"🏛️ {house_name}", house_total)
                
                # Display years with counts
                if years:
                    years_text = []
                    for year_data in years[:5]:  # Show top 5 years
                        year = year_data.get("year", 0)
                        count = year_data.get("count", 0)
                        years_text.append(f"{year} ({count})")
                    
                    st.caption(" • ".join(years_text))
                    
                    if len(years) > 5:
                        with st.expander("Ver todos os anos"):
                            for year_data in years[5:]:
                                year = year_data.get("year", 0)
                                count = year_data.get("count", 0)
                                st.caption(f"{year} ({count})")
        
        st.caption(f"**Total de projetos únicos:** {total_projects}")
    else:
        st.info("Nenhum dado encontrado na base vetorial.")
    
    st.divider()

# Initialize session state for pagination
if "search_offset" not in st.session_state:
    st.session_state.search_offset = 0
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

query = st.text_input("Buscar por", placeholder="Exemplo: iluminação pública em praças", value=st.session_state.search_query)
col_limit, col_filters = st.columns([1, 2])
limit = col_limit.number_input("Limite", min_value=1, max_value=50, value=5, step=1)

# Advanced filters in expander
with col_filters.expander("🔍 Filtros avançados"):
    filter_house = st.selectbox("Casa", ["Todas", "Câmara dos Deputados", "Senado Federal"], index=0)
    col_year_from, col_year_to = st.columns(2)
    filter_year_from = col_year_from.number_input("Ano inicial", min_value=1900, max_value=2100, value=2020, step=1)
    filter_year_to = col_year_to.number_input("Ano final", min_value=1900, max_value=2100, value=2025, step=1)
    filter_score_threshold = st.slider("Score mínimo", min_value=0.0, max_value=1.0, value=0.0, step=0.05)

def apply_filters(items: list) -> list:
    """Apply advanced filters to search results."""
    filtered = items
    
    # Filter by house
    if filter_house != "Todas":
        filtered = [item for item in filtered if item.get("house") == filter_house]
    
    # Filter by year range
    filtered = [item for item in filtered 
                if filter_year_from <= item.get("year", 0) <= filter_year_to]
    
    # Filter by score threshold
    filtered = [item for item in filtered 
                if item.get("score", 0) >= filter_score_threshold]
    
    return filtered


def render_pagination_controls(pagination: Dict[str, Any]) -> None:
    """Render previous/next pagination buttons."""
    st.divider()
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    
    has_more = pagination.get("has_more", False)
    current_offset = pagination.get("offset", 0)
    returned = pagination.get("total_returned", 0)
    
    with col_info:
        st.caption(f"Mostrando resultados a partir do índice {current_offset}")
    
    with col_prev:
        if current_offset > 0:
            if st.button("⬅️ Anterior", use_container_width=True):
                st.session_state.search_offset = max(0, current_offset - int(limit))
                st.rerun()
    
    with col_next:
        if has_more:
            if st.button("Próxima ➡️", use_container_width=True):
                st.session_state.search_offset = current_offset + returned
                st.rerun()


tab_chunks, tab_projects = st.tabs(["Resultados detalhados", "Projetos relacionados"])

def show_chunk_results(payload: Dict[str, Any]) -> None:
    # Display performance metrics
    query_time = payload.get("query_time_ms", 0)
    pagination = payload.get("pagination", {})
    
    col_metrics_1, col_metrics_2, col_metrics_3 = st.columns(3)
    col_metrics_1.metric("⏱️ Tempo de consulta", f"{query_time:.0f} ms")
    col_metrics_2.metric("📊 Resultados", pagination.get("total_returned", 0))
    col_metrics_3.metric("📄 Offset", pagination.get("offset", 0))
    
    results = payload.get("projects", [])
    if not results:
        st.info("Nenhum resultado para a busca informada.")
        return
    
    # Apply filters
    filtered_results = apply_filters(results)
    if not filtered_results:
        st.warning("Nenhum resultado corresponde aos filtros aplicados.")
        return
    
    df = pd.DataFrame(filtered_results)
    st.dataframe(df, use_container_width=True)
    
    # Pagination controls
    render_pagination_controls(pagination)


def show_project_results(payload: Dict[str, Any]) -> None:
    # Display performance metrics
    query_time = payload.get("query_time_ms", 0)
    pagination = payload.get("pagination", {})
    
    col_metrics_1, col_metrics_2, col_metrics_3 = st.columns(3)
    col_metrics_1.metric("⏱️ Tempo de consulta", f"{query_time:.0f} ms")
    col_metrics_2.metric("📊 Projetos", pagination.get("total_returned", 0))
    col_metrics_3.metric("📄 Offset", pagination.get("offset", 0))
    
    projects = payload.get("projects", [])
    if not projects:
        st.info("Nenhum projeto encontrado.")
        return
    
    # Apply filters
    filtered_projects = apply_filters(projects)
    if not filtered_projects:
        st.warning("Nenhum projeto corresponde aos filtros aplicados.")
        return
    
    for project in filtered_projects:
        with st.expander(f"{project.get('title')} • {project.get('year')}"):
            st.write(f"Autor: {project.get('author') or '—'}")
            st.write(f"Casa: {project.get('house') or '—'}")
            st.write(f"Assunto: {project.get('subject') or '—'}")
            st.write(f"Score médio: {project.get('score'):.2f}")
            chunks = project.get("chunks", [])
            if chunks:
                st.write("Trechos mais relevantes:")
                for chunk in chunks[:5]:
                    st.markdown(f"**Trecho {chunk.get('chunk_number')}** — score {chunk.get('score'):.2f}")
                    chunk_text = chunk.get("chunk_text", "")
                    if len(chunk_text) > 500:
                        with st.expander("📄 Ver texto completo"):
                            st.markdown(chunk_text)
                        st.markdown(chunk_text[:500] + "...")
                    else:
                        st.markdown(chunk_text)
    
    # Pagination controls
    render_pagination_controls(pagination)


with tab_chunks:
    if st.button("Buscar detalhes", use_container_width=True, key="btn-chunks"):
        if not query.strip():
            st.error("Digite um termo de busca.")
        else:
            # Update session state
            if query.strip() != st.session_state.search_query:
                st.session_state.search_offset = 0
            st.session_state.search_query = query.strip()
            
            with st.spinner("Consultando base vetorial..."):
                payload = ui.call_api(api.vector_query, query.strip(), int(limit), 
                                     st.session_state.search_offset, True)
            if payload:
                show_chunk_results(payload)

with tab_projects:
    if st.button("Listar projetos", use_container_width=True, key="btn-projects"):
        if not query.strip():
            st.error("Digite um termo de busca.")
        else:
            # Update session state
            if query.strip() != st.session_state.search_query:
                st.session_state.search_offset = 0
            st.session_state.search_query = query.strip()
            
            with st.spinner("Carregando projetos relevantes..."):
                payload = ui.call_api(api.vector_top_projects, query.strip(), int(limit), 
                                     st.session_state.search_offset)
            if payload:
                show_project_results(payload)
