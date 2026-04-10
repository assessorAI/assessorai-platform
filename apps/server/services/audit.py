from __future__ import annotations

import json
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from ..db.models import AuditLog
from ..db.session import get_session

_request_id_ctx: ContextVar[str] = ContextVar("audit_request_id", default="")


def set_request_id(request_id: str) -> None:
    _request_id_ctx.set(request_id)


def get_request_id() -> str:
    rid = _request_id_ctx.get()
    if not rid:
        rid = uuid.uuid4().hex
        _request_id_ctx.set(rid)
    return rid


class AuditLogger:
    """Service responsible for recording audit events."""

    def __init__(self, session: Session):
        self.session = session

    def log(
        self,
        *,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        response: Optional[Dict[str, Any]] = None,
        subject_id: Optional[str] = None,
        actor_user_id: Optional[int] = None,
        actor_mandato_id: Optional[int] = None,
        actor_permission_level: Optional[str] = None,
        notes: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLog:
        serializable_payload = json.loads(json.dumps(payload or {}, default=str))
        serializable_response = json.loads(json.dumps(response or {}, default=str)) if response else None

        log_entry = AuditLog(
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            event_type=event_type,
            subject_id=subject_id,
            actor_user_id=actor_user_id,
            actor_mandato_id=actor_mandato_id,
            actor_permission_level=actor_permission_level,
            request_id=request_id or get_request_id(),
            payload=serializable_payload,
            response=serializable_response,
            notes=notes,
        )
        self.session.add(log_entry)
        self.session.commit()
        self.session.refresh(log_entry)
        return log_entry


def get_audit_logger(session: Session = Depends(get_session)) -> AuditLogger:
    return AuditLogger(session=session)
