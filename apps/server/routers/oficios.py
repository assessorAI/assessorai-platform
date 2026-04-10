from typing import Optional
from fastapi import HTTPException, APIRouter, Depends, Request, Form
from pydantic import BaseModel, Field
from ..models import Mandato as MandatoSchema, form_factory
from ..db.session import get_session
from ..db.models import Mandato as MandatoORM
from sqlalchemy.orm import Session
from ..llm import call_llm, generate_response
from ..utils.reference_processor import process_references
from datetime import datetime
from fastapi.responses import JSONResponse
from .deps import get_current_user, resolve_mandato_with_permissions
from ..services.audit import AuditLogger, get_audit_logger
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/oficio",
    tags=["oficio"],
)

class OficioRequest(BaseModel):
    input: str = Field(
        ...,
        description="Texto da demanda cidadã",
        examples=["Falta de vaga em creche"],
    )


@router.post("/generate", response_model=dict)
async def generate_oficio(
    oficio_request: OficioRequest = form_factory(OficioRequest),
    referencias: Optional[str] = Form(None, description="JSON: lista de contextos", examples=[[{"type": "text", "content": "Natal"}]]),
    mandato_id: Optional[int] = None,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """Generate an oficio using Mandato data (if id provided) plus input and destino."""
    payload: dict = {
        'mandato': None,
    }
    
    # Resolve mandate with permissions; if not provided, inherit from user
    mandato_obj = resolve_mandato_with_permissions(session, current_user, mandato_id)
    mandato = MandatoSchema.model_validate(mandato_obj, from_attributes=True)
    payload['mandato'] = mandato.model_dump()
    # Inject oficio-specific fields
    payload['input'] = oficio_request.input
    payload['data'] = datetime.now().isoformat()
    files, texts, referencias_file_uri = process_references(referencias, session, mandato_id, current_user)
    if texts:
        payload['references_text'] = texts
    try:
        print("Payload for LLM:", payload)
        content = call_llm(payload, files=files, prompt_template='generate_oficio', session=session)
    except ValueError as e:
        logger.warning(
            "Invalid input for oficio generation",
            extra={
                "user_id": getattr(current_user, "id", None),
                "mandato_id": getattr(mandato_obj, "id", None),
                "error": str(e)
            }
        )
        audit_logger.log(
            event_type="oficio.generate.failed",
            payload={"error": str(e), "input": oficio_request.input, "referencias_file": referencias_file_uri, "files": [f.get("path") for f in files]},
            actor_user_id=getattr(current_user, "id", None),
            actor_mandato_id=getattr(mandato_obj, "id", None),
            actor_permission_level=getattr(current_user, "permission_level", None),
        )
        return JSONResponse(
            status_code=400,
            content={"detail": str(e)}
        )
    except Exception as e:
        logger.error(
            "Failed to generate oficio",
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
            event_type="oficio.generate.error",
            payload={"error": str(e), "error_type": type(e).__name__, "referencias_file": referencias_file_uri, "files": [f.get("path") for f in files]},
            actor_user_id=getattr(current_user, "id", None),
            actor_mandato_id=getattr(mandato_obj, "id", None),
            actor_permission_level=getattr(current_user, "permission_level", None),
        )
        return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor."})

    log_entry = audit_logger.log(
        event_type="oficio.generate.success",
        payload={
            "input": oficio_request.input,
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
        response.headers["x-audit-log-id"] = str(log_entry.id)
    return response
