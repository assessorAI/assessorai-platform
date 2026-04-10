from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..db.models import VectorImportJob, VectorImportJobStatus
from ..db.session import SessionLocal, get_session
from ..services.audit import AuditLogger, get_audit_logger
from ..services.embeddings import (
    EmbeddingProvider,
    get_embedding_provider,
    list_available_providers,
    resolve_current_model,
    resolve_current_provider,
)
from ..services.vector_ingestion import ImportItem, ingest_documents
from ..services.vector_store import VectorStorePgVector
from .deps import require_admin_user, get_embedding_provider_dep, get_vector_store

logger = logging.getLogger(__name__)


class VectorImportItem(BaseModel):
    title: Optional[str] = None
    house: Optional[str] = None
    type: Optional[str] = None
    number: Optional[int] = None
    presentation_date: Optional[str] = None
    year: Optional[int] = None
    author: Optional[List[str] | str] = None
    subject: Optional[str] = None
    full_text: Optional[str] = None
    length: Optional[int] = None
    url: Optional[str] = None
    scraped_at: Optional[str] = None
    metadata: Optional[Dict[str, Any] | str] = None

    @field_validator("author", mode="before")
    @classmethod
    def _normalize_author(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return value
        return list(value)

    @model_validator(mode='before')
    @classmethod
    def _check_wrong_format(cls, data):
        """Detecta se recebeu um wrapper ao invés de um item"""
        if isinstance(data, dict) and "items" in data and len(data.keys()) <= 3:
            raise ValueError(
                "Formato incorreto: parece que você enviou o wrapper JSON inteiro. "
                "Envie apenas a lista de itens, não o objeto que contém 'items'."
            )
        return data


class VectorImportRequest(BaseModel):
    items: List[VectorImportItem]
    chunk_full_text: bool = True
    chunk_size: int = Field(3000, ge=128, le=8000)
    chunk_overlap: int = Field(150, ge=0, le=1000)
    chunk_token_model: Optional[str] = None
    truncate_before_insert: bool = True
    embedding_provider: Optional[str] = None
    embedding_model: Optional[str] = None
    name: Optional[str] = None

    @field_validator("items")
    @classmethod
    def _ensure_items(cls, value: List[VectorImportItem]) -> List[VectorImportItem]:
        if not value:
            raise ValueError("A lista de itens não pode estar vazia.")
        return value


class VectorImportResponse(BaseModel):
    items: int
    chunks: int
    provider: str
    model: str


router = APIRouter(prefix="/admin/vector", tags=["admin/vector"])


class VectorProviderOption(BaseModel):
    id: str
    label: str
    available: bool = True
    default_model: Optional[str] = None


class VectorProvidersResponse(BaseModel):
    providers: List[VectorProviderOption]
    current_provider: str
    current_model: Optional[str]


class VectorStatsResponse(BaseModel):
    projects: int
    chunks: int


class VectorReindexRequest(BaseModel):
    embedding_provider: Optional[str] = None
    embedding_model: Optional[str] = None
    batch_size: int = Field(64, ge=1, le=512)


class VectorReindexResponse(BaseModel):
    provider: str
    model: Optional[str]
    chunks: int
    skipped: int
    total: int


@router.get("/providers", response_model=VectorProvidersResponse)
def list_embedding_providers(
    current_admin=require_admin_user,
) -> VectorProvidersResponse:
    available = list_available_providers()
    current_provider = resolve_current_provider()
    current_model = resolve_current_model(current_provider)
    if not available:
        current_provider = "local"
        current_model = resolve_current_model(current_provider)
    return VectorProvidersResponse(
        providers=[VectorProviderOption(**item) for item in available],
        current_provider=current_provider,
        current_model=current_model,
    )


@router.get("/stats", response_model=VectorStatsResponse)
def vector_stats(
    store: VectorStorePgVector = Depends(get_vector_store),
    current_admin=require_admin_user,
) -> VectorStatsResponse:
    stats = store.stats()
    return VectorStatsResponse(projects=stats["projects"], chunks=stats["chunks"])


@router.get("/summary")
def vector_summary(
    store: VectorStorePgVector = Depends(get_vector_store),
    current_admin=require_admin_user,
) -> Dict[str, Any]:
    """Get summary statistics grouped by house and year"""
    return store.get_summary_by_house_and_year()


@router.post("/reindex", response_model=VectorReindexResponse)
def reindex_vectors(
    payload: VectorReindexRequest,
    store: VectorStorePgVector = Depends(get_vector_store),
    current_admin=require_admin_user,
) -> VectorReindexResponse:
    provider = get_embedding_provider(
        provider=payload.embedding_provider,
        model_name=payload.embedding_model,
    )
    result = store.reindex(provider, batch_size=payload.batch_size)
    provider_name = getattr(provider, "name", payload.embedding_provider or "local")
    model_name = (
        payload.embedding_model
        or getattr(provider, "model_name", None)
        or resolve_current_model(provider_name.split(":", 1)[0])
    )
    return VectorReindexResponse(
        provider=provider_name,
        model=model_name,
        chunks=result.get("updated", 0),
        skipped=result.get("skipped", 0),
        total=result.get("total", 0),
    )


def _build_import_items(payload: VectorImportRequest) -> List[ImportItem]:
    return [
        ImportItem(
            title=item.title,
            house=item.house,
            type=item.type,
            number=item.number,
            presentation_date=item.presentation_date,
            year=item.year,
            author=item.author,
            subject=item.subject,
            full_text=item.full_text,
            length=item.length,
            url=item.url,
            scraped_at=item.scraped_at,
            metadata=item.metadata,
        )
        for item in payload.items
    ]


class VectorImportJobResponse(BaseModel):
    id: int
    name: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    total_items: int
    processed_chunks: int
    error_message: Optional[str]
    created_by: Optional[int]

    model_config = ConfigDict(from_attributes=True)


@router.get("/jobs", response_model=List[VectorImportJobResponse])
def list_import_jobs(
    limit: int = 10,
    offset: int = 0,
    session: Session = Depends(get_session),
    current_admin=require_admin_user,
) -> List[VectorImportJobResponse]:
    jobs = (
        session.query(VectorImportJob)
        .order_by(desc(VectorImportJob.created_at))
        .limit(limit)
        .offset(offset)
        .all()
    )
    return jobs


@router.delete("/jobs/{job_id}")
def delete_import_job(
    job_id: int,
    session: Session = Depends(get_session),
    current_admin=require_admin_user,
    audit: AuditLogger = Depends(get_audit_logger),
):
    job = session.get(VectorImportJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    
    # Audit log deletion
    audit.log(
        event_type="vector_import_job_deleted",
        subject_id=str(job_id),
        actor_user_id=current_admin.id if hasattr(current_admin, "id") else None,
        actor_permission_level=getattr(current_admin, "permission_level", None),
        payload={
            "job_id": job_id,
            "job_name": job.name,
            "status": job.status,
            "total_items": job.total_items,
            "processed_chunks": job.processed_chunks,
        },
    )
    
    session.delete(job)
    session.commit()
    
    return {"status": "deleted", "job_id": job_id}


def background_ingest_task(
    job_id: int,
    payload: VectorImportRequest,
    provider_name: str,
    model_name: str,
):
    from ..db.session import SessionLocal as SessionFactory
    if SessionFactory is None:
        logger.error("SessionLocal not initialized - cannot run background task")
        return
    session = SessionFactory()
    try:
        job = session.get(VectorImportJob, job_id)
        if not job:
            logger.warning("vector_import_job_not_found", extra={"job_id": job_id})
            return

        logger.info(
            "vector_import_job_started",
            extra={
                "job_id": job_id,
                "job_name": job.name,
                "total_items": job.total_items,
                "provider": provider_name,
                "model": model_name,
            },
        )

        job.status = VectorImportJobStatus.PROCESSING
        session.commit()

        if payload.embedding_provider or payload.embedding_model:
            provider = get_embedding_provider(provider=provider_name, model_name=model_name)
        else:
            # Fallback or default logic if needed, but we passed resolved names
            provider = get_embedding_provider(provider=provider_name, model_name=model_name)

        result = ingest_documents(
            session,
            provider=provider,
            items=_build_import_items(payload),
            chunk_full_text=payload.chunk_full_text,
            chunk_size=payload.chunk_size,
            overlap_tokens=payload.chunk_overlap,
            chunk_model=payload.chunk_token_model or model_name,
            truncate_before_insert=payload.truncate_before_insert,
        )

        job.processed_chunks = result.get("chunks", 0)
        job.status = VectorImportJobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        session.commit()

        # Audit log completion
        audit_logger = AuditLogger(session=session)
        audit_logger.log(
            event_type="vector_import_completed",
            subject_id=str(job_id),
            actor_user_id=job.created_by,
            payload={
                "job_id": job_id,
                "job_name": job.name,
                "total_items": result.get("items", 0),
                "processed_chunks": result.get("chunks", 0),
            },
        )

        logger.info(
            "vector_import_job_completed",
            extra={
                "job_id": job_id,
                "job_name": job.name,
                "total_items": result.get("items", 0),
                "processed_chunks": result.get("chunks", 0),
            },
        )

    except Exception as e:
        session.rollback()
        logger.error(
            "vector_import_job_failed",
            extra={
                "job_id": job_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        if job:
            job.status = VectorImportJobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            session.commit()

            # Audit log failure
            audit_logger = AuditLogger(session=session)
            audit_logger.log(
                event_type="vector_import_failed",
                subject_id=str(job_id),
                actor_user_id=job.created_by,
                payload={
                    "job_id": job_id,
                    "job_name": job.name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
    finally:
        session.close()


class CheckDuplicatesRequest(BaseModel):
    items: List[VectorImportItem]
    sample_size: int = Field(5, ge=1, le=20)

    @field_validator("items")
    @classmethod
    def _ensure_items(cls, value: List[VectorImportItem]) -> List[VectorImportItem]:
        if not value:
            raise ValueError("A lista de itens não pode estar vazia.")
        return value


class CheckDuplicatesResponse(BaseModel):
    total_checked: int
    existing_count: int
    existing_documents: List[Dict[str, Any]]
    all_exist: bool
    warning_message: Optional[str] = None


@router.post("/check-duplicates", response_model=CheckDuplicatesResponse)
def check_duplicates(
    payload: CheckDuplicatesRequest,
    vector_store: VectorStorePgVector = Depends(get_vector_store),
    current_admin=require_admin_user,
):
    """
    Verifica se os primeiros N documentos do upload já existem no banco vetorial.
    
    Isso ajuda a prevenir importações duplicadas acidentais.
    """
    documents = [item.model_dump() for item in payload.items]
    result = vector_store.check_documents_exist(documents, sample_size=payload.sample_size)
    
    # Add warning message if duplicates found
    if result["existing_count"] > 0:
        if result["all_exist"]:
            result["warning_message"] = (
                f"⚠️ ATENÇÃO: Todos os {result['total_checked']} documentos verificados já existem no banco! "
                "Importar novamente pode criar duplicatas. Considere desabilitar a opção 'Substituir registros existentes'."
            )
        else:
            result["warning_message"] = (
                f"⚠️ Encontrados {result['existing_count']} de {result['total_checked']} documentos já existentes no banco. "
                "Verifique se esta importação é realmente necessária."
            )
    
    return result


@router.post("/import", response_model=VectorImportJobResponse)
def import_vector_documents(
    payload: VectorImportRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_admin=require_admin_user,
    audit: AuditLogger = Depends(get_audit_logger),
):
    provider_name = (payload.embedding_provider or os.getenv("EMBEDDING_PROVIDER", "openai")).lower()
    model_name = payload.embedding_model or os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # Check for active jobs to prevent concurrent imports
    active_jobs = session.query(VectorImportJob).filter(
        VectorImportJob.status.in_([
            VectorImportJobStatus.PENDING,
            VectorImportJobStatus.PROCESSING
        ])
    ).all()
    
    if active_jobs:
        active_names = [j.name for j in active_jobs[:3]]
        job_list = ", ".join(active_names)
        if len(active_jobs) > 3:
            job_list += f" e mais {len(active_jobs) - 3}"
        
        raise HTTPException(
            status_code=409,
            detail={
                "error": "concurrent_import_not_allowed",
                "message": f"Já existe(m) {len(active_jobs)} importação(ões) em andamento. Aguarde a conclusão ou cancele os jobs ativos.",
                "active_jobs": [
                    {"id": j.id, "name": j.name, "status": j.status, "created_at": j.created_at.isoformat()}
                    for j in active_jobs
                ]
            }
        )

    # Create Job
    job = VectorImportJob(
        name=payload.name or f"Import {datetime.utcnow().isoformat()}",
        status=VectorImportJobStatus.PENDING,
        total_items=len(payload.items),
        created_by=current_admin.id if hasattr(current_admin, "id") else None,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    # Audit log
    audit.log(
        event_type="vector_import_initiated",
        subject_id=str(job.id),
        actor_user_id=current_admin.id if hasattr(current_admin, "id") else None,
        actor_permission_level=getattr(current_admin, "permission_level", None),
        payload={
            "job_id": job.id,
            "job_name": job.name,
            "total_items": job.total_items,
            "provider": provider_name,
            "model": model_name,
            "chunk_size": payload.chunk_size,
            "chunk_overlap": payload.chunk_overlap,
            "truncate_before_insert": payload.truncate_before_insert,
        },
    )

    background_tasks.add_task(
        background_ingest_task,
        job.id,
        payload,
        provider_name,
        model_name,
    )

    return job

