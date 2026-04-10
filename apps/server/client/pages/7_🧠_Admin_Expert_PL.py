from __future__ import annotations

from pathlib import Path
import json
import sys
from typing import Any, Dict

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

st.title("Admin • Expert PL")

mandatos_response = ui.call_api(api.list_mandatos) or {}
mandatos = mandatos_response.get("mandatos", [])
mandato_options: Dict[str, Optional[int]] = {"Selecionar automaticamente": None}
for m in mandatos:
    label = f"{m.get('nome_parlamentar') or 'Sem nome'} (ID {m.get('id')})"
    mandato_options[label] = m.get("id")

origem_choices = ["", "Executivo", "Legislativo"]

tab_const, tab_emendas, tab_criar_emenda, tab_projeto = st.tabs(
    [
        "Análise constitucionalidade",
        "Sugestão de emendas",
        "Redação de emenda",
        "Projeto de lei",
    ]
)


def render_llm_result(result: Dict[str, Any]) -> None:
    if not result:
        return
    if result.get("full_markdown"):
        st.markdown(result["full_markdown"], unsafe_allow_html=False)
    elif result.get("response"):
        st.markdown(result["response"], unsafe_allow_html=False)
    else:
        st.json(result)


with tab_const:
    with st.form("expert-const"):
        mandato_label = st.selectbox("Mandato", list(mandato_options.keys()), key="mandato-const")
        origem = st.selectbox("Origem legislativa", origem_choices, key="origem-const")
        arquivo = st.file_uploader("Projeto (PDF)", type=["pdf"], key="file-const")
        submitted = st.form_submit_button("Analisar", use_container_width=True)
    if submitted:
        with st.spinner("Executando análise..."):
            result = ui.call_api(
                api.expert_pl_analysis,
                mandato_options[mandato_label],
                origem or None,
                arquivo,
            )
        if result:
            render_llm_result(result)


with tab_emendas:
    with st.form("expert-emendas"):
        mandato_label = st.selectbox("Mandato", list(mandato_options.keys()), key="mandato-emendas")
        origem = st.selectbox("Origem legislativa", origem_choices, key="origem-emendas")
        arquivo = st.file_uploader("Projeto (PDF)", type=["pdf"], key="file-emendas")
        submitted = st.form_submit_button("Sugerir emendas", use_container_width=True)
    if submitted:
        with st.spinner("Gerando sugestões..."):
            result = ui.call_api(
                api.expert_pl_suggest_amendments,
                mandato_options[mandato_label],
                origem or None,
                arquivo,
            )
        if result:
            render_llm_result(result)


with tab_criar_emenda:
    with st.form("expert-criar-emenda"):
        mandato_label = st.selectbox("Mandato", list(mandato_options.keys()), key="mandato-criar-emenda")
        origem = st.selectbox("Origem legislativa", origem_choices, key="origem-criar-emenda")
        artigo = st.number_input("Artigo", min_value=1, step=1, key="emenda-artigo")
        tipo = st.selectbox(
            "Tipo",
            ["aditiva", "modificativa", "supressiva"],
            key="emenda-tipo",
        )
        texto = st.text_area("Texto resumido da alteração", height=120, key="emenda-texto")
        arquivo = st.file_uploader("Projeto base (PDF)", type=["pdf"], key="file-criar-emenda")
        submitted = st.form_submit_button("Gerar emenda", use_container_width=True)
    if submitted:
        payload = {
            "art": int(artigo),
            "tipo": tipo,
            "texto": texto,
        }
        with st.spinner("Gerando emenda completa..."):
            result = ui.call_api(
                api.expert_pl_create_amend,
                mandato_options[mandato_label],
                origem or None,
                payload,
                arquivo,
            )
        if result:
            render_llm_result(result)


with tab_projeto:
    with st.form("expert-projeto"):
        mandato_label = st.selectbox("Mandato", list(mandato_options.keys()), key="mandato-projeto")
        origem = st.selectbox("Origem legislativa", origem_choices, key="origem-projeto")
        tema = st.text_area("Tema do projeto", height=120, key="tema-projeto")
        referencias = st.text_area(
            "Referências (JSON opcional)",
            help="Forneça uma lista JSON de contextos (texto, arquivo base64 ou referência por ID).",
            key="referencias-projeto",
        )
        submitted = st.form_submit_button("Gerar projeto", use_container_width=True)
    if submitted:
        referencias_str = referencias.strip() or None
        if referencias_str:
            try:
                json.loads(referencias_str)
            except json.JSONDecodeError as err:
                st.error(f"JSON inválido em Referências: {err}")
                referencias_str = None
        with st.spinner("Gerando proposta..."):
            result = ui.call_api(
                api.expert_pl_create_project,
                mandato_options[mandato_label],
                origem or None,
                tema.strip(),
                referencias_str,
            )
        if result:
            render_llm_result(result)
