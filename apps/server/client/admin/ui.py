from __future__ import annotations

from typing import Any, Callable, Optional, TypeVar

import streamlit as st

from . import api, state

T = TypeVar("T")


def render_sidebar() -> None:
    session = state.get_session()
    st.sidebar.title("Console Administrativo")
    st.sidebar.caption(f"API: {api.get_base_url()}")
    if session.is_authenticated:
        st.sidebar.success(session.user.get("email", ""))
        if st.sidebar.button("Sair", use_container_width=True):
            api.logout()
            st.rerun()
    else:
        st.sidebar.info("Faça login na página inicial.")


def require_admin_session() -> state.AdminSession:
    session = state.get_session()
    if not session.is_authenticated:
        st.error("Faça login na página inicial antes de acessar esta página.")
        st.stop()
    if not session.is_admin:
        st.error("Apenas administradores podem acessar esta área.")
        st.stop()
    return session


def call_api(fn: Callable[..., T], *args, **kwargs) -> Optional[T]:
    try:
        return fn(*args, **kwargs)
    except api.APIError as err:
        st.error(str(err))
    except RuntimeError as err:
        st.warning(str(err))
    except ValueError as err:
        st.warning(str(err))
    return None
