from typing import Optional, List, Literal
from fastapi import HTTPException, APIRouter, Body, File, UploadFile, Depends, Form
from pydantic import BaseModel, Field
from ..models import Mandato as MandatoSchema, EmendasOneLiner, EmendaCompleta, Emenda, ParecerConstitucional, ProjetoLei, SimpleText, form_factory
from .upload import store_bytes_to_gcs, resolve_ref
from ..utils.reference_processor import process_references
from ..utils.text_cleanup import clean_llm_response

from ..llm import call_llm, generate_response
from ..db.session import get_session
from ..db.models import Mandato as MandatoORM, File as FileModel
from sqlalchemy.orm import Session
from .deps import get_current_user, resolve_mandato_with_permissions
from ..services.audit import AuditLogger, get_audit_logger
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/expert",
    tags=["pl"],
)


class ExpertPlRequest(BaseModel):
    origem_legislativa: Optional[str] = Field(
        None,
        description="Origem da legislação",
        examples=["Executivo", "Legislativo"],
    )

@router.post("/pl/analise_constitucionalidade")
async def api_analise_constitucionalidade(
    request: ExpertPlRequest = form_factory(ExpertPlRequest),
    mandato_id: Optional[int] = None,
    file: UploadFile = File(description="Arquivo em PDF do projeto"),
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    payload: dict = {
        'mandato': None,
        'origem_legislativa': None,
    }
    mandato_obj = resolve_mandato_with_permissions(session, current_user, mandato_id)
    payload['mandato'] = MandatoSchema.model_validate(mandato_obj, from_attributes=True).model_dump()
    if request.origem_legislativa:
        payload['origem_legislativa'] = request.origem_legislativa
    file_content = await file.read()
    stored_file = store_bytes_to_gcs(file_content, filename=file.filename, content_type=file.content_type, userId=str(getattr(current_user, 'id', 'dummy')))
    #parsed_file = await file.read()
    #parsed_file = {
    #    "type": "local",
    #    "raw": parsed_file,
    #    "filename": file.filename
    #}
    #constituicao = open('library/constituicao-checklist.pdf', 'rb').read()
    parsed_file = {
        "type": "remote",
        "path": stored_file["file_uri"]
    }
    
    constituicao = {
        "type": "remote",
        "path": "gs://assessorai_storage/library/constituicao-checklist.pdf"
    }
    
    try:
        content = call_llm(
            payload,
            files=[constituicao, parsed_file],
            prompt_template='expert_pl_constitucionalidade',
            answer_template=ParecerConstitucional,
            session=session,
        )
        # Clean redundant titles from LLM response
        content = clean_llm_response(
            content,
            fields_to_clean=['justificativa', 'sugestao']
        )
    except ValueError as e:
        logger.warning(
            "Invalid input for constitutional analysis",
            extra={
                "user_id": getattr(current_user, "id", None),
                "mandato_id": getattr(mandato_obj, "id", None),
                "file_uri": stored_file.get("file_uri"),
                "error": str(e)
            }
        )
        audit_logger.log(
            event_type="expert_pl.analysis.failed",
            payload={"error": str(e), "file": stored_file.get("file_uri")},
            actor_user_id=getattr(current_user, "id", None),
            actor_mandato_id=getattr(mandato_obj, "id", None),
            actor_permission_level=getattr(current_user, "permission_level", None),
        )
        raise HTTPException(status_code=400, detail=str(e))

    audit_log = audit_logger.log(
        event_type="expert_pl.analysis.success",
        payload={
            "origem_legislativa": request.origem_legislativa,
            "file_uri": stored_file.get("file_uri"),
        },
        response=content,
        actor_user_id=getattr(current_user, "id", None),
        actor_mandato_id=getattr(mandato_obj, "id", None),
        actor_permission_level=getattr(current_user, "permission_level", None),
    )
    response = generate_response(content)
    if hasattr(response, "headers"):
        response.headers["x-audit-log-id"] = str(audit_log.id)
    return response

@router.post("/pl/sugestao_emendas")
async def sugestao_emendas(
    request: ExpertPlRequest = form_factory(ExpertPlRequest),
    mandato_id: Optional[int] = None,
    file: UploadFile = File(),
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    payload: dict = {
        'mandato': None,
        'origem_legislativa': None,
    }
    mandato_obj = resolve_mandato_with_permissions(session, current_user, mandato_id)
    payload['mandato'] = MandatoSchema.model_validate(mandato_obj, from_attributes=True).model_dump()
    if request.origem_legislativa:
        payload['origem_legislativa'] = request.origem_legislativa
    file_content = await file.read()
    stored_file = store_bytes_to_gcs(file_content, filename=file.filename, content_type=file.content_type, userId=str(getattr(current_user, 'id', 'dummy')))
    parsed_file = {
        "type": "remote",
        "path": stored_file["file_uri"],
    }
    try:
        content = call_llm(
            payload,
            files=[parsed_file],
            prompt_template='expert_pl_sugestao_emendas',
            answer_template=EmendasOneLiner,
            session=session,
        )
    except ValueError as e:
        logger.warning(
            "Invalid input for amendment suggestions",
            extra={
                "user_id": getattr(current_user, "id", None),
                "mandato_id": getattr(mandato_obj, "id", None),
                "file_uri": stored_file.get("file_uri"),
                "error": str(e)
            }
        )
        audit_logger.log(
            event_type="expert_pl.suggest_amendments.failed",
            payload={"error": str(e), "file_uri": stored_file.get("file_uri")},
            actor_user_id=getattr(current_user, "id", None),
            actor_mandato_id=getattr(mandato_obj, "id", None),
            actor_permission_level=getattr(current_user, "permission_level", None),
        )
        raise HTTPException(status_code=400, detail=str(e))

    audit_log = audit_logger.log(
        event_type="expert_pl.suggest_amendments.success",
        payload={
            "origem_legislativa": request.origem_legislativa,
            "file_uri": stored_file.get("file_uri"),
        },
        response=content,
        actor_user_id=getattr(current_user, "id", None),
        actor_mandato_id=getattr(mandato_obj, "id", None),
        actor_permission_level=getattr(current_user, "permission_level", None),
    )
    response = generate_response(content)
    if hasattr(response, "headers"):
        response.headers["x-audit-log-id"] = str(audit_log.id)
    return response

@router.post("/pl/criar_emenda")
async def criar_emenda(
    request: ExpertPlRequest = form_factory(ExpertPlRequest),
    mandato_id: Optional[int] = None,
    emenda: Emenda = form_factory(Emenda),
    file: UploadFile = File(),
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    payload: dict = {
        'mandato': None,
        'origem_legislativa': None,
    }
    mandato_obj = resolve_mandato_with_permissions(session, current_user, mandato_id)
    payload['mandato'] = MandatoSchema.model_validate(mandato_obj, from_attributes=True).model_dump()
    if request.origem_legislativa:
        payload['origem_legislativa'] = request.origem_legislativa
    payload['emenda'] = emenda.model_dump()
    file_content = await file.read()
    stored_file = store_bytes_to_gcs(file_content, filename=file.filename, content_type=file.content_type, userId=str(getattr(current_user, 'id', 'dummy')))
    parsed_file = {
        "type": "remote",
        "path": stored_file["file_uri"],
    }
    try:
        content = call_llm(
            payload,
            files=[parsed_file],
            prompt_template='expert_pl_criar_emenda',
            answer_template=EmendaCompleta,
            session=session,
        )
        # Clean redundant titles from LLM response
        content = clean_llm_response(
            content,
            fields_to_clean=['texto', 'justificativa']
        )
    except ValueError as e:
        logger.warning(
            "Invalid input for amendment creation",
            extra={
                "user_id": getattr(current_user, "id", None),
                "mandato_id": getattr(mandato_obj, "id", None),
                "file_uri": stored_file.get("file_uri"),
                "emenda_tipo": emenda.tipo if emenda else None,
                "error": str(e)
            }
        )
        audit_logger.log(
            event_type="expert_pl.create_amendment.failed",
            payload={"error": str(e), "file_uri": stored_file.get("file_uri")},
            actor_user_id=getattr(current_user, "id", None),
            actor_mandato_id=getattr(mandato_obj, "id", None),
            actor_permission_level=getattr(current_user, "permission_level", None),
        )
        raise HTTPException(status_code=400, detail=str(e))

    content['full_markdown'] = f"## Emenda\n\n{content.get('texto', '')}\n\n## Justificativa\n\n{content.get('justificativa', '')}\n" #Trocar por modelo com template de /templates

    audit_log = audit_logger.log(
        event_type="expert_pl.create_amendment.success",
        payload={
            "origem_legislativa": request.origem_legislativa,
            "file_uri": stored_file.get("file_uri"),
            "tipo": emenda.tipo,
        },
        response=content,
        actor_user_id=getattr(current_user, "id", None),
        actor_mandato_id=getattr(mandato_obj, "id", None),
        actor_permission_level=getattr(current_user, "permission_level", None),
    )
    response = generate_response(content)
    if hasattr(response, "headers"):
        response.headers["x-audit-log-id"] = str(audit_log.id)
    return response


@router.post("/pl/criar_projeto")
async def sugestao_projeto(
    request: ExpertPlRequest = form_factory(ExpertPlRequest),
    mandato_id: Optional[int] = None,
    text_input: SimpleText = form_factory(SimpleText, examples=["Projeto de iluminação pública"]),
    referencias: Optional[str] = Form(None,
                                      description="JSON: lista de contextos",
                                      examples=[[{"type": "text", "content": "Natal"}],]
                                      ),
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    payload: dict = {
        'mandato': None,
    }
    mandato_obj = resolve_mandato_with_permissions(session, current_user, mandato_id)
    payload['mandato'] = MandatoSchema.model_validate(mandato_obj, from_attributes=True).model_dump()
    payload['input'] = text_input.text
    files, texts, referencias_file_uri = process_references(referencias, session, mandato_id, current_user)
    if texts:
        payload['references_text'] = texts
    try:
        content = call_llm(
            payload,
            files=files,
            prompt_template='expert_pl_sugestao_projetos',
            answer_template=ProjetoLei,
            session=session,
        )
        # Clean redundant titles from LLM response
        content = clean_llm_response(
            content,
            fields_to_clean=['justificativa', 'texto', 'ementa']
        )
    except Exception as e:
        logger.error(
            "Failed to create project via Expert PL",
            extra={
                "user_id": getattr(current_user, "id", None),
                "mandato_id": getattr(mandato_obj, "id", None),
                "referencias_file": referencias_file_uri,
                "files_count": len(files),
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        audit_logger.log(
            event_type="expert_pl.create_project.failed",
            payload={
                "error": str(e),
                "error_type": type(e).__name__,
                "referencias_file": referencias_file_uri,
                "files": [f.get("path") for f in files]
            },
            actor_user_id=getattr(current_user, "id", None),
            actor_mandato_id=getattr(mandato_obj, "id", None),
            actor_permission_level=getattr(current_user, "permission_level", None),
        )
        raise HTTPException(status_code=400, detail="Failed to generate project. Please verify your input and try again.")

    content['full_markdown'] = f"# Projeto de Lei\n\n{content.get('titulo', 'Sem título')}\n\n## Ementa\n\n{content.get('ementa', 'Sem ementa')}\n\n## Texto Completo\n\n{content.get('texto', 'Sem texto completo')}\n\n## Justificativa\n\n{content.get('justificativa', '')}" #Trocar por modelo com template de /templates

    audit_log = audit_logger.log(
        event_type="expert_pl.create_project.success",
        payload={
            "origem_legislativa": request.origem_legislativa,
            "referencias_text": len(payload.get('references_text', [])),
            "referencias_file": referencias_file_uri,
            "files": [f.get("path") for f in files],
        },
        response=content,
        actor_user_id=getattr(current_user, "id", None),
        actor_mandato_id=getattr(mandato_obj, "id", None),
        actor_permission_level=getattr(current_user, "permission_level", None),
    )
    response = generate_response(content)
    if hasattr(response, "headers"):
        response.headers["x-audit-log-id"] = str(audit_log.id)
    return response
