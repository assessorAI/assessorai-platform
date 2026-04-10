from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..db.models import PromptTemplate as PromptTemplateORM, User as UserORM
from ..db.session import get_session
from ..models import (
    PromptTemplate,
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateListItem,
    PromptTemplateType,
    PromptTemplateFileContent,
)
from ..routers.deps import require_admin_user, get_current_user
from ..services.audit import AuditLogger, get_audit_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/prompts", tags=["admin/prompts"])

# Known template types with display names
TEMPLATE_TYPES = {
    "generate_oficio": "Geração de Ofícios",
    "expert_pl_constitucionalidade": "Análise de Constitucionalidade",
    "expert_pl_criar_emenda": "Criação de Emendas",
    "expert_pl_sugestao_emendas": "Sugestão de Emendas",
    "expert_pl_sugestao_projetos": "Sugestão de Projetos",
}


@router.get("/types", response_model=List[PromptTemplateType])
async def list_template_types(
    *,
    session: Session = Depends(get_session),
    current_admin: UserORM = require_admin_user,
) -> List[PromptTemplateType]:
    """List all template types with metadata about versions and file availability"""
    
    result = []
    for template_type, display_name in TEMPLATE_TYPES.items():
        # Check if file exists
        file_path = f"prompts/{template_type}.md"
        file_exists = os.path.exists(file_path)
        
        # Count database versions
        db_count = session.scalar(
            select(func.count(PromptTemplateORM.id))
            .where(PromptTemplateORM.template_type == template_type)
        ) or 0
        
        # Get default version if exists
        default_template = session.scalar(
            select(PromptTemplateORM)
            .where(
                PromptTemplateORM.template_type == template_type,
                PromptTemplateORM.is_default == True,
                PromptTemplateORM.is_active == True
            )
        )
        
        result.append(PromptTemplateType(
            type=template_type,
            display_name=display_name,
            file_exists=file_exists,
            db_versions_count=db_count,
            default_version=default_template.version if default_template else None,
            has_active_default=default_template is not None,
        ))
    
    return result


@router.get("/", response_model=List[PromptTemplateListItem])
async def list_all_templates(
    *,
    session: Session = Depends(get_session),
    current_admin: UserORM = require_admin_user,
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> List[PromptTemplateListItem]:
    """List all prompt templates with optional filtering"""
    
    statement = select(PromptTemplateORM).order_by(
        PromptTemplateORM.template_type,
        PromptTemplateORM.version.desc()
    )
    
    if template_type:
        statement = statement.where(PromptTemplateORM.template_type == template_type)
    if is_active is not None:
        statement = statement.where(PromptTemplateORM.is_active == is_active)
    
    statement = statement.offset(offset).limit(limit)
    results = session.execute(statement).scalars().all()
    
    return [_to_list_item_schema(t) for t in results]


@router.get("/{template_type}/versions", response_model=List[PromptTemplateListItem])
async def list_template_versions(
    template_type: str,
    session: Session = Depends(get_session),
    current_admin: UserORM = require_admin_user,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
) -> List[PromptTemplateListItem]:
    """List all versions of a specific template type"""
    
    if template_type not in TEMPLATE_TYPES:
        raise HTTPException(status_code=404, detail=f"Template type '{template_type}' not recognized")
    
    statement = select(PromptTemplateORM).where(
        PromptTemplateORM.template_type == template_type
    ).order_by(PromptTemplateORM.version.desc())
    
    if is_active is not None:
        statement = statement.where(PromptTemplateORM.is_active == is_active)
    
    results = session.execute(statement).scalars().all()
    return [_to_list_item_schema(t) for t in results]


@router.get("/{template_type}/file-content", response_model=PromptTemplateFileContent)
async def get_template_file_content(
    template_type: str,
    session: Session = Depends(get_session),
    current_admin: UserORM = require_admin_user,
) -> PromptTemplateFileContent:
    """Get the file-based template content for comparison"""
    
    if template_type not in TEMPLATE_TYPES:
        raise HTTPException(status_code=404, detail=f"Template type '{template_type}' not recognized")
    
    file_path = f"prompts/{template_type}.md"
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File template for '{template_type}' not found at {file_path}"
        )
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return PromptTemplateFileContent(
        template_type=template_type,
        content=content,
        source="file"
    )


@router.get("/{template_type}/{version}", response_model=PromptTemplate)
async def get_template_version(
    template_type: str,
    version: int,
    session: Session = Depends(get_session),
    current_admin: UserORM = require_admin_user,
) -> PromptTemplate:
    """Get a specific version of a template"""
    
    template = session.scalar(
        select(PromptTemplateORM).where(
            PromptTemplateORM.template_type == template_type,
            PromptTemplateORM.version == version
        )
    )
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_type}' version {version} not found"
        )
    
    return _to_full_schema(template)


@router.post("/", response_model=PromptTemplate)
async def create_template_version(
    *,
    session: Session = Depends(get_session),
    current_admin: UserORM = require_admin_user,
    audit: AuditLogger = Depends(get_audit_logger),
    payload: PromptTemplateCreate,
) -> PromptTemplate:
    """Create a new version of a prompt template"""
    
    if payload.template_type not in TEMPLATE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Template type '{payload.template_type}' not recognized"
        )
    
    # Get next version number
    max_version = session.scalar(
        select(func.max(PromptTemplateORM.version))
        .where(PromptTemplateORM.template_type == payload.template_type)
    )
    next_version = (max_version or 0) + 1
    
    # Create new template
    new_template = PromptTemplateORM(
        template_type=payload.template_type,
        version=next_version,
        content=payload.content,
        description=payload.description,
        is_default=False,  # New versions are not default by default
        is_active=True,
        created_by=current_admin.id,
        created_at=datetime.now(timezone.utc),
    )
    
    session.add(new_template)
    session.commit()
    session.refresh(new_template)
    
    # Log audit event
    audit.log(
        event_type="prompt_template_created",
        actor_user_id=current_admin.id,
        subject_id=str(new_template.id),
        payload={
            "template_type": payload.template_type,
            "version": next_version,
            "description": payload.description,
        },
        notes=f"Created prompt template '{payload.template_type}' version {next_version}"
    )
    
    logger.info(
        f"Created prompt template version",
        extra={
            "template_type": payload.template_type,
            "version": next_version,
            "created_by": current_admin.id
        }
    )
    
    return _to_full_schema(new_template)


@router.put("/{template_id}", response_model=PromptTemplate)
async def update_template_metadata(
    template_id: int,
    payload: PromptTemplateUpdate,
    session: Session = Depends(get_session),
    current_admin: UserORM = require_admin_user,
    audit: AuditLogger = Depends(get_audit_logger),
) -> PromptTemplate:
    """Update template metadata (description, content, or active status)"""
    
    template = session.get(PromptTemplateORM, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Track what changed
    changes = {}
    
    if payload.description is not None:
        template.description = payload.description
        changes["description"] = payload.description
    
    if payload.content is not None:
        template.content = payload.content
        changes["content_updated"] = True
    
    if payload.is_active is not None:
        template.is_active = payload.is_active
        changes["is_active"] = payload.is_active
    
    template.updated_at = datetime.now(timezone.utc)
    
    session.commit()
    session.refresh(template)
    
    # Log audit event
    audit.log(
        event_type="prompt_template_updated",
        actor_user_id=current_admin.id,
        subject_id=str(template.id),
        payload={
            "template_type": template.template_type,
            "version": template.version,
            "changes": changes,
        },
        notes=f"Updated prompt template '{template.template_type}' version {template.version}"
    )
    
    logger.info(
        f"Updated prompt template",
        extra={
            "template_id": template_id,
            "template_type": template.template_type,
            "version": template.version,
            "changes": list(changes.keys()),
            "updated_by": current_admin.id
        }
    )
    
    return _to_full_schema(template)


@router.delete("/{template_id}", response_model=PromptTemplate)
async def soft_delete_template(
    template_id: int,
    session: Session = Depends(get_session),
    current_admin: UserORM = require_admin_user,
    audit: AuditLogger = Depends(get_audit_logger),
) -> PromptTemplate:
    """Soft delete a template (set is_active=False)"""
    
    template = session.get(PromptTemplateORM, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if not template.is_active:
        raise HTTPException(status_code=400, detail="Template is already inactive")
    
    # Cannot delete the default version
    if template.is_default:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the default version. Set another version as default first."
        )
    
    template.is_active = False
    template.updated_at = datetime.now(timezone.utc)
    
    session.commit()
    session.refresh(template)
    
    # Log audit event
    audit.log(
        event_type="prompt_template_deleted",
        actor_user_id=current_admin.id,
        subject_id=str(template.id),
        payload={
            "template_type": template.template_type,
            "version": template.version,
        },
        notes=f"Soft deleted prompt template '{template.template_type}' version {template.version}"
    )
    
    logger.info(
        f"Soft deleted prompt template",
        extra={
            "template_id": template_id,
            "template_type": template.template_type,
            "version": template.version,
            "deleted_by": current_admin.id
        }
    )
    
    return _to_full_schema(template)


@router.delete("/{template_id}/permanent", status_code=200)
async def hard_delete_template(
    template_id: int,
    session: Session = Depends(get_session),
    current_admin: UserORM = require_admin_user,
    audit: AuditLogger = Depends(get_audit_logger),
) -> dict:
    """Permanently delete a template from database (hard delete)
    
    WARNING: This action is irreversible. Use with caution.
    """
    
    template = session.get(PromptTemplateORM, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Cannot delete the default version
    if template.is_default:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the default version. Set another version as default first."
        )
    
    # Store info before deleting
    template_type = template.template_type
    version = template.version
    
    # Log audit event BEFORE deletion
    audit.log(
        event_type="prompt_template_permanently_deleted",
        actor_user_id=current_admin.id,
        subject_id=str(template.id),
        payload={
            "template_type": template_type,
            "version": version,
        },
        notes=f"Permanently deleted prompt template '{template_type}' version {version}"
    )
    
    logger.warning(
        f"Permanently deleted prompt template",
        extra={
            "template_id": template_id,
            "template_type": template_type,
            "version": version,
            "deleted_by": current_admin.id
        }
    )
    
    # Hard delete from database
    session.delete(template)
    session.commit()
    
    return {
        "message": "Template permanently deleted",
        "template_type": template_type,
        "version": version
    }


@router.post("/{template_id}/set-default", response_model=PromptTemplate)
async def set_default_template(
    template_id: int,
    session: Session = Depends(get_session),
    current_admin: UserORM = require_admin_user,
    audit: AuditLogger = Depends(get_audit_logger),
) -> PromptTemplate:
    """Set a template version as the default for its type"""
    
    template = session.get(PromptTemplateORM, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if not template.is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot set an inactive template as default. Activate it first."
        )
    
    if template.is_default:
        raise HTTPException(status_code=400, detail="This version is already the default")
    
    # Unset current default for this template type
    current_default = session.scalar(
        select(PromptTemplateORM).where(
            PromptTemplateORM.template_type == template.template_type,
            PromptTemplateORM.is_default == True
        )
    )
    
    old_version = None
    if current_default:
        old_version = current_default.version
        current_default.is_default = False
        current_default.updated_at = datetime.now(timezone.utc)
        # Flush to unset old default before setting new one (avoids unique constraint violation)
        session.flush()
    
    # Set new default
    template.is_default = True
    template.updated_at = datetime.now(timezone.utc)
    
    session.commit()
    session.refresh(template)
    
    # Log audit event
    audit.log(
        event_type="prompt_template_default_changed",
        actor_user_id=current_admin.id,
        subject_id=str(template.id),
        payload={
            "template_type": template.template_type,
            "old_default_version": old_version,
            "new_default_version": template.version,
        },
        notes=f"Set prompt template '{template.template_type}' version {template.version} as default"
    )
    
    logger.info(
        f"Set default prompt template",
        extra={
            "template_id": template_id,
            "template_type": template.template_type,
            "old_version": old_version,
            "new_version": template.version,
            "set_by": current_admin.id
        }
    )
    
    return _to_full_schema(template)


# Helper functions for schema conversion
def _to_list_item_schema(template: PromptTemplateORM) -> PromptTemplateListItem:
    return PromptTemplateListItem(
        id=template.id,
        template_type=template.template_type,
        version=template.version,
        is_default=template.is_default,
        is_active=template.is_active,
        created_at=template.created_at,
        description=template.description,
    )


def _to_full_schema(template: PromptTemplateORM) -> PromptTemplate:
    return PromptTemplate(
        id=template.id,
        template_type=template.template_type,
        version=template.version,
        content=template.content,
        description=template.description,
        is_default=template.is_default,
        is_active=template.is_active,
        created_by=template.created_by,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )
