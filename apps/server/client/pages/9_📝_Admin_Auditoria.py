from __future__ import annotations

import datetime as dt
from pathlib import Path
import sys
from typing import Dict, Optional

import pandas as pd
import streamlit as st

try:
    from client.admin import api, ui
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from client.admin import api, ui  # type: ignore  # noqa: E402


FILTER_SESSION_KEY = "admin_audit_filters"
DEFAULT_LIMIT = 100


def _init_filter_state() -> None:
    if FILTER_SESSION_KEY not in st.session_state:
        st.session_state[FILTER_SESSION_KEY] = {
            "event_type": "",
            "mandato": "",
            "date_from": None,
            "date_to": None,
            "limit": DEFAULT_LIMIT,
        }


def _to_iso(date_value) -> Optional[str]:
    if not date_value:
        return None
    try:
        return date_value.isoformat()
    except AttributeError:
        return None


def _normalize_date(value) -> Optional[dt.date]:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    return None


ui.render_sidebar()
session = ui.require_admin_session()

st.title("Admin • Auditoria de Logs")

_init_filter_state()
filters: Dict[str, object] = st.session_state[FILTER_SESSION_KEY]

with st.sidebar:
    st.subheader("Filtros")
    with st.form("audit-filter-form"):
        event_type_filter = st.text_input(
            "Tipo de operação",
            value=filters.get("event_type", "") or "",
            placeholder="oficio.generate.success",
        )
        mandato_filter = st.text_input(
            "Mandato (ID)",
            value=filters.get("mandato", "") or "",
        )
        col_date_from, col_date_to = st.columns(2)
        date_from = col_date_from.date_input(
            "De",
            value=_normalize_date(filters.get("date_from")),
        )
        date_to = col_date_to.date_input(
            "Até",
            value=_normalize_date(filters.get("date_to")),
        )
        limit = st.slider(
            "Quantidade de eventos",
            min_value=20,
            max_value=200,
            step=20,
            value=int(filters.get("limit") or DEFAULT_LIMIT),
            help="Quantidade máxima de registros retornados pela API",
        )
        submitted = st.form_submit_button("Aplicar filtros")

    if submitted:
        st.session_state[FILTER_SESSION_KEY] = {
            "event_type": event_type_filter.strip(),
            "mandato": mandato_filter.strip(),
            "date_from": date_from if isinstance(date_from, dt.date) else None,
            "date_to": date_to if isinstance(date_to, dt.date) else None,
            "limit": limit,
        }
        filters = st.session_state[FILTER_SESSION_KEY]

mandato_id = None
mandato_raw = str(filters.get("mandato", "")).strip()
if mandato_raw.isdigit():
    mandato_id = int(mandato_raw)

payload = ui.call_api(
    api.fetch_audit_logs,
    event_type=str(filters.get("event_type") or "") or None,
    mandato_id=mandato_id,
    from_dt=_to_iso(filters.get("date_from")),
    to_dt=_to_iso(filters.get("date_to")),
    limit=int(filters.get("limit") or DEFAULT_LIMIT),
    offset=0,
)

if not payload:
    st.info("Nenhum evento encontrado para os filtros selecionados.")
    st.stop()

df = pd.DataFrame(payload)
df["created_at_dt"] = pd.to_datetime(df.get("created_at"), errors="coerce", utc=True)

if "created_at_dt" in df and isinstance(df["created_at_dt"].dtype, pd.DatetimeTZDtype):
    df["created_at_dt"] = df["created_at_dt"].dt.tz_convert(None)

events_total = len(df)
stats = (
    df.groupby("event_type", dropna=False)
    .agg(total=("id", "count"), ultimo_evento=("created_at_dt", "max"))
    .reset_index()
    .sort_values("total", ascending=False)
)
stats["event_type"] = stats["event_type"].fillna("—")
stats["percentual"] = (stats["total"] / events_total * 100).round(1)

stats_display = stats.copy()
stats_display["percentual"] = stats_display["percentual"].map(
    lambda value: f"{value:.1f}%" if pd.notna(value) else "—"
)
stats_display["ultimo_evento"] = stats_display["ultimo_evento"].dt.strftime("%Y-%m-%d %H:%M:%S")
stats_display["ultimo_evento"] = stats_display["ultimo_evento"].fillna("—")

col_total, col_types, col_mandatos = st.columns(3)
col_total.metric("Logs no intervalo", events_total)
col_types.metric("Tipos de operação", int(stats["event_type"].nunique()))
col_mandatos.metric(
    "Mandatos envolvidos",
    int(df["actor_mandato_id"].nunique()) if "actor_mandato_id" in df else 0,
)

st.subheader("Estatísticas por tipo de operação")
st.dataframe(
    stats_display.rename(columns={"event_type": "Tipo"}),
    use_container_width=True,
    hide_index=True,
)

chart_source = stats.set_index("event_type")["total"]
if not chart_source.empty:
    st.bar_chart(chart_source, height=240)

st.subheader("Eventos auditados")
df_display = df.drop(columns=["payload", "notes"], errors="ignore").copy()
if "created_at_dt" in df_display:
    df_display["created_at"] = df["created_at_dt"].dt.strftime("%Y-%m-%d %H:%M:%S")
df_display = df_display.drop(columns=["created_at_dt"], errors="ignore")
st.dataframe(df_display, use_container_width=True, hide_index=True)

selected_idx = st.selectbox(
    "Ver detalhes do log",
    options=["-"] + [str(row["id"]) for _, row in df.iterrows()],
)

if selected_idx and selected_idx != "-":
    detail = ui.call_api(api.fetch_audit_log, int(selected_idx))
    if detail:
        st.subheader(f"Log #{detail['id']}")
        st.write(f"Tipo: `{detail['event_type']}`")
        st.write(f"Criado em: {detail['created_at']}")
        col_actor, col_mandato = st.columns(2)
        col_actor.write(f"Usuário: {detail.get('actor_user_id') or '—'}")
        col_actor.write(f"Permissão: {detail.get('actor_permission_level') or '—'}")
        col_mandato.write(f"Mandato: {detail.get('actor_mandato_id') or '—'}")
        col_mandato.write(f"Request ID: {detail.get('request_id') or '—'}")
        st.write(f"Recurso afetado: {detail.get('subject_id') or '—'}")
        if detail.get("payload"):
            st.write("Payload")
            payload_value = detail["payload"]
            if isinstance(payload_value, dict):
                st.json(payload_value)
            else:
                st.write(payload_value)
        if detail.get("notes"):
            st.write("Notas")
            st.write(detail["notes"])
