from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import re
import secrets
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from google.cloud import storage
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import ColetaDemanda, ColetaDemandaAttachment, ColetaDemandasContact, Mandato
from ..db.session import get_session
from ..models import (
    ColetaDemandaCreateIn,
    ColetaDemandasCreateResponse,
    ColetaDemandasUserOut,
    ColetaDemandasValidateResponse,
    form_factory,
)
from ..services.embeddings import EmbeddingProvider
from .coleta_demandas_triagem import persist_triagem_result
from .deps import get_embedding_provider_dep

router = APIRouter(prefix="/coleta-demandas", tags=["coleta-demandas"])
limiter = Limiter(key_func=get_remote_address, enabled=not bool(os.getenv("PYTEST_CURRENT_TEST")))
logger = logging.getLogger(__name__)

MAX_ARQUIVOS = int(os.getenv("COLETA_DEMANDAS_MAX_FILES", "5"))
MAX_FILE_SIZE = int(os.getenv("COLETA_DEMANDAS_MAX_FILE_SIZE", "10485760"))
TOKEN_SECRET = os.getenv("COLETA_DEMANDAS_TOKEN_SECRET", os.getenv("SECRET_KEY", "dev-secret"))
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}


def _normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) < 10 or len(digits) > 13:
        raise HTTPException(status_code=400, detail="Telefone invalido")
    return digits


def _parse_birth_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="data_nascimento invalida") from exc


def _build_contact_token(contact_id: int, mandato_id: int) -> str:
    payload = f"{contact_id}:{mandato_id}:{int(datetime.now(timezone.utc).timestamp())}"
    signature = hmac.new(TOKEN_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    token = f"{payload}:{signature}"
    return base64.urlsafe_b64encode(token.encode("utf-8")).decode("utf-8")


def _decode_contact_token(token: str) -> tuple[int, int]:
    try:
        decoded = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        contact_id_str, mandato_id_str, _issued_at, signature = decoded.split(":", 3)
        payload = f"{contact_id_str}:{mandato_id_str}:{_issued_at}"
    except Exception as exc:
        raise HTTPException(status_code=400, detail="contact_token invalido") from exc

    expected = hmac.new(TOKEN_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=400, detail="contact_token invalido")

    return int(contact_id_str), int(mandato_id_str)


def _get_bucket():
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        raise HTTPException(status_code=500, detail="GCS_BUCKET_NAME not configured")
    client = storage.Client()
    return client.bucket(bucket_name), bucket_name


def _serialize_contact(contact: ColetaDemandasContact) -> ColetaDemandasUserOut:
    return ColetaDemandasUserOut(
        id=str(contact.id),
        nome_completo=contact.nome_completo,
        telefone=contact.telefone_exibicao,
        bairro=contact.bairro,
        data_nascimento=contact.data_nascimento.strftime("%d/%m/%Y"),
    )


def _resolve_contact_from_token(token: Optional[str], session: Session) -> Optional[ColetaDemandasContact]:
    if not token:
        return None
    contact_id, mandato_id = _decode_contact_token(token)
    contact = session.get(ColetaDemandasContact, contact_id)
    if contact is None or int(contact.mandato_id) != mandato_id:
        raise HTTPException(status_code=400, detail="contact_token invalido")
    return contact


@router.get("/me", response_model=ColetaDemandasValidateResponse)
def get_saved_contact(
    contact_token: str = Query(...),
    session: Session = Depends(get_session),
) -> ColetaDemandasValidateResponse:
    contact = _resolve_contact_from_token(contact_token, session)
    if not contact:
        raise HTTPException(status_code=404, detail="Contato nao encontrado")
    return ColetaDemandasValidateResponse(user=_serialize_contact(contact))


@router.post("", response_model=ColetaDemandasCreateResponse)
@limiter.limit("30/minute")
async def create_coleta_demanda(
    request: Request,
    mandato_id: int,
    payload: ColetaDemandaCreateIn = form_factory(ColetaDemandaCreateIn),
    arquivos: Optional[List[UploadFile]] = File(None),
    session: Session = Depends(get_session),
    provider: EmbeddingProvider = Depends(get_embedding_provider_dep),
) -> ColetaDemandasCreateResponse:
    if not session.get(Mandato, mandato_id):
        raise HTTPException(status_code=404, detail="Mandato nao encontrado")

    token_contact = _resolve_contact_from_token(payload.contact_token, session)

    nome_completo_final = (payload.nome_completo or (token_contact.nome_completo if token_contact else "")).strip()
    telefone_exibicao_final = (payload.telefone or (token_contact.telefone_exibicao if token_contact else "")).strip()
    bairro_final = (payload.bairro or (token_contact.bairro if token_contact else "")).strip()
    data_nascimento_final = (
        payload.data_nascimento
        or (token_contact.data_nascimento.strftime("%d/%m/%Y") if token_contact else "")
    ).strip()

    if len(nome_completo_final) < 3:
        raise HTTPException(status_code=400, detail="nome_completo invalido")
    if len(bairro_final) < 3:
        raise HTTPException(status_code=400, detail="bairro invalido")

    telefone_normalizado = _normalize_phone(telefone_exibicao_final)
    nascimento = _parse_birth_date(data_nascimento_final)

    endereco_final = (payload.endereco or "").strip() or None
    ponto_referencia_final = (payload.ponto_referencia or "").strip() or None
    if not endereco_final and not ponto_referencia_final:
        raise HTTPException(status_code=400, detail="Informe pelo menos um: endereco ou ponto_referencia")

    arquivos = arquivos or []
    if len(arquivos) > MAX_ARQUIVOS:
        raise HTTPException(status_code=400, detail=f"Maximo de {MAX_ARQUIVOS} arquivos")

    contact: Optional[ColetaDemandasContact] = token_contact
    existing_contact = session.scalar(
        select(ColetaDemandasContact).where(
            ColetaDemandasContact.mandato_id == mandato_id,
            ColetaDemandasContact.telefone_normalizado == telefone_normalizado,
        )
    )
    if existing_contact:
        contact = existing_contact
        contact.nome_completo = nome_completo_final
        contact.telefone_exibicao = telefone_exibicao_final
        contact.bairro = bairro_final
        contact.data_nascimento = nascimento
    else:
        contact = ColetaDemandasContact(
            mandato_id=mandato_id,
            nome_completo=nome_completo_final,
            telefone_normalizado=telefone_normalizado,
            telefone_exibicao=telefone_exibicao_final,
            bairro=bairro_final,
            data_nascimento=nascimento,
        )
        session.add(contact)
        session.flush()

    demanda = ColetaDemanda(
        mandato_id=mandato_id,
        contact_id=contact.id if contact else None,
        descricao=payload.descricao.strip(),
        endereco=endereco_final,
        nao_sei_endereco=False,
        ponto_referencia=ponto_referencia_final,
        nome_completo=nome_completo_final,
        telefone_normalizado=telefone_normalizado,
        telefone_exibicao=telefone_exibicao_final,
        bairro=bairro_final,
        data_nascimento=nascimento,
        nome_responsavel=None,
        telefone_responsavel=None,
    )
    session.add(demanda)
    session.flush()

    bucket, bucket_name = _get_bucket()
    for arquivo in arquivos:
        content_type = (arquivo.content_type or "").lower()
        if content_type and content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=415, detail=f"Tipo de arquivo nao suportado: {content_type}")
        content = await arquivo.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Arquivo muito grande")

        generated_name = f"{demanda.id}-{secrets.token_hex(6)}-{Path(arquivo.filename or 'file').name}"
        blob_name = f"coleta-demandas/{mandato_id}/{demanda.id}/{generated_name}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(content, content_type=content_type or "application/octet-stream")
        storage_path = f"gs://{bucket_name}/{blob_name}"

        session.add(
            ColetaDemandaAttachment(
                demanda_id=demanda.id,
                filename=arquivo.filename or generated_name,
                content_type=content_type or None,
                size_bytes=len(content),
                storage_path=storage_path,
            )
        )

    try:
        persist_triagem_result(
            session=session,
            provider=provider,
            mandato_id=mandato_id,
            coleta_demanda_id=demanda.id,
            origem="coleta_publica",
            descricao_original=payload.descricao.strip(),
            local_texto=endereco_final or ponto_referencia_final,
            solicitante_nome=nome_completo_final,
            solicitante_email=None,
            solicitante_telefone=telefone_normalizado,
        )
    except Exception as exc:
        logger.warning(
            "Triagem IA failed during public coleta creation",
            extra={"error": str(exc), "error_type": type(exc).__name__, "demanda_id": demanda.id},
        )

    session.commit()

    contact_token_out = None
    if contact:
        contact_token_out = _build_contact_token(contact.id, contact.mandato_id)

    return ColetaDemandasCreateResponse(
        message="Demanda criada com sucesso",
        contact_token=contact_token_out,
    )
