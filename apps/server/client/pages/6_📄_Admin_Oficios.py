from __future__ import annotations

from pathlib import Path
import sys
from typing import Dict, Optional

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

st.title("Admin • Geração de Ofícios")

mandatos_response = ui.call_api(api.list_mandatos) or {}
mandatos = mandatos_response.get("mandatos", [])

mandato_options: Dict[str, Optional[int]] = {"Selecionar automaticamente": None}
for m in mandatos:
    label = f"{m.get('nome_parlamentar') or 'Sem nome'} (ID {m.get('id')})"
    mandato_options[label] = m.get("id")

with st.form("generate-oficio"):
    selected_label = st.selectbox("Mandato", list(mandato_options.keys()))
    demanda = st.text_area("Descreva a demanda", height=200)
    submitted = st.form_submit_button("Gerar ofício", use_container_width=True)

if submitted:
    if not demanda.strip():
        st.error("Informe a demanda para gerar o ofício.")
    else:
        with st.spinner("Gerando ofício..."):
            result = ui.call_api(
                api.generate_oficio,
                mandato_options[selected_label],
                demanda.strip(),
            )
        if result:
            st.success("Ofício gerado com sucesso!")
            if isinstance(result, dict):
                if result.get("full_markdown"):
                    st.markdown(result["full_markdown"], unsafe_allow_html=False)
                elif result.get("response"):
                    st.markdown(result["response"], unsafe_allow_html=False)
                else:
                    st.json(result)
            else:
                st.write(result)
