from pathlib import Path
import sys

import streamlit as st

try:
    from client.admin import api, state, ui
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from client.admin import api, state, ui  # type: ignore  # noqa: E402

st.set_page_config(
    page_title="Assessor.AI Admin",
    page_icon="🛠️",
    layout="wide",
)

ui.render_sidebar()

st.title("Assessor.AI • Console Administrativo")
st.caption(f"Backend: {api.get_base_url()}")

session = state.get_session()

if session.is_authenticated:
    if api.is_token_expired():
        st.warning("Sessão expirada. Faça login novamente.")
        api.logout()
        st.rerun()
    else:
        st.success(f"Logado como {session.user.get('email')}")
        if st.button("Sair", use_container_width=False):
            api.logout()
            st.rerun()
else:
    st.info("Informe suas credenciais administrativas para acessar o console.")
    with st.form("admin-login"):
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        if submitted:
            if not email or not password:
                st.error("Email e senha são obrigatórios.")
            else:
                try:
                    api.login(email, password)
                except api.APIError as err:
                    st.error(str(err))
                except RuntimeError as err:
                    st.warning(str(err))
                else:
                    st.success("Login realizado com sucesso.")
                    st.rerun()

st.write("---")
st.markdown(
    """
**Dica:** configure o endpoint da API via `ASSESSORAI_API_URL` ou `.streamlit/config.toml` (`[api] base_url = "https://..."`).
Caso não seja definido, usamos `http://localhost:8000`.
"""
)
