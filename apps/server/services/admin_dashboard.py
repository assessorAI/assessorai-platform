from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Sequence

from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..db.models import (
    AuthToken as AuthTokenORM,
    Mandato as MandatoORM,
    User as UserORM,
    UserActivationToken as UserActivationTokenORM,
)
from ..models import (
    AdminDashboardSummary,
    AdminHealthCheck,
    AdminHealthResponse,
    AdminMandatoMetrics,
    AdminTokenMetrics,
    AdminUserMetrics,
)
from .sendgrid_service import get_email_service


MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "db" / "migrations"
HEALTH_STATUS_ORDER = {"ok": 0, "warning": 1, "error": 2}


def _safe_scalar(session: Session, statement) -> int:
    value = session.scalar(statement)
    return int(value or 0)


def collect_dashboard_summary(session: Session) -> AdminDashboardSummary:
    total_users = _safe_scalar(session, select(func.count(UserORM.id)))
    active_users = _safe_scalar(
        session, select(func.count(UserORM.id)).where(UserORM.is_active.is_(True))
    )
    inactive_users = total_users - active_users

    permission_counts: Dict[str, int] = defaultdict(int)
    for level, count in session.execute(
        select(UserORM.permission_level, func.count(UserORM.id)).group_by(UserORM.permission_level)
    ):
        permission_counts[str(level)] = int(count or 0)

    total_mandatos = _safe_scalar(session, select(func.count(MandatoORM.id)))
    mandatos_with_users = _safe_scalar(
        session,
        select(func.count(func.distinct(MandatoORM.id))).join(MandatoORM.users),
    )
    mandatos_without_users = max(total_mandatos - mandatos_with_users, 0)

    active_tokens = _safe_scalar(
        session, select(func.count(AuthTokenORM.id)).where(AuthTokenORM.expires_at > datetime.now(timezone.utc).replace(tzinfo=None))
    )
    expiring_tokens = _safe_scalar(
        session,
        select(func.count(AuthTokenORM.id)).where(
            AuthTokenORM.expires_at.between(datetime.now(timezone.utc).replace(tzinfo=None), datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24))
        ),
    )

    pending_invitations = _safe_scalar(
        session,
        select(func.count(UserActivationTokenORM.id)).where(
            UserActivationTokenORM.used.is_(False), UserActivationTokenORM.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)
        ),
    )

    users_metrics = AdminUserMetrics(
        total=total_users,
        active=active_users,
        inactive=inactive_users,
        by_permission=dict(permission_counts),
    )
    mandatos_metrics = AdminMandatoMetrics(
        total=total_mandatos,
        with_users=mandatos_with_users,
        without_users=mandatos_without_users,
    )
    token_metrics = AdminTokenMetrics(active=active_tokens, expiring_within_24h=expiring_tokens)

    return AdminDashboardSummary(
        users=users_metrics,
        mandatos=mandatos_metrics,
        tokens=token_metrics,
        pending_invitations=pending_invitations,
    )


def _check_database(session: Session) -> AdminHealthCheck:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        return AdminHealthCheck(name="database", status="error", detail=str(exc))
    return AdminHealthCheck(name="database", status="ok", detail="Connection healthy")


def _collect_migration_facts(session: Session) -> Sequence[str]:
    try:
        rows = session.execute(text("SELECT filename FROM schema_migrations"))
    except SQLAlchemyError:
        return []
    return [row[0] for row in rows]


def _check_migrations(session: Session) -> AdminHealthCheck:
    applied = set(_collect_migration_facts(session))
    available = sorted(path.name for path in MIGRATIONS_DIR.glob("*.sql"))

    missing_table = False
    if not applied and available:
        # Ensure we differentiate between empty table and missing table
        try:
            session.execute(text("SELECT COUNT(*) FROM schema_migrations"))
        except SQLAlchemyError:
            missing_table = True

    pending = [name for name in available if name not in applied]
    extra = [name for name in applied if name not in available]

    if missing_table:
        return AdminHealthCheck(
            name="migrations",
            status="warning",
            detail="schema_migrations table missing; run manage_db.py to initialise.",
            data={"available": available},
        )

    if pending:
        return AdminHealthCheck(
            name="migrations",
            status="warning",
            detail="Pending migrations detected.",
            data={"pending": pending, "applied": sorted(applied)},
        )

    if extra:
        return AdminHealthCheck(
            name="migrations",
            status="warning",
            detail="Applied migrations not found on disk.",
            data={"extra": extra},
        )

    return AdminHealthCheck(
        name="migrations",
        status="ok",
        detail="All migrations applied.",
        data={"available": available},
    )


def _check_google_credentials() -> AdminHealthCheck:
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    cred_b64 = os.getenv("GOOGLE_APPLICATION_BASE64")

    if cred_path:
        if Path(cred_path).exists():
            return AdminHealthCheck(
                name="google_credentials",
                status="ok",
                detail=f"Credentials file available at {cred_path}.",
            )
        return AdminHealthCheck(
            name="google_credentials",
            status="warning",
            detail=f"GOOGLE_APPLICATION_CREDENTIALS set but file not found at {cred_path}.",
        )

    if cred_b64:
        return AdminHealthCheck(
            name="google_credentials",
            status="ok",
            detail="Credentials provided via GOOGLE_APPLICATION_BASE64.",
        )

    return AdminHealthCheck(
        name="google_credentials",
        status="warning",
        detail="Google credentials not configured.",
    )


def _check_email_service() -> AdminHealthCheck:
    email_service = get_email_service()
    if email_service.is_configured:
        return AdminHealthCheck(name="email", status="ok", detail="SendGrid configured.")
    return AdminHealthCheck(
        name="email",
        status="warning",
        detail="SendGrid not configured; transactional emails disabled.",
    )


def collect_health_snapshot(session: Session) -> AdminHealthResponse:
    checks = [
        _check_database(session),
        _check_migrations(session),
        _check_google_credentials(),
        _check_email_service(),
    ]
    worst_status = max((HEALTH_STATUS_ORDER.get(check.status, 1) for check in checks), default=0)
    reverse_map = {v: k for k, v in HEALTH_STATUS_ORDER.items()}
    overall = reverse_map.get(worst_status, "warning")
    return AdminHealthResponse(overall_status=overall, checks=checks)
