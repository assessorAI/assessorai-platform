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

st.title("Admin • Health")

health = ui.call_api(api.fetch_health_snapshot)
if health is None:
    st.stop()

status = health.get("overall_status", "warning")
status_map = {
    "ok": ("✅", "Sistema saudável."),
    "warning": ("⚠️", "Alguns pontos precisam de atenção."),
    "error": ("❌", "Erros detectados."),
}
icon, message = status_map.get(status, ("ℹ️", "Estado desconhecido."))
st.subheader("Estado geral")
st.write(f"{icon} {message}")

rows = [
    {
        "Componente": check.get("name"),
        "Status": check.get("status"),
        "Detalhe": check.get("detail") or "",
        "Dados": ", ".join(
            f"{key}: {', '.join(values)}" if isinstance(values, list) else f"{key}: {values}"
            for key, values in (check.get("data") or {}).items()
        ),
    }
    for check in health.get("checks", [])
]

st.write("---")
st.subheader("Verificações detalhadas")
if rows:
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
else:
    st.info("Nenhuma verificação disponível.")

if st.button("Recarregar estado"):
    st.rerun()
