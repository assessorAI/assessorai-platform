from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import streamlit as st


ADMIN_TOKEN_KEY = "admin_api_token"
ADMIN_USER_KEY = "admin_api_user"


@dataclass
class AdminSession:
    token: Optional[str]
    user: Optional[Dict[str, Any]]

    @property
    def is_authenticated(self) -> bool:
        return bool(self.token and self.user)

    @property
    def permission_level(self) -> Optional[str]:
        if not self.user:
            return None
        return self.user.get("permission_level")

    @property
    def is_admin(self) -> bool:
        return self.permission_level == "Admin"


def get_session() -> AdminSession:
    return AdminSession(
        token=st.session_state.get(ADMIN_TOKEN_KEY),
        user=st.session_state.get(ADMIN_USER_KEY),
    )


def set_session(token: str, user: Dict[str, Any]) -> None:
    st.session_state[ADMIN_TOKEN_KEY] = token
    st.session_state[ADMIN_USER_KEY] = user


def clear_session() -> None:
    st.session_state.pop(ADMIN_TOKEN_KEY, None)
    st.session_state.pop(ADMIN_USER_KEY, None)
