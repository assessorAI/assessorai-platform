from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from collections import defaultdict

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from ..db.models import (
    AuditLog,
    Mandato as MandatoORM,
    User as UserORM,
    AnalyticsMetric,
)
from .analytics_helpers import (
    get_funcionalidade_from_event,
    calculate_risk_level,
    MandatoStatusEnum,
)


def get_month_start(dt: datetime) -> datetime:
    """Return first day of month at 00:00:00"""
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_ultimo_login(
    session: Session, 
    entity_type: str, 
    entity_id: int
) -> Optional[datetime]:
    """
    Get last login timestamp for mandato (any user) or user (specific).
    
    Args:
        entity_type: 'mandato' or 'user'
        entity_id: ID of the entity
    
    Returns:
        DateTime of last login or None if never logged in
    """
    stmt = select(AuditLog.created_at).where(
        AuditLog.event_type == "auth:login"
    )
    
    if entity_type == "user":
        stmt = stmt.where(AuditLog.actor_user_id == entity_id)
    elif entity_type == "mandato":
        stmt = stmt.where(AuditLog.actor_mandato_id == entity_id)
    else:
        raise ValueError(f"Invalid entity_type: {entity_type}")
    
    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(1)
    
    result = session.scalar(stmt)
    return result


def count_logs_by_period(
    session: Session,
    entity_type: str,
    entity_id: int,
    days: int,
) -> int:
    """Count audit logs in the last N days"""
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    
    stmt = select(func.count(AuditLog.id)).where(
        AuditLog.created_at >= cutoff
    )
    
    if entity_type == "user":
        stmt = stmt.where(AuditLog.actor_user_id == entity_id)
    elif entity_type == "mandato":
        stmt = stmt.where(AuditLog.actor_mandato_id == entity_id)
    
    return session.scalar(stmt) or 0


def count_logs_by_funcionalidade(
    session: Session,
    entity_type: str,
    entity_id: int,
    days: Optional[int] = None,
) -> Dict[str, int]:
    """
    Count logs grouped by funcionalidade.
    
    Args:
        days: If provided, only count last N days. If None, count all time.
    
    Returns:
        {"expert_pl": 10, "oficios": 5, ...}
    """
    stmt = select(AuditLog.event_type)
    
    if entity_type == "user":
        stmt = stmt.where(AuditLog.actor_user_id == entity_id)
    elif entity_type == "mandato":
        stmt = stmt.where(AuditLog.actor_mandato_id == entity_id)
    
    if days:
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        stmt = stmt.where(AuditLog.created_at >= cutoff)
    
    results = session.execute(stmt).scalars().all()
    
    # Map event_types to funcionalidades and count
    func_counts = defaultdict(int)
    for event_type in results:
        func_name = get_funcionalidade_from_event(event_type)
        func_counts[func_name] += 1
    
    return dict(func_counts)


def calculate_mandato_status(
    session: Session,
    mandato_id: int,
    reference_month: datetime,
) -> str:
    """
    Determine if mandato is 'ativo' or 'inativo' for given month.
    
    Rules:
        - Created in reference month -> ativo
        - Has any log in reference month -> ativo
        - Otherwise -> inativo
    """
    # Get mandato
    mandato = session.get(MandatoORM, mandato_id)
    if not mandato:
        return MandatoStatusEnum.INATIVO.value
    
    # Check if created in reference month
    if mandato.created_at:
        mandato_month = get_month_start(mandato.created_at)
        ref_month = get_month_start(reference_month)
        if mandato_month == ref_month:
            return MandatoStatusEnum.ATIVO.value
    
    # Check if has logs in reference month
    month_start = get_month_start(reference_month)
    month_end = (month_start + timedelta(days=32)).replace(day=1)  # Next month start
    
    log_count = session.scalar(
        select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.actor_mandato_id == mandato_id,
                AuditLog.created_at >= month_start,
                AuditLog.created_at < month_end,
            )
        )
    )
    
    if log_count and log_count > 0:
        return MandatoStatusEnum.ATIVO.value
    
    return MandatoStatusEnum.INATIVO.value


def calculate_user_status(
    session: Session,
    user_id: int,
    reference_month: datetime,
) -> str:
    """Same logic as mandato but for individual user"""
    # Check if has logs in reference month
    month_start = get_month_start(reference_month)
    month_end = (month_start + timedelta(days=32)).replace(day=1)
    
    log_count = session.scalar(
        select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.actor_user_id == user_id,
                AuditLog.created_at >= month_start,
                AuditLog.created_at < month_end,
            )
        )
    )
    
    if log_count and log_count > 0:
        return MandatoStatusEnum.ATIVO.value
    
    return MandatoStatusEnum.INATIVO.value


def calculate_metrics_for_entity(
    session: Session,
    entity_type: str,
    entity_id: int,
    reference_date: datetime,
) -> AnalyticsMetric:
    """
    Calculate all metrics for a mandato or user at given reference date.
    
    Returns:
        AnalyticsMetric instance (not committed to DB)
    """
    # Último login
    ultimo_login = get_ultimo_login(session, entity_type, entity_id)
    
    # Dias sem login
    dias_sem_login = None
    if ultimo_login:
        # Ensure both datetimes are naive for comparison
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        # Handle both naive and aware datetimes from database
        ultimo_login_naive = ultimo_login.replace(tzinfo=None) if ultimo_login.tzinfo else ultimo_login
        delta = now_naive - ultimo_login_naive
        dias_sem_login = delta.days
    
    # Risk level
    risk_level = calculate_risk_level(dias_sem_login)
    
    # Status (ativo/inativo)
    if entity_type == "mandato":
        status = calculate_mandato_status(session, entity_id, reference_date)
    else:
        status = calculate_user_status(session, entity_id, reference_date)
    
    # Log counts
    logs_7d = count_logs_by_period(session, entity_type, entity_id, 7)
    logs_30d = count_logs_by_period(session, entity_type, entity_id, 30)
    logs_total = count_logs_by_period(session, entity_type, entity_id, 365*10)  # All time
    
    # Funcionalidades breakdown
    funcionalidades_count = count_logs_by_funcionalidade(
        session, entity_type, entity_id, days=30
    )
    
    return AnalyticsMetric(
        entity_type=entity_type,
        entity_id=entity_id,
        reference_date=get_month_start(reference_date),
        calculated_at=datetime.now(timezone.utc).replace(tzinfo=None),
        status=status,
        risk_level=risk_level,
        ultimo_login=ultimo_login,
        dias_sem_login=dias_sem_login,
        logs_7d=logs_7d,
        logs_30d=logs_30d,
        logs_total=logs_total,
        funcionalidades_count=funcionalidades_count,
    )


def refresh_metrics_for_entity(
    session: Session,
    entity_type: str,
    entity_id: int,
    reference_date: Optional[datetime] = None,
) -> AnalyticsMetric:
    """
    Calculate and persist metrics for entity.
    Upserts into analytics_metrics table.
    """
    if reference_date is None:
        reference_date = datetime.now(timezone.utc).replace(tzinfo=None)
    
    ref_month = get_month_start(reference_date)
    
    # Check if exists
    existing = session.scalar(
        select(AnalyticsMetric).where(
            and_(
                AnalyticsMetric.entity_type == entity_type,
                AnalyticsMetric.entity_id == entity_id,
                AnalyticsMetric.reference_date == ref_month,
            )
        )
    )
    
    # Calculate fresh metrics
    new_metrics = calculate_metrics_for_entity(
        session, entity_type, entity_id, reference_date
    )
    
    if existing:
        # Update existing
        existing.calculated_at = new_metrics.calculated_at
        existing.status = new_metrics.status
        existing.risk_level = new_metrics.risk_level
        existing.ultimo_login = new_metrics.ultimo_login
        existing.dias_sem_login = new_metrics.dias_sem_login
        existing.logs_7d = new_metrics.logs_7d
        existing.logs_30d = new_metrics.logs_30d
        existing.logs_total = new_metrics.logs_total
        existing.funcionalidades_count = new_metrics.funcionalidades_count
        session.commit()
        return existing
    else:
        # Insert new
        session.add(new_metrics)
        session.commit()
        session.refresh(new_metrics)
        return new_metrics


def refresh_all_metrics(
    session: Session,
    reference_date: Optional[datetime] = None,
) -> Tuple[int, int]:
    """
    Refresh metrics for ALL mandatos and users.
    
    Returns:
        (mandatos_updated, users_updated)
    """
    if reference_date is None:
        reference_date = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Get all mandatos
    mandatos = session.execute(select(MandatoORM.id)).scalars().all()
    mandatos_count = 0
    for mandato_id in mandatos:
        refresh_metrics_for_entity(session, "mandato", mandato_id, reference_date)
        mandatos_count += 1
    
    # Get all users
    users = session.execute(select(UserORM.id)).scalars().all()
    users_count = 0
    for user_id in users:
        refresh_metrics_for_entity(session, "user", user_id, reference_date)
        users_count += 1
    
    return (mandatos_count, users_count)
