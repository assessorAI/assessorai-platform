from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from .deps import (
    get_current_user,
    get_embedding_provider_dep,
    get_vector_store,
)
from ..services.audit import AuditLogger, get_audit_logger
from ..services.embeddings import EmbeddingProvider
from ..services.vector_store import VectorStorePgVector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["vector"])


def _embed_query(provider: EmbeddingProvider, query: str) -> list[float]:
    vectors = provider.embed([query.strip()])
    if not vectors:
        raise ValueError("Embedding provider retornou vetor vazio.")
    return vectors[0]


@router.get("/query")
async def search_vector(
    query: str,
    limit: int = 5,
    offset: int = 0,
    detail: bool = False,
    deduplicate: bool = True,
    current_user=Depends(get_current_user),
    store: VectorStorePgVector = Depends(get_vector_store),
    provider: EmbeddingProvider = Depends(get_embedding_provider_dep),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> Dict[str, Any]:
    try:
        query_vector = _embed_query(provider, query)
        results, query_time_ms = store.search(
            query_vector,
            limit=limit,
            offset=offset,
            return_latency=True,
            detail=detail,
            deduplicate=deduplicate,
        )
        query_time_ms = round(query_time_ms, 3)
        response_payload = {
            "projects": results,
            "pagination": {
                "offset": offset,
                "limit": limit,
                "total_returned": len(results),
                "has_more": len(results) == limit,
            },
            "query_time_ms": query_time_ms,
        }
        audit_logger.log(
            event_type="vector_search.query.success",
            payload={
                "query": query,
                "limit": limit,
                "offset": offset,
                "detail": detail,
                "deduplicate": deduplicate,
                "projects_returned": len(results),
                "query_time_ms": query_time_ms,
            },
            actor_user_id=getattr(current_user, "id", None),
            actor_permission_level=getattr(current_user, "permission_level", None),
        )
        return response_payload
    except Exception as exc:  # pragma: no cover - audit before raising
        logger.exception("Vector search failed")
        audit_logger.log(
            event_type="vector_search.query.error",
            payload={"query": query, "detail": detail, "deduplicate": deduplicate, "error": str(exc)},
            actor_user_id=getattr(current_user, "id", None),
            actor_permission_level=getattr(current_user, "permission_level", None),
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/top_projects")
async def top_projects(
    query: str,
    limit: int = 10,
    offset: int = 0,
    current_user=Depends(get_current_user),
    store: VectorStorePgVector = Depends(get_vector_store),
    provider: EmbeddingProvider = Depends(get_embedding_provider_dep),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> Dict[str, Any]:
    try:
        query_vector = _embed_query(provider, query)
        payload = store.top_projects(query_vector, limit=limit, offset=offset)
        audit_logger.log(
            event_type="vector_search.top_projects.success",
            payload={
                "query": query,
                "limit": limit,
                "offset": offset,
                "projects_returned": len(payload["projects"]),
            },
            actor_user_id=getattr(current_user, "id", None),
            actor_permission_level=getattr(current_user, "permission_level", None),
        )
        return payload
    except Exception as exc:  # pragma: no cover - audit before raising
        logger.exception("Vector top projects failed")
        audit_logger.log(
            event_type="vector_search.top_projects.error",
            payload={"query": query, "error": str(exc)},
            actor_user_id=getattr(current_user, "id", None),
            actor_permission_level=getattr(current_user, "permission_level", None),
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc
