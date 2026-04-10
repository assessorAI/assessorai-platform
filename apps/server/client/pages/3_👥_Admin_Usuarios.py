from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Dict, List

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
admin_session = ui.require_admin_session()

st.title("Admin • Usuários")

# Paginação
if "user_page" not in st.session_state:
    st.session_state.user_page = 0

page_size = st.selectbox("Usuários por página", [50, 100, 200, 500], index=0, key="page_size")
offset = st.session_state.user_page * page_size

users_response = ui.call_api(api.list_users, limit=page_size, offset=offset)
if users_response is None:
    st.stop()

users = users_response.get("users", [])
total_users = users_response.get("total", 0)
current_page = st.session_state.user_page + 1
total_pages = (total_users + page_size - 1) // page_size

# Controles de paginação
col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
with col1:
    st.write(f"Mostrando {len(users)} de {total_users} usuários (Página {current_page} de {total_pages})")
with col2:
    if st.button("⬅️ Anterior", disabled=st.session_state.user_page == 0):
        st.session_state.user_page -= 1
        st.rerun()
with col3:
    if st.button("Próxima ➡️", disabled=current_page >= total_pages):
        st.session_state.user_page += 1
        st.rerun()

mandatos_response = ui.call_api(api.list_mandatos) or {}
mandatos = mandatos_response.get("mandatos", [])
mandato_options: Dict[str, int] = {
    f"{m.get('nome_parlamentar') or 'Sem nome'} (ID {m.get('id')})": m.get("id")
    for m in mandatos
    if m.get("id") is not None
}
mandato_label_by_id: Dict[int, str] = {v: k for k, v in mandato_options.items()}

search = st.text_input("Pesquisar por nome ou e-mail")
selected_permissions = st.multiselect(
    "Filtrar por permissão",
    options=api.permission_levels(),
    default=api.permission_levels(),
)


def _matches(user: Dict[str, Any]) -> bool:
    if selected_permissions and user.get("permission_level") not in selected_permissions:
        return False
    if search:
        haystack = f"{user.get('email','')} {user.get('first_name','')} {user.get('last_name','')}".lower()
        if search.lower() not in haystack:
            return False
    return True


filtered = [u for u in users if _matches(u)]
st.write(f"{len(filtered)} usuários encontrados.")

table_rows = [
    {
        "Nome": f"{u.get('first_name','')} {u.get('last_name','')}".strip() or "—",
        "Email": u.get("email"),
        "Permissão": u.get("permission_level"),
        "Ativo": u.get("is_active"),
        "Mandatos": ", ".join(m.get("nome_parlamentar") or "-" for m in u.get("mandato", [])),
    }
    for u in filtered
]

if table_rows:
    st.dataframe(pd.DataFrame(table_rows), hide_index=True, use_container_width=True)
else:
    st.info("Nenhum usuário com os filtros atuais.")

with st.expander("✏️ Editar usuário", expanded=False):
    options = [u["email"] for u in filtered]
    if not options:
        st.info("Nenhum usuário disponível para edição.")
    else:
        selected_email = st.selectbox("Selecione o usuário", options)
        user = next(u for u in users if u["email"] == selected_email)
        with st.form(f"edit-user-{user['id']}"):
            email = st.text_input("Email", user.get("email") or "")
            first_name = st.text_input("Nome", user.get("first_name") or "")
            last_name = st.text_input("Sobrenome", user.get("last_name") or "")
            phone = st.text_input("Telefone", user.get("phone") or "")
            role = st.text_input("Cargo interno", user.get("role") or "")
            permission = st.selectbox(
                "Permissão",
                options=api.permission_levels(),
                index=api.permission_levels().index(user.get("permission_level", "User")),
            )
            is_active = st.checkbox("Usuário ativo", value=bool(user.get("is_active", True)))
            lgpd_check = st.checkbox("Aceite LGPD", value=bool(user.get("lgpd_check", True)))
            password = st.text_input("Definir nova senha (opcional)", type="password")

            current_mandato_labels: List[str] = []
            for mandato_data in user.get("mandato", []) or []:
                mid = mandato_data.get("id")
                if mid is None:
                    continue
                label = mandato_label_by_id.get(mid)
                if not label:
                    label = f"{mandato_data.get('nome_parlamentar') or 'Sem nome'} (ID {mid})"
                    mandato_options[label] = mid
                    mandato_label_by_id[mid] = label
                current_mandato_labels.append(label)

            selected_mandatos_edit = st.multiselect(
                "Mandatos associados",
                options=list(mandato_options.keys()),
                default=current_mandato_labels,
                key=f"mandatos-edit-{user['id']}"
            )

            submitted = st.form_submit_button("Salvar alterações")
            if submitted:
                payload: Dict[str, Any] = {}
                if email != user.get("email"):
                    payload["email"] = email or None
                if first_name != user.get("first_name"):
                    payload["first_name"] = first_name or None
                if last_name != user.get("last_name"):
                    payload["last_name"] = last_name or None
                if phone != user.get("phone"):
                    payload["phone"] = phone or None
                if role != user.get("role"):
                    payload["role"] = role or None
                if permission != user.get("permission_level"):
                    payload["permission_level"] = permission
                if is_active != user.get("is_active"):
                    payload["is_active"] = is_active
                if lgpd_check != user.get("lgpd_check"):
                    payload["lgpd_check"] = lgpd_check
                if password:
                    payload["password"] = password
                payload["mandato"] = [
                    {"id": mandato_options[label]} for label in selected_mandatos_edit
                ]

                if not payload:
                    st.info("Nenhuma alteração detectada.")
                else:
                    if ui.call_api(api.update_user, user["id"], payload) is not None:
                        st.success("Usuário atualizado com sucesso.")
                        st.rerun()

with st.expander("➕ Adicionar novo usuário", expanded=False):
    with st.form("create-user-form"):
        email = st.text_input("Email")
        first_name = st.text_input("Nome")
        last_name = st.text_input("Sobrenome")
        phone = st.text_input("Telefone", "(11) 99999-9999")
        role = st.text_input("Cargo interno", "staff")
        permission = st.selectbox("Permissão", options=api.permission_levels(), index=0)
        password = st.text_input("Senha inicial", type="password")
        selected_existing = st.multiselect(
            "Associar mandatos existentes",
            options=list(mandato_options.keys()),
        )
        submitted = st.form_submit_button("Criar usuário")
        if submitted:
            if not email or not password:
                st.error("Email e senha são obrigatórios.")
            else:
                payload: Dict[str, Any] = {
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone": phone,
                    "role": role,
                    "permission_level": permission,
                    "lgpd_check": True,
                    "password": password,
                }
                if selected_existing:
                    payload["mandato"] = [{"id": mandato_options[label]} for label in selected_existing]
                if ui.call_api(api.create_user, payload) is not None:
                    st.success("Usuário criado com sucesso.")
                    st.rerun()

with st.expander("🗑️ Remover usuário", expanded=False):
    delete_options = [u["email"] for u in filtered if u.get("email") != admin_session.user.get("email")]
    if not delete_options:
        st.info("Nenhum usuário disponível para remoção.")
    else:
        delete_email = st.selectbox("Selecione o usuário para remover", delete_options)
        confirm = st.checkbox("Confirmo a remoção permanente", key="confirm-delete")
        if st.button("Remover usuário", use_container_width=False, disabled=not confirm):
            target = next(u for u in users if u["email"] == delete_email)
            if ui.call_api(api.delete_user, target["id"]) is not None:
                st.success("Usuário removido com sucesso.")
                st.rerun()

with st.expander("📧 Enviar emails de redefinição de senha", expanded=False):
    st.write("Envie emails de redefinição de senha para usuários selecionados.")
    
    # Template selector
    template_option = st.selectbox(
        "Template de email",
        ["password_reset", "bubble_import_password_reset"],
        format_func=lambda x: "Esqueci a Senha (padrão)" if x == "password_reset" else "Importação Bubble (boas-vindas)",
        key="email_template"
    )
    
    send_mode = st.radio(
        "Modo de envio",
        ["Usuários filtrados na página atual", "Usuários específicos", "⚠️ TODOS os usuários ativos"],
        key="send_mode"
    )
    
    selected_users = []
    
    if send_mode == "Usuários específicos":
        email_options = [u["email"] for u in filtered]
        if not email_options:
            st.info("Nenhum usuário disponível.")
        else:
            selected_emails = st.multiselect(
                "Selecione os usuários",
                options=email_options,
                key="selected_emails_for_reset"
            )
            selected_users = [u for u in users if u["email"] in selected_emails]
            
            if selected_users:
                st.info(f"✉️ {len(selected_users)} usuário(s) selecionado(s).")
            
    elif send_mode == "Usuários filtrados na página atual":
        selected_users = filtered
        if selected_users:
            st.info(f"✉️ {len(selected_users)} usuário(s) serão incluídos (baseado nos filtros atuais).")
        else:
            st.warning("Nenhum usuário corresponde aos filtros atuais.")
            
    else:  # Todos os usuários
        st.error(f"⚠️ **ATENÇÃO**: Isso enviará emails para **TODOS** os {total_users} usuários ativos no sistema!")
        st.warning("Esta operação não pode ser desfeita. Tenha certeza absoluta antes de continuar.")
    
    # Disable button if no users selected (except for "all" mode)
    can_send = (
        send_mode == "⚠️ TODOS os usuários ativos" or 
        (selected_users and len(selected_users) > 0)
    )
    
    confirm_send = st.checkbox("Confirmo o envio dos emails", key="confirm-send-emails")
    
    if st.button("📤 Enviar emails de redefinição", disabled=not (confirm_send and can_send), use_container_width=True):
        with st.spinner("Enviando emails..."):
            try:
                if send_mode == "⚠️ TODOS os usuários ativos":
                    # Send to all users using special "all" keyword
                    response = ui.call_api(api.send_password_reset_emails, user_ids=None, emails=["all"], template=template_option)
                elif send_mode == "Usuários filtrados na página atual":
                    # Send to filtered users
                    user_ids = [u["id"] for u in selected_users]
                    response = ui.call_api(api.send_password_reset_emails, user_ids=user_ids, emails=None, template=template_option)
                else:
                    # Send to specific users
                    emails = [u["email"] for u in selected_users]
                    response = ui.call_api(api.send_password_reset_emails, user_ids=None, emails=emails, template=template_option)
                
                if response:
                    sent = response.get("sent", 0)
                    failed = response.get("failed", 0)
                    
                    if failed == 0:
                        st.success(f"✅ {sent} emails enviados com sucesso!")
                    else:
                        st.warning(f"⚠️ {sent} enviados, {failed} falharam.")
                    
                    # Show details
                    show_details = st.checkbox("Mostrar detalhes", key="show_email_details")
                    if show_details:
                        details = response.get("details", [])
                        for detail in details:
                            status_emoji = "✅" if detail.get("status") == "sent" else "❌"
                            email = detail.get("email", "N/A")
                            error = detail.get("error", "")
                            error_msg = f" - {error}" if error else ""
                            st.write(f"{status_emoji} {email}{error_msg}")
            except Exception as e:
                st.error(f"Erro ao enviar emails: {str(e)}")

