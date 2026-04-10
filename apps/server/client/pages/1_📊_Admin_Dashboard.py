from __future__ import annotations

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

st.title("Admin • Dashboard")

summary = ui.call_api(api.fetch_dashboard_summary)
if not summary:
    st.stop()

users = summary["users"]
mandatos = summary["mandatos"]
tokens = summary["tokens"]

col1, col2, col3 = st.columns(3)
col1.metric("Usuários", users["total"], delta=f"{users['active']} ativos")
col2.metric("Mandatos", mandatos["total"], delta=f"{mandatos['with_users']} com usuários")
col3.metric("Tokens ativos", tokens["active"], delta=f"{tokens['expiring_within_24h']} expiram < 24h")

st.write("---")
st.subheader("Distribuição de permissões")
perm_rows = [{"Permissão": level, "Quantidade": count} for level, count in users["by_permission"].items()]
if perm_rows:
    perm_df = pd.DataFrame(perm_rows).set_index("Permissão")
    st.bar_chart(perm_df)
else:
    st.info("Nenhum usuário cadastrado para exibir.")

st.write("---")
st.subheader("Convites pendentes")
st.metric("Tokens de ativação pendentes", summary["pending_invitations"])
