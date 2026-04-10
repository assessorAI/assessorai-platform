from __future__ import annotations

from typing import Any, Dict, List
from pathlib import Path
import sys

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

st.title("Admin • Mandatos")

# Paginação
if "mandato_page" not in st.session_state:
    st.session_state.mandato_page = 0

page_size = st.selectbox("Mandatos por página", [50, 100, 200, 500], index=0, key="mandato_page_size")
offset = st.session_state.mandato_page * page_size

mandatos_response = ui.call_api(api.list_mandatos, limit=page_size, offset=offset)
if mandatos_response is None:
    st.stop()
mandatos = mandatos_response.get("mandatos", [])
total_mandatos = mandatos_response.get("total", 0)
current_page = st.session_state.mandato_page + 1
total_pages = (total_mandatos + page_size - 1) // page_size

# Controles de paginação
col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
with col1:
    st.write(f"Mostrando {len(mandatos)} de {total_mandatos} mandatos (Página {current_page} de {total_pages})")
with col2:
    if st.button("⬅️ Anterior", disabled=st.session_state.mandato_page == 0, key="mandato_prev"):
        st.session_state.mandato_page -= 1
        st.rerun()
with col3:
    if st.button("Próxima ➡️", disabled=current_page >= total_pages, key="mandato_next"):
        st.session_state.mandato_page += 1
        st.rerun()

# Get all users for dropdowns (without pagination)
all_users_response = ui.call_api(api.list_users, limit=500, offset=0) or {}
all_users = all_users_response.get("users", [])
user_options: Dict[str, int] = {
    f"{u.get('email')} ({u.get('permission_level')})": u.get("id")
    for u in all_users
    if u.get("id") is not None
}
user_lookup: Dict[int, Dict[str, Any]] = {u.get("id"): u for u in all_users if u.get("id") is not None}

rows = [
    {
        "ID": m.get("id"),
        "Nome parlamentar": m.get("nome_parlamentar"),
        "Casa legislativa": m.get("casa_legislativa"),
        "Município": m.get("municipio"),
        "UF": m.get("ue"),
        "Cargo Parlamentar": m.get("cargo_parlamentar"),
        "Partido": m.get("partido"),
        "Usuários associados": len(m.get("users", [])),
    }
    for m in mandatos
]

if rows:
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
else:
    st.info("Nenhum mandato cadastrado.")

with st.expander("✏️ Editar mandato existente", expanded=False):
    options = [f"{m.get('id')} - {m.get('nome_parlamentar') or 'Sem nome'}" for m in mandatos]
    if not options:
        st.info("Nenhum mandato para editar.")
    else:
        selection = st.selectbox("Selecione o mandato", options)
        mandato_id = int(selection.split(" - ")[0])
        mandato = next(m for m in mandatos if m["id"] == mandato_id)
        with st.form(f"edit-mandato-{mandato_id}"):
            nome_parlamentar = st.text_input("Nome parlamentar", mandato.get("nome_parlamentar") or "")
            casa = st.text_input("Casa legislativa", mandato.get("casa_legislativa") or "")
            municipio = st.text_input("Município", mandato.get("municipio") or "")
            uf = st.text_input("UF", mandato.get("ue") or "")
            cargo_parlamentar = st.text_input("Cargo Parlamentar", mandato.get("cargo_parlamentar") or "")
            partido = st.text_input("Partido", mandato.get("partido") or "")
            temas = st.text_area("Temas de interesse", mandato.get("temas_interesse") or "")
            perfil = st.text_area("Perfil parlamentar", mandato.get("perfil_parlamentar") or "")
            espectro = st.text_input("Espectro político", mandato.get("espectro_politico") or "")

            current_user_ids_list = list(dict.fromkeys(mandato.get("users", []) or []))
            inverse_labels = {v: k for k, v in user_options.items()}
            current_user_labels: List[str] = []
            for uid in current_user_ids_list:
                label = inverse_labels.get(uid)
                if not label:
                    user_data = user_lookup.get(uid, {})
                    label = f"{user_data.get('email', 'desconhecido')} (ID {uid})"
                    user_options[label] = uid
                    inverse_labels[uid] = label
                current_user_labels.append(label)

            selected_users_edit = st.multiselect(
                "Usuários associados",
                options=list(user_options.keys()),
                default=current_user_labels,
                key=f"mandato-users-{mandato_id}"
            )

            submitted = st.form_submit_button("Salvar alterações")
            if submitted:
                payload: Dict[str, Any] = {
                    "nome_parlamentar": nome_parlamentar or None,
                    "casa_legislativa": casa or None,
                    "municipio": municipio or None,
                    "ue": uf or None,
                    "cargo_parlamentar": cargo_parlamentar or None,
                    "partido": partido or None,
                    "temas_interesse": temas or None,
                    "perfil_parlamentar": perfil or None,
                    "espectro_politico": espectro or None,
                }
                if ui.call_api(api.update_mandato, mandato_id, payload) is not None:
                    selected_ids = {user_options[label] for label in selected_users_edit}
                    current_ids_set = set(current_user_ids_list)
                    to_add = selected_ids - current_ids_set
                    to_remove = current_ids_set - selected_ids
                    for uid in to_add:
                        email = user_lookup.get(uid, {}).get("email")
                        if email:
                            ui.call_api(api.add_user_to_mandato, mandato_id, email)
                    for uid in to_remove:
                        ui.call_api(api.remove_user_from_mandato, mandato_id, uid)
                    st.success("Mandato atualizado com sucesso.")
                    st.rerun()

with st.expander("➕ Criar novo mandato", expanded=False):
    with st.form("create-mandato-form"):
        nome_parlamentar = st.text_input("Nome parlamentar")
        casa = st.text_input("Casa legislativa")
        municipio = st.text_input("Município")
        uf = st.text_input("UF", "SP")
        cargo_parlamentar = st.text_input("Cargo Parlamentar", "Vereador")
        partido = st.text_input("Partido")
        selected_users_create = st.multiselect(
            "Associar usuários existentes",
            options=list(user_options.keys()),
        )
        submitted = st.form_submit_button("Criar mandato")
        if submitted:
            payload = {
                "nome_parlamentar": nome_parlamentar or None,
                "casa_legislativa": casa or None,
                "municipio": municipio or None,
                "ue": uf or None,
                "cargo_parlamentar": cargo_parlamentar or None,
                "partido": partido or None,
            }
            created = ui.call_api(api.create_mandato, payload)
            if created is not None:
                created_id = created.get("id")
                if created_id:
                    for label in selected_users_create:
                        uid = user_options[label]
                        email = user_lookup.get(uid, {}).get("email")
                        if email:
                            ui.call_api(api.add_user_to_mandato, created_id, email)
                st.success("Mandato criado com sucesso.")
                st.rerun()

with st.expander("🗑️ Remover mandato", expanded=False):
    delete_options = [f"{m.get('id')} - {m.get('nome_parlamentar') or 'Sem nome'}" for m in mandatos]
    if not delete_options:
        st.info("Nenhum mandato disponível para remoção.")
    else:
        delete_selection = st.selectbox("Selecione o mandato para remover", delete_options)
        delete_mandato_id = int(delete_selection.split(" - ")[0])
        delete_mandato = next(m for m in mandatos if m["id"] == delete_mandato_id)
        
        st.warning(f"⚠️ Você está prestes a remover o mandato de **{delete_mandato.get('nome_parlamentar')}**")
        st.info(f"Usuários associados: {len(delete_mandato.get('users', []))}")
        
        confirm = st.checkbox("Confirmo a remoção permanente deste mandato", key="confirm-delete-mandato")
        if st.button("Remover mandato", use_container_width=False, disabled=not confirm):
            if ui.call_api(api.delete_mandato, delete_mandato_id) is not None:
                st.success("Mandato removido com sucesso.")
                st.rerun()
