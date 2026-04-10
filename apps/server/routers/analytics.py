from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from collections import defaultdict

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from ..db.session import get_session
from ..db.models import (
    Mandato as MandatoORM,
    User as UserORM,
    AnalyticsMetric,
    AuditLog,
    mandato_user_link,
)
from ..models import (
    AnalyticsSummaryMandatos,
    AnalyticsTimeline,
    AnalyticsTimelineBucket,
    AnalyticsFuncionalidadesResponse,
    AnalyticsFuncionalidadeUso,
    AnalyticsEngagementList,
    AnalyticsMandatoMetrics,
    AnalyticsMandatoBasic,
    AnalyticsUserMetricsOut,
)
from ..services.analytics import (
    refresh_metrics_for_entity,
    refresh_all_metrics,
    get_month_start,
)
from ..services.analytics_helpers import get_funcionalidade_from_event
from ..services.csv_export import generate_csv_response
from .deps import require_admin_user

router = APIRouter(
    prefix="/admin/analytics",
    tags=["admin/analytics"],
)


@router.post("/refresh")
def refresh_metrics(
    *,
    session: Session = Depends(get_session),
    current_admin=require_admin_user,
    reference_month: Optional[str] = Query(None, description="YYYY-MM format"),
):
    """
    Trigger recalculation of all metrics.
    Use this when audit data changes or for backfilling historical months.
    """
    ref_date = None
    if reference_month:
        try:
            ref_date = datetime.strptime(reference_month, "%Y-%m")
        except ValueError:
            raise HTTPException(400, "Invalid date format. Use YYYY-MM")
    
    mandatos_count, users_count = refresh_all_metrics(session, ref_date)
    
    return {
        "message": "Metrics refreshed successfully",
        "mandatos_updated": mandatos_count,
        "users_updated": users_count,
        "reference_date": get_month_start(ref_date or datetime.now()).isoformat(),
    }


@router.get("/mandatos/summary", response_model=AnalyticsSummaryMandatos)
def get_mandatos_summary(
    *,
    session: Session = Depends(get_session),
    current_admin=require_admin_user,
    reference_month: Optional[str] = Query(None, description="YYYY-MM, defaults to current"),
):
    """
    Aggregate summary of all mandatos.
    Includes total, ativos, inativos, retention rate, and breakdowns.
    """
    # Parse reference month
    if reference_month:
        try:
            ref_date = datetime.strptime(reference_month, "%Y-%m")
        except ValueError:
            raise HTTPException(400, "Invalid date format. Use YYYY-MM")
    else:
        ref_date = datetime.now(timezone.utc).replace(tzinfo=None)
    
    ref_month = get_month_start(ref_date)
    
    # Get all mandatos
    mandatos = session.execute(select(MandatoORM)).scalars().all()
    total = len(mandatos)
    
    # Get metrics for reference month
    metrics = session.execute(
        select(AnalyticsMetric).where(
            and_(
                AnalyticsMetric.entity_type == "mandato",
                AnalyticsMetric.reference_date == ref_month,
            )
        )
    ).scalars().all()
    
    # If no metrics cached, calculate on-the-fly (slow)
    if not metrics:
        refresh_all_metrics(session, ref_date)
        metrics = session.execute(
            select(AnalyticsMetric).where(
                and_(
                    AnalyticsMetric.entity_type == "mandato",
                    AnalyticsMetric.reference_date == ref_month,
                )
            )
        ).scalars().all()
    
    # Count ativos/inativos
    ativos = sum(1 for m in metrics if m.status == "ativo")
    inativos = total - ativos
    taxa_retencao = (ativos / total * 100) if total > 0 else 0
    
    # Breakdowns - need to join with Mandato table
    por_cargo = defaultdict(int)
    por_uf = defaultdict(int)
    por_perfil = defaultdict(int)
    por_espectro = defaultdict(int)
    por_risco = defaultdict(int)
    
    for m in metrics:
        mandato = session.get(MandatoORM, m.entity_id)
        if mandato:
            if mandato.cargo_parlamentar:
                por_cargo[mandato.cargo_parlamentar] += 1
            if mandato.ue:
                por_uf[mandato.ue] += 1
            if mandato.perfil_parlamentar:
                por_perfil[mandato.perfil_parlamentar] += 1
            if mandato.espectro_politico:
                por_espectro[mandato.espectro_politico] += 1
        
        if m.risk_level:
            por_risco[m.risk_level] += 1
    
    return AnalyticsSummaryMandatos(
        total=total,
        ativos=ativos,
        inativos=inativos,
        taxa_retencao=round(taxa_retencao, 2),
        por_cargo=dict(por_cargo),
        por_uf=dict(por_uf),
        por_perfil=dict(por_perfil),
        por_espectro=dict(por_espectro),
        por_risco=dict(por_risco),
    )


@router.get("/mandatos/timeline", response_model=AnalyticsTimeline)
def get_mandatos_timeline(
    *,
    session: Session = Depends(get_session),
    current_admin=require_admin_user,
    period: str = Query("month", pattern="^(month|week)$"),
):
    """
    Timeline of mandato registrations.
    Groups by month or week.
    """
    # Get all mandatos with created_at
    stmt = select(MandatoORM.created_at).where(MandatoORM.created_at.isnot(None))
    created_dates = session.execute(stmt).scalars().all()
    
    # Group by period
    buckets = defaultdict(int)
    for dt in created_dates:
        if period == "month":
            key = dt.strftime("%Y-%m")
        else:  # week
            key = dt.strftime("%Y-W%U")
        buckets[key] += 1
    
    # Sort chronologically
    timeline = [
        AnalyticsTimelineBucket(period=k, count=v)
        for k, v in sorted(buckets.items())
    ]
    
    return AnalyticsTimeline(timeline=timeline)


@router.get("/mandatos/retention-timeline")
def get_retention_timeline(
    *,
    session: Session = Depends(get_session),
    current_admin=require_admin_user,
    months: int = Query(12, ge=1, le=36, description="Number of months to analyze"),
):
    """
    Historical retention rate per month.
    Shows how many mandatos were active each month.
    """
    results = []
    current = datetime.now(timezone.utc).replace(tzinfo=None)
    
    for i in range(months):
        ref_date = current - timedelta(days=30*i)
        ref_month = get_month_start(ref_date)
        
        # Get metrics for this month
        metrics = session.execute(
            select(AnalyticsMetric).where(
                and_(
                    AnalyticsMetric.entity_type == "mandato",
                    AnalyticsMetric.reference_date == ref_month,
                )
            )
        ).scalars().all()
        
        total_mandatos = session.scalar(select(func.count(MandatoORM.id)))
        ativos = sum(1 for m in metrics if m.status == "ativo")
        taxa = (ativos / total_mandatos * 100) if total_mandatos > 0 else 0
        
        results.append({
            "period": ref_month.strftime("%Y-%m"),
            "total_mandatos": total_mandatos,
            "ativos": ativos,
            "taxa_retencao": round(taxa, 2),
        })
    
    return {"timeline": list(reversed(results))}


@router.get("/funcionalidades", response_model=AnalyticsFuncionalidadesResponse)
def get_funcionalidades_uso(
    *,
    session: Session = Depends(get_session),
    current_admin=require_admin_user,
    mandato_id: Optional[int] = Query(None, description="Filter by mandato"),
    user_id: Optional[int] = Query(None, description="Filter by user"),
    period: str = Query("30d", pattern="^(7d|30d|all)$"),
):
    """
    Usage breakdown by funcionalidade.
    Can filter by mandato or user, and time period.
    """
    stmt = select(AuditLog.event_type)
    
    if mandato_id:
        stmt = stmt.where(AuditLog.actor_mandato_id == mandato_id)
    if user_id:
        stmt = stmt.where(AuditLog.actor_user_id == user_id)
    
    if period != "all":
        days = int(period.replace("d", ""))
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        stmt = stmt.where(AuditLog.created_at >= cutoff)
    
    event_types = session.execute(stmt).scalars().all()
    
    # Group by funcionalidade
    func_counts = defaultdict(int)
    for et in event_types:
        func = get_funcionalidade_from_event(et)
        func_counts[func] += 1
    
    total = sum(func_counts.values())
    
    funcionalidades = [
        AnalyticsFuncionalidadeUso(
            funcionalidade=k,
            count=v,
            percentage=round(v / total * 100, 2) if total > 0 else 0,
        )
        for k, v in sorted(func_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return AnalyticsFuncionalidadesResponse(
        total_logs=total,
        funcionalidades=funcionalidades,
    )


@router.get("/engagement/mandatos", response_model=AnalyticsEngagementList)
def get_mandatos_engagement(
    *,
    session: Session = Depends(get_session),
    current_admin=require_admin_user,
    risk_level: Optional[str] = Query(None, pattern="^(ok|baixo|medio|alto)$"),
    status: Optional[str] = Query(None, pattern="^(ativo|inativo)$"),
    reference_month: Optional[str] = Query(None, description="YYYY-MM"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    List mandatos with engagement metrics.
    Supports filtering by risk level and status.
    """
    if reference_month:
        try:
            ref_date = datetime.strptime(reference_month, "%Y-%m")
        except ValueError:
            raise HTTPException(400, "Invalid date format. Use YYYY-MM")
    else:
        ref_date = datetime.now(timezone.utc).replace(tzinfo=None)
    
    ref_month = get_month_start(ref_date)
    
    stmt = select(AnalyticsMetric).where(
        and_(
            AnalyticsMetric.entity_type == "mandato",
            AnalyticsMetric.reference_date == ref_month,
        )
    )
    
    if risk_level:
        stmt = stmt.where(AnalyticsMetric.risk_level == risk_level)
    if status:
        stmt = stmt.where(AnalyticsMetric.status == status)
    
    stmt = stmt.order_by(AnalyticsMetric.dias_sem_login.desc().nullslast())
    stmt = stmt.offset(offset).limit(limit)
    
    metrics = session.execute(stmt).scalars().all()
    
    mandatos_data = []
    for m in metrics:
        mandato = session.get(MandatoORM, m.entity_id)
        if mandato:
            mandatos_data.append(
                AnalyticsMandatoMetrics(
                    mandato=AnalyticsMandatoBasic(
                        id=mandato.id,
                        nome_parlamentar=mandato.nome_parlamentar,
                        cargo_parlamentar=mandato.cargo_parlamentar,
                        ue=mandato.ue,
                        created_at=mandato.created_at,
                    ),
                    status=m.status,
                    risk_level=m.risk_level,
                    ultimo_login=m.ultimo_login,
                    dias_sem_login=m.dias_sem_login,
                    logs_7d=m.logs_7d,
                    logs_30d=m.logs_30d,
                    funcionalidades=m.funcionalidades_count or {},
                )
            )
    
    total = session.scalar(
        select(func.count(AnalyticsMetric.id)).where(
            and_(
                AnalyticsMetric.entity_type == "mandato",
                AnalyticsMetric.reference_date == ref_month,
            )
        )
    )
    
    return AnalyticsEngagementList(mandatos=mandatos_data, total=total or 0)


@router.get("/engagement/users", response_model=List[AnalyticsUserMetricsOut])
def get_users_engagement(
    *,
    session: Session = Depends(get_session),
    current_admin=require_admin_user,
    mandato_id: Optional[int] = Query(None, description="Filter by mandato"),
    reference_month: Optional[str] = Query(None),
):
    """
    List users with engagement metrics.
    Can filter by mandato.
    """
    if reference_month:
        try:
            ref_date = datetime.strptime(reference_month, "%Y-%m")
        except ValueError:
            raise HTTPException(400, "Invalid date format")
    else:
        ref_date = datetime.now(timezone.utc).replace(tzinfo=None)
    
    ref_month = get_month_start(ref_date)
    
    stmt = select(AnalyticsMetric).where(
        and_(
            AnalyticsMetric.entity_type == "user",
            AnalyticsMetric.reference_date == ref_month,
        )
    )
    
    if mandato_id:
        # Get users of mandato
        user_ids = session.execute(
            select(mandato_user_link.c.user_id).where(
                mandato_user_link.c.mandato_id == mandato_id
            )
        ).scalars().all()
        stmt = stmt.where(AnalyticsMetric.entity_id.in_(user_ids))
    
    metrics = session.execute(stmt).scalars().all()
    
    users_data = []
    for m in metrics:
        user = session.get(UserORM, m.entity_id)
        if user:
            users_data.append(
                AnalyticsUserMetricsOut(
                    user_id=user.id,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    status=m.status,
                    risk_level=m.risk_level,
                    ultimo_login=m.ultimo_login,
                    dias_sem_login=m.dias_sem_login,
                    logs_7d=m.logs_7d,
                    logs_30d=m.logs_30d,
                    funcionalidades=m.funcionalidades_count or {},
                )
            )
    
    return users_data


@router.get("/mandatos/{mandato_id}/activity")
def get_mandato_activity_detail(
    mandato_id: int,
    *,
    session: Session = Depends(get_session),
    current_admin=require_admin_user,
    days: int = Query(30, ge=1, le=365),
):
    """
    Detailed activity timeline for a specific mandato.
    Returns daily log counts and funcionalidades breakdown.
    """
    mandato = session.get(MandatoORM, mandato_id)
    if not mandato:
        raise HTTPException(404, "Mandato não encontrado")
    
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    
    # Get all logs for period
    logs = session.execute(
        select(AuditLog).where(
            and_(
                AuditLog.actor_mandato_id == mandato_id,
                AuditLog.created_at >= cutoff,
            )
        ).order_by(AuditLog.created_at.desc())
    ).scalars().all()
    
    # Group by day
    daily_counts = defaultdict(int)
    func_counts = defaultdict(int)
    
    for log in logs:
        day_key = log.created_at.strftime("%Y-%m-%d")
        daily_counts[day_key] += 1
        
        func = get_funcionalidade_from_event(log.event_type)
        func_counts[func] += 1
    
    return {
        "mandato_id": mandato_id,
        "mandato_nome": mandato.nome_parlamentar,
        "period_days": days,
        "total_logs": len(logs),
        "daily_activity": [
            {"date": k, "count": v}
            for k, v in sorted(daily_counts.items())
        ],
        "funcionalidades": dict(func_counts),
    }


# Raw Data Endpoints

@router.get("/raw/audit-logs")
def get_raw_audit_logs(
    *,
    session: Session = Depends(get_session),
    current_admin=require_admin_user,
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    mandato_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    format: str = Query("json", pattern="^(json|csv)$"),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    """
    Export raw audit logs with all fields.
    Supports JSON and CSV formats for external analysis.
    """
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    
    if from_date:
        stmt = stmt.where(AuditLog.created_at >= from_date)
    if to_date:
        stmt = stmt.where(AuditLog.created_at <= to_date)
    if mandato_id:
        stmt = stmt.where(AuditLog.actor_mandato_id == mandato_id)
    if user_id:
        stmt = stmt.where(AuditLog.actor_user_id == user_id)
    if event_type:
        stmt = stmt.where(AuditLog.event_type == event_type)
    
    # Get total count for metadata
    count_stmt = select(func.count(AuditLog.id))
    if from_date:
        count_stmt = count_stmt.where(AuditLog.created_at >= from_date)
    if to_date:
        count_stmt = count_stmt.where(AuditLog.created_at <= to_date)
    if mandato_id:
        count_stmt = count_stmt.where(AuditLog.actor_mandato_id == mandato_id)
    if user_id:
        count_stmt = count_stmt.where(AuditLog.actor_user_id == user_id)
    if event_type:
        count_stmt = count_stmt.where(AuditLog.event_type == event_type)
    
    total = session.scalar(count_stmt) or 0
    
    stmt = stmt.offset(offset).limit(limit)
    logs = session.execute(stmt).scalars().all()
    
    # Build response data with enriched fields
    data = []
    for log in logs:
        user = session.get(UserORM, log.actor_user_id) if log.actor_user_id else None
        mandato = session.get(MandatoORM, log.actor_mandato_id) if log.actor_mandato_id else None
        
        row = {
            "id": log.id,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "event_type": log.event_type,
            "funcionalidade": get_funcionalidade_from_event(log.event_type),
            "actor_user_id": log.actor_user_id,
            "actor_user_email": user.email if user else None,
            "actor_mandato_id": log.actor_mandato_id,
            "actor_mandato_nome": mandato.nome_parlamentar if mandato else None,
            "actor_permission_level": log.actor_permission_level,
            "subject_id": log.subject_id,
            "request_id": log.request_id,
            "notes": log.notes,
        }
        data.append(row)
    
    if format == "csv":
        filename = f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return generate_csv_response(data, filename)
    
    return {
        "total": total,
        "count": len(data),
        "offset": offset,
        "logs": data,
    }


@router.get("/raw/mandatos")
def get_raw_mandatos_data(
    *,
    session: Session = Depends(get_session),
    current_admin=require_admin_user,
    reference_month: Optional[str] = Query(None),
    include_users: bool = Query(False),
    include_metrics: bool = Query(True),
    format: str = Query("json", pattern="^(json|csv)$"),
):
    """
    Export complete mandatos data with optional metrics and users.
    Ideal for BI tools and custom dashboards.
    """
    if reference_month:
        try:
            ref_date = datetime.strptime(reference_month, "%Y-%m")
        except ValueError:
            raise HTTPException(400, "Invalid date format. Use YYYY-MM")
    else:
        ref_date = datetime.now(timezone.utc).replace(tzinfo=None)
    
    ref_month = get_month_start(ref_date)
    
    # Get all mandatos
    mandatos = session.execute(select(MandatoORM)).scalars().all()
    
    # Get metrics if requested
    metrics_map = {}
    if include_metrics:
        metrics = session.execute(
            select(AnalyticsMetric).where(
                and_(
                    AnalyticsMetric.entity_type == "mandato",
                    AnalyticsMetric.reference_date == ref_month,
                )
            )
        ).scalars().all()
        metrics_map = {m.entity_id: m for m in metrics}
    
    data = []
    for mandato in mandatos:
        row: Dict[str, Any] = {
            "id": mandato.id,
            "nome_parlamentar": mandato.nome_parlamentar,
            "cargo_parlamentar": mandato.cargo_parlamentar,
            "partido": mandato.partido,
            "casa_legislativa": mandato.casa_legislativa,
            "municipio": mandato.municipio,
            "ue": mandato.ue,
            "esfera": mandato.esfera,
            "perfil_parlamentar": mandato.perfil_parlamentar,
            "espectro_politico": mandato.espectro_politico,
            "temas_interesse": mandato.temas_interesse,
            "created_at": mandato.created_at.isoformat() if mandato.created_at else None,
        }
        
        if include_metrics and mandato.id in metrics_map:
            m = metrics_map[mandato.id]
            row["metrics"] = {
                "status": m.status,
                "risk_level": m.risk_level,
                "ultimo_login": m.ultimo_login.isoformat() if m.ultimo_login else None,
                "dias_sem_login": m.dias_sem_login,
                "logs_7d": m.logs_7d,
                "logs_30d": m.logs_30d,
                "logs_total": m.logs_total,
                "funcionalidades": m.funcionalidades_count or {},
            }
        
        if include_users:
            users_list = []
            for user in mandato.users:
                users_list.append({
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "permission_level": user.permission_level,
                    "is_active": user.is_active,
                })
            row["users"] = users_list
        
        data.append(row)
    
    if format == "csv":
        filename = f"mandatos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return generate_csv_response(data, filename)
    
    return {
        "reference_month": ref_month.strftime("%Y-%m"),
        "count": len(data),
        "mandatos": data,
    }


@router.get("/raw/users")
def get_raw_users_data(
    *,
    session: Session = Depends(get_session),
    current_admin=require_admin_user,
    mandato_id: Optional[int] = Query(None),
    reference_month: Optional[str] = Query(None),
    include_metrics: bool = Query(True),
    format: str = Query("json", pattern="^(json|csv)$"),
):
    """Export users data with optional metrics"""
    if reference_month:
        try:
            ref_date = datetime.strptime(reference_month, "%Y-%m")
        except ValueError:
            raise HTTPException(400, "Invalid date format. Use YYYY-MM")
    else:
        ref_date = datetime.now(timezone.utc).replace(tzinfo=None)
    
    ref_month = get_month_start(ref_date)
    
    # Get users
    stmt = select(UserORM)
    if mandato_id:
        stmt = stmt.join(UserORM.mandatos).where(MandatoORM.id == mandato_id)
    
    users = session.execute(stmt).scalars().all()
    
    # Get metrics if requested
    metrics_map = {}
    if include_metrics:
        metrics = session.execute(
            select(AnalyticsMetric).where(
                and_(
                    AnalyticsMetric.entity_type == "user",
                    AnalyticsMetric.reference_date == ref_month,
                )
            )
        ).scalars().all()
        metrics_map = {m.entity_id: m for m in metrics}
    
    data = []
    for user in users:
        row: Dict[str, Any] = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "permission_level": user.permission_level,
            "role": user.role,
            "is_active": user.is_active,
            "lgpd_check": user.lgpd_check,
        }
        
        # Add mandatos
        mandatos_list = []
        for m in user.mandatos:
            mandatos_list.append({
                "id": m.id,
                "nome_parlamentar": m.nome_parlamentar,
            })
        row["mandatos"] = mandatos_list
        
        if include_metrics and user.id in metrics_map:
            metric = metrics_map[user.id]
            row["metrics"] = {
                "status": metric.status,
                "risk_level": metric.risk_level,
                "ultimo_login": metric.ultimo_login.isoformat() if metric.ultimo_login else None,
                "dias_sem_login": metric.dias_sem_login,
                "logs_7d": metric.logs_7d,
                "logs_30d": metric.logs_30d,
                "logs_total": metric.logs_total,
                "funcionalidades": metric.funcionalidades_count or {},
            }
        
        data.append(row)
    
    if format == "csv":
        filename = f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return generate_csv_response(data, filename)
    
    return {
        "reference_month": ref_month.strftime("%Y-%m"),
        "count": len(data),
        "users": data,
    }


@router.get("/raw/timeseries")
def get_raw_timeseries(
    *,
    session: Session = Depends(get_session),
    current_admin=require_admin_user,
    entity_type: str = Query(..., pattern="^(mandato|user)$"),
    entity_id: Optional[int] = Query(None),
    metric: str = Query(..., pattern="^(logs|logins)$"),
    from_date: datetime = Query(...),
    to_date: datetime = Query(...),
    granularity: str = Query("day", pattern="^(hour|day|week|month)$"),
    format: str = Query("json", pattern="^(json|csv)$"),
):
    """Time series data for custom charts"""
    # Build base query
    stmt = select(AuditLog.created_at)
    
    if entity_type == "mandato":
        stmt = stmt.where(AuditLog.actor_mandato_id == entity_id)
    elif entity_type == "user":
        stmt = stmt.where(AuditLog.actor_user_id == entity_id)
    
    if metric == "logins":
        stmt = stmt.where(AuditLog.event_type == "auth:login")
    
    stmt = stmt.where(
        and_(
            AuditLog.created_at >= from_date,
            AuditLog.created_at <= to_date,
        )
    )
    
    timestamps = session.execute(stmt).scalars().all()
    
    # Group by granularity
    buckets = defaultdict(int)
    for ts in timestamps:
        if granularity == "hour":
            key = ts.strftime("%Y-%m-%d %H:00:00")
        elif granularity == "day":
            key = ts.strftime("%Y-%m-%d")
        elif granularity == "week":
            key = ts.strftime("%Y-W%U")
        else:  # month
            key = ts.strftime("%Y-%m")
        buckets[key] += 1
    
    # Build response
    data = [
        {"timestamp": k, "value": v}
        for k, v in sorted(buckets.items())
    ]
    
    if format == "csv":
        filename = f"timeseries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return generate_csv_response(data, filename)
    
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "metric": metric,
        "granularity": granularity,
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
        "data": data,
    }


@router.get("/raw/funcionalidades-detail")
def get_raw_funcionalidades_detail(
    *,
    session: Session = Depends(get_session),
    current_admin=require_admin_user,
    mandato_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    format: str = Query("json", pattern="^(json|csv)$"),
):
    """Detailed breakdown of feature usage"""
    stmt = select(AuditLog)
    
    if mandato_id:
        stmt = stmt.where(AuditLog.actor_mandato_id == mandato_id)
    if user_id:
        stmt = stmt.where(AuditLog.actor_user_id == user_id)
    if from_date:
        stmt = stmt.where(AuditLog.created_at >= from_date)
    if to_date:
        stmt = stmt.where(AuditLog.created_at <= to_date)
    
    logs = session.execute(stmt).scalars().all()
    
    # Aggregate by funcionalidade
    func_detail = defaultdict(lambda: {"total_logs": 0, "event_types": defaultdict(int), "days": set()})
    by_day = defaultdict(lambda: defaultdict(int))
    
    total_logs = len(logs)
    
    for log in logs:
        func = get_funcionalidade_from_event(log.event_type)
        day = log.created_at.strftime("%Y-%m-%d")
        
        func_detail[func]["total_logs"] += 1
        func_detail[func]["event_types"][log.event_type] += 1
        func_detail[func]["days"].add(day)
        
        by_day[day][func] += 1
    
    # Build response
    by_funcionalidade = []
    for func, details in func_detail.items():
        unique_days = len(details["days"])
        avg_per_day = details["total_logs"] / unique_days if unique_days > 0 else 0
        
        event_types_list = [
            {"event_type": et, "count": count}
            for et, count in sorted(details["event_types"].items(), key=lambda x: x[1], reverse=True)
        ]
        
        by_funcionalidade.append({
            "funcionalidade": func,
            "total_logs": details["total_logs"],
            "percentage": round(details["total_logs"] / total_logs * 100, 2) if total_logs > 0 else 0,
            "unique_days": unique_days,
            "avg_per_day": round(avg_per_day, 2),
            "event_types": event_types_list,
        })
    
    by_funcionalidade.sort(key=lambda x: x["total_logs"], reverse=True)
    
    by_day_list = [
        {
            "date": day,
            "logs": sum(counts.values()),
            "breakdown": dict(counts),
        }
        for day, counts in sorted(by_day.items())
    ]
    
    unique_days_active = len(by_day)
    avg_logs_per_day = total_logs / unique_days_active if unique_days_active > 0 else 0
    
    result = {
        "filters": {
            "mandato_id": mandato_id,
            "user_id": user_id,
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
        },
        "summary": {
            "total_logs": total_logs,
            "unique_days_active": unique_days_active,
            "avg_logs_per_day": round(avg_logs_per_day, 2),
        },
        "by_funcionalidade": by_funcionalidade,
        "by_day": by_day_list,
    }
    
    if format == "csv":
        # Flatten for CSV
        csv_data = []
        for item in by_funcionalidade:
            csv_data.append({
                "funcionalidade": item["funcionalidade"],
                "total_logs": item["total_logs"],
                "percentage": item["percentage"],
                "unique_days": item["unique_days"],
                "avg_per_day": item["avg_per_day"],
            })
        filename = f"funcionalidades_detail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return generate_csv_response(csv_data, filename)
    
    return result
