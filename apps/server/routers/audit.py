from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import AuditLog
from ..db.session import get_session
from ..models import AuditLogOut
from ..routers.deps import require_admin_user

router = APIRouter(prefix="/admin/audit", tags=["admin/audit"])


@router.get("/", response_model=List[AuditLogOut])
async def list_audit_logs(
    *,
    session: Session = Depends(get_session),
    current_admin= require_admin_user,
    event_type: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    mandato_id: Optional[int] = Query(None),
    from_dt: Optional[datetime] = Query(None, alias="from"),
    to_dt: Optional[datetime] = Query(None, alias="to"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> List[AuditLogOut]:
    statement = select(AuditLog).order_by(AuditLog.created_at.desc())
    if event_type:
        statement = statement.where(AuditLog.event_type == event_type)
    if user_id:
        statement = statement.where(AuditLog.actor_user_id == user_id)
    if mandato_id:
        statement = statement.where(AuditLog.actor_mandato_id == mandato_id)
    if from_dt:
        statement = statement.where(AuditLog.created_at >= from_dt)
    if to_dt:
        statement = statement.where(AuditLog.created_at <= to_dt)
    statement = statement.offset(offset).limit(limit)
    results = session.execute(statement).scalars().all()
    return [_to_schema(r) for r in results]


@router.get("/{log_id}", response_model=AuditLogOut)
async def get_audit_log(
    log_id: int,
    session: Session = Depends(get_session),
    current_admin= require_admin_user,
) -> AuditLogOut:
    log_entry = session.get(AuditLog, log_id)
    if not log_entry:
        raise HTTPException(status_code=404, detail="Log não encontrado")
    return _to_schema(log_entry)


def _to_schema(log: AuditLog) -> AuditLogOut:
    payload = log.payload
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            payload = {"raw": payload}
    
    response = log.response
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            response = {"raw": response}
    
    return AuditLogOut(
        id=log.id,
        created_at=log.created_at,
        event_type=log.event_type,
        subject_id=log.subject_id,
        actor_user_id=log.actor_user_id,
        actor_mandato_id=log.actor_mandato_id,
        actor_permission_level=log.actor_permission_level,
        request_id=log.request_id,
        payload=payload,
        response=response,
        notes=log.notes,
    )
