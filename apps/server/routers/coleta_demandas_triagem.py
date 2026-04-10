from typing import Any, Dict, List, Optional, cast

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db.models import ColetaDemandaTriagem as ColetaDemandaTriagemORM
from ..db.models import Mandato as MandatoORM
from ..db.session import get_session
from ..llm import call_llm
from ..models import (
    ColetaDemandaCategoria,
    ColetaDemandaTipo,
    ColetaDemandaTriagemCreate,
    ColetaDemandaTriagemExtractRequest,
    ColetaDemandaTriagemExtraction,
    ColetaDemandaTriagemExtractionDraft,
    ColetaDemandaTriagemOut,
    ColetaDemandaTriagemUpdate,
)
from ..services.embeddings import EmbeddingProvider
from .deps import get_embedding_provider_dep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/coleta-demandas/triagem", tags=["coleta-demandas/triagem"])


def _extract_triagem_data(
    mandato_id: int,
    descricao_original: str,
    local_texto: Optional[str],
    solicitante_nome: Optional[str],
    solicitante_email: Optional[str],
    solicitante_telefone: Optional[str],
    session: Session,
) -> ColetaDemandaTriagemExtraction:
    mandato = session.get(MandatoORM, mandato_id)
    if not mandato:
        raise HTTPException(status_code=404, detail="Mandato nao encontrado")

    municipio = (mandato.municipio or "").strip()
    ue = (mandato.ue or "").strip()
    local_parts = [part for part in [municipio, ue] if part]

    pieces = [descricao_original]
    if local_texto:
        pieces.append(f"Local informado: {local_texto}")
    if solicitante_nome:
        pieces.append(f"Solicitante: {solicitante_nome}")
    if solicitante_email:
        pieces.append(f"Email: {solicitante_email}")
    if solicitante_telefone:
        pieces.append(f"Telefone: {solicitante_telefone}")
    if municipio:
        pieces.append(f"Municipio: {municipio}")
    if ue:
        pieces.append(f"UF: {ue}")

    try:
        response = call_llm(
            content={
                "input": "\n".join(pieces),
                "mandato": {
                    "nome_parlamentar": (mandato.nome_parlamentar or "").strip(),
                    "casa_legislativa": (mandato.casa_legislativa or "").strip(),
                    "cargo_parlamentar": (mandato.cargo_parlamentar or "").strip(),
                    "partido": (mandato.partido or "").strip(),
                    "esfera": (mandato.esfera or "").strip(),
                    "local": ", ".join(local_parts),
                },
            },
            prompt_template="extract_coleta_demanda_triagem",
            answer_template=ColetaDemandaTriagemExtractionDraft,
            session=session,
        )
    except Exception as exc:
        logger.error(
            "Coleta demandas triagem extraction failed",
            extra={"error": str(exc), "error_type": type(exc).__name__},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Falha ao extrair triagem da demanda")

    draft = ColetaDemandaTriagemExtractionDraft(**response)
    tipo_value = (draft.tipo or "outro").strip().lower()
    categoria_value = (draft.categoria or "outro").strip().lower()

    tipo_values = {item.value for item in ColetaDemandaTipo}
    categoria_values = {item.value for item in ColetaDemandaCategoria}

    tipo_safe = tipo_value if tipo_value in tipo_values else "outro"
    categoria_safe = categoria_value if categoria_value in categoria_values else "outro"

    descricao_processada = (draft.descricao_processada or descricao_original).strip()

    return ColetaDemandaTriagemExtraction(
        tipo=ColetaDemandaTipo(tipo_safe),
        categoria=ColetaDemandaCategoria(categoria_safe),
        descricao_processada=descricao_processada,
        local_texto=draft.local_texto or local_texto,
        solicitante_nome=draft.solicitante_nome or solicitante_nome,
        solicitante_email=draft.solicitante_email or solicitante_email,
        solicitante_telefone=draft.solicitante_telefone or solicitante_telefone,
    )


def persist_triagem_result(
    session: Session,
    provider: EmbeddingProvider,
    mandato_id: int,
    coleta_demanda_id: Optional[int],
    origem: str,
    descricao_original: str,
    local_texto: Optional[str],
    solicitante_nome: Optional[str],
    solicitante_email: Optional[str],
    solicitante_telefone: Optional[str],
) -> ColetaDemandaTriagemORM:
    extraction = _extract_triagem_data(
        mandato_id=mandato_id,
        descricao_original=descricao_original,
        local_texto=local_texto,
        solicitante_nome=solicitante_nome,
        solicitante_email=solicitante_email,
        solicitante_telefone=solicitante_telefone,
        session=session,
    )

    embedding_text = extraction.descricao_processada or descricao_original
    embedding: Optional[List[float]] = None
    try:
        embedding = provider.embed([embedding_text])[0]
    except Exception as exc:
        logger.warning(
            "Failed to generate triagem embedding",
            extra={"error": str(exc), "error_type": type(exc).__name__},
        )

    obj = ColetaDemandaTriagemORM(
        mandato_id=mandato_id,
        coleta_demanda_id=coleta_demanda_id,
        tipo=extraction.tipo.value,
        categoria=extraction.categoria.value,
        descricao_original=descricao_original,
        descricao_processada=extraction.descricao_processada,
        descricao_embedding=embedding,
        local_texto=extraction.local_texto,
        origem=origem,
        solicitante_nome=extraction.solicitante_nome,
        solicitante_email=extraction.solicitante_email,
        solicitante_telefone=extraction.solicitante_telefone,
    )
    session.add(obj)
    session.flush()
    return obj


@router.post("/extract", response_model=ColetaDemandaTriagemExtraction)
def extract_triagem(
    data: ColetaDemandaTriagemExtractRequest,
    session: Session = Depends(get_session),
) -> ColetaDemandaTriagemExtraction:
    return _extract_triagem_data(
        mandato_id=data.mandato_id,
        descricao_original=data.descricao_original,
        local_texto=data.local_texto,
        solicitante_nome=data.solicitante_nome,
        solicitante_email=str(data.solicitante_email) if data.solicitante_email else None,
        solicitante_telefone=data.solicitante_telefone,
        session=session,
    )


@router.post("", response_model=ColetaDemandaTriagemOut)
def create_triagem(
    data: ColetaDemandaTriagemCreate,
    session: Session = Depends(get_session),
    provider: EmbeddingProvider = Depends(get_embedding_provider_dep),
) -> ColetaDemandaTriagemOut:
    mandato = session.get(MandatoORM, data.mandato_id)
    if not mandato:
        raise HTTPException(status_code=404, detail="Mandato nao encontrado")

    embedding_text = data.descricao_processada or data.descricao_original
    embedding: Optional[List[float]] = None
    try:
        embedding = provider.embed([embedding_text])[0]
    except Exception as exc:
        logger.warning(
            "Failed to generate triagem embedding",
            extra={"error": str(exc), "error_type": type(exc).__name__},
        )

    obj = ColetaDemandaTriagemORM(
        mandato_id=data.mandato_id,
        coleta_demanda_id=data.coleta_demanda_id,
        tipo=data.tipo.value if data.tipo else None,
        categoria=data.categoria.value if data.categoria else None,
        descricao_original=data.descricao_original,
        descricao_processada=data.descricao_processada,
        descricao_embedding=embedding,
        local_texto=data.local_texto,
        origem=data.origem,
        solicitante_nome=data.solicitante_nome,
        solicitante_email=str(data.solicitante_email) if data.solicitante_email else None,
        solicitante_telefone=data.solicitante_telefone,
    )
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return ColetaDemandaTriagemOut.model_validate(obj)


@router.get("", response_model=Dict[str, Any])
def list_triagem(
    mandato_id: int = Query(..., ge=1),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    tipo: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    origem: Optional[str] = Query(None),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    stmt = select(ColetaDemandaTriagemORM).where(ColetaDemandaTriagemORM.mandato_id == mandato_id)
    if tipo:
        stmt = stmt.where(ColetaDemandaTriagemORM.tipo == tipo)
    if categoria:
        stmt = stmt.where(ColetaDemandaTriagemORM.categoria == categoria)
    if origem:
        stmt = stmt.where(ColetaDemandaTriagemORM.origem == origem)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.scalar(count_stmt) or 0
    items = session.scalars(
        stmt.order_by(ColetaDemandaTriagemORM.created_at.desc()).limit(limit).offset(offset)
    ).all()

    return {
        "triagens": [ColetaDemandaTriagemOut.model_validate(obj) for obj in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{triagem_id}", response_model=ColetaDemandaTriagemOut)
def get_triagem(
    triagem_id: int,
    mandato_id: int = Query(..., ge=1),
    session: Session = Depends(get_session),
) -> ColetaDemandaTriagemOut:
    obj = session.scalar(
        select(ColetaDemandaTriagemORM).where(
            ColetaDemandaTriagemORM.id == triagem_id,
            ColetaDemandaTriagemORM.mandato_id == mandato_id,
        )
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Triagem nao encontrada")
    return ColetaDemandaTriagemOut.model_validate(obj)


@router.put("/{triagem_id}", response_model=ColetaDemandaTriagemOut)
def update_triagem(
    triagem_id: int,
    data: ColetaDemandaTriagemUpdate,
    mandato_id: int = Query(..., ge=1),
    session: Session = Depends(get_session),
    provider: EmbeddingProvider = Depends(get_embedding_provider_dep),
) -> ColetaDemandaTriagemOut:
    obj = session.scalar(
        select(ColetaDemandaTriagemORM).where(
            ColetaDemandaTriagemORM.id == triagem_id,
            ColetaDemandaTriagemORM.mandato_id == mandato_id,
        )
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Triagem nao encontrada")

    obj_any = cast(Any, obj)
    payload = dict(data.model_dump(exclude_unset=True))
    if "tipo" in payload:
        tipo_value = payload.pop("tipo")
        obj_any.tipo = tipo_value.value if tipo_value else None
    if "categoria" in payload:
        categoria_value = payload.pop("categoria")
        obj_any.categoria = categoria_value.value if categoria_value else None

    for key in [
        "descricao_original",
        "descricao_processada",
        "origem",
        "local_texto",
        "solicitante_nome",
        "solicitante_email",
        "solicitante_telefone",
    ]:
        if key in payload:
            setattr(obj, key, payload[key])

    if "descricao_original" in payload or "descricao_processada" in payload:
        embedding_text = str(obj_any.descricao_processada or obj_any.descricao_original)
        try:
            obj_any.descricao_embedding = provider.embed([embedding_text])[0]
        except Exception as exc:
            logger.warning(
                "Failed to update triagem embedding",
                extra={"error": str(exc), "error_type": type(exc).__name__},
            )

    session.add(obj)
    session.commit()
    session.refresh(obj)
    return ColetaDemandaTriagemOut.model_validate(obj)


@router.delete("/{triagem_id}", response_model=Dict[str, str])
def delete_triagem(
    triagem_id: int,
    mandato_id: int = Query(..., ge=1),
    session: Session = Depends(get_session),
) -> Dict[str, str]:
    obj = session.scalar(
        select(ColetaDemandaTriagemORM).where(
            ColetaDemandaTriagemORM.id == triagem_id,
            ColetaDemandaTriagemORM.mandato_id == mandato_id,
        )
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Triagem nao encontrada")

    session.delete(obj)
    session.commit()
    return {"detail": "Triagem removida"}
