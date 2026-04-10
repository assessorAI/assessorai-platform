from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
import secrets
import time
import logging
import os
from fastapi import HTTPException, APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
from pydantic import BaseModel, EmailStr, Field
from ..models import (
    Mandato as MandatoSchema,
    MandatoListOut,
    MandatoOut,
    User as UserSchema,
    UserOut,
    PermissionLevel,
)
from ..db.session import get_session
from ..db.models import (
    AuditLog as AuditLogORM,
    Mandato,
    User as UserORM,
    UserActivationToken as UserActivationTokenORM,
)
from ..utils.security import get_password_hash
from ..services.sendgrid_service import get_email_service
from ..utils.config import get_frontend_url
from ..utils.serializers import serialize_mandato
from ..utils.query_params import ci_in
from ..utils.slug import generate_unique_slug
from ..utils.google_creds import ensure_google_credentials_file
from ..utils.image import resize_and_crop
from .deps import get_current_user, resolve_mandato_with_permissions, resolve_mandato_by_id_or_slug, resolve_mandato_public

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/mandatos",
    tags=["mandatos"],
)

# Public router: endpoints accessible without authentication
public_router = APIRouter(
    prefix="/mandatos",
    tags=["mandatos"],
)

@router.post("/", response_model=MandatoOut)
def create_mandato(
    mandato: MandatoSchema,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    # Permissão: apenas Admin ou Manager
    if current_user.permission_level not in {PermissionLevel.admin.value, PermissionLevel.manager.value}:
        raise HTTPException(status_code=403, detail="Not authorized to create mandatos")

    data = mandato.model_dump(exclude={"users", "id", "slug", "profile_image_url"}, exclude_unset=True)
    obj = Mandato(**data)
    session.add(obj)
    # Adiciona o usuário criador ao mandato
    creator = session.scalar(select(UserORM).where(UserORM.email == current_user.email))
    if not creator:
        raise HTTPException(status_code=400, detail="Creator user not found in database")
    obj.users.append(creator)
    # Flush to get the id before generating the slug
    session.flush()

    # Generate or validate slug
    requested_slug = mandato.slug
    if requested_slug and requested_slug.strip():
        existing = session.scalar(select(Mandato).where(Mandato.slug == requested_slug).where(Mandato.id != obj.id))
        if existing:
            raise HTTPException(status_code=409, detail=f"Slug '{requested_slug}' já está em uso")
        obj.slug = requested_slug.strip()
    else:
        obj.slug = generate_unique_slug(
            mandato.nome_parlamentar, session, fallback_id=obj.id
        )

    session.commit()
    session.refresh(obj)
    return MandatoOut(**serialize_mandato(obj))


@router.get("/", response_model=dict)
def list_mandatos(
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of mandatos to return"),
    offset: int = Query(0, ge=0, description="Number of mandatos to skip"),
    search: Optional[str] = Query(None, description="Search by nome_parlamentar"),
    cargo_parlamentar: Optional[str] = Query(
        None,
        description="Filter by cargo_parlamentar (comma-separated for multiple values)",
    ),
    casa_legislativa: Optional[str] = Query(
        None,
        description="Filter by casa_legislativa (comma-separated for multiple values)",
    ),
    partido: Optional[str] = Query(None, description="Filter by partido (comma-separated for multiple values)"),
    perfil_parlamentar: Optional[str] = Query(
        None,
        description="Filter by perfil_parlamentar (comma-separated for multiple values)",
    ),
    espectro_politico: Optional[str] = Query(
        None,
        description="Filter by espectro_politico (comma-separated for multiple values)",
    ),
    from_dt: Optional[datetime] = Query(
        None,
        alias="from",
        description=(
            "Filter by last_login from (inclusive). "
            "Format: ISO 8601 / RFC3339 date-time (e.g. '2026-02-03T16:57:39Z' or "
            "'2026-02-03T16:57:39+00:00')."
        ),
    ),
    to_dt: Optional[datetime] = Query(
        None,
        alias="to",
        description=(
            "Filter by last_login to (inclusive). "
            "Format: ISO 8601 / RFC3339 date-time (e.g. '2026-02-03T16:57:39Z' or "
            "'2026-02-03T16:57:39+00:00')."
        ),
    ),
    order_by: Optional[str] = Query(
        None,
        alias="orderBy",
        description="Order by: nome_parlamentar, created_at, last_login. Prefix with '-' for DESC.",
    ),
):

    allowed_order_fields = {"nome_parlamentar", "created_at", "last_login"}
    desc = False
    order_field = (order_by or "").strip() or None
    if order_field and order_field.startswith("-"):
        desc = True
        order_field = order_field[1:]
    if order_field and order_field not in allowed_order_fields:
        allowed = ", ".join(sorted(allowed_order_fields))
        raise HTTPException(status_code=400, detail=f"Invalid orderBy. Allowed: {allowed}")

    def _ci_like(col, term: str):
        return func.lower(func.coalesce(col, "")).like(f"%{term.lower()}%")

    def _nulls_last_sort(col, *, desc: bool):
        if desc:
            return (col.is_(None)).asc(), col.desc()
        return (col.is_(None)).asc(), col.asc()

    def _to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
        if dt is None:
            return None
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    # Base filters
    base_filters = []
    cargo_clause = ci_in(Mandato.cargo_parlamentar, cargo_parlamentar)
    if cargo_clause is not None:
        base_filters.append(cargo_clause)
    casa_clause = ci_in(Mandato.casa_legislativa, casa_legislativa)
    if casa_clause is not None:
        base_filters.append(casa_clause)
    partido_clause = ci_in(Mandato.partido, partido)
    if partido_clause is not None:
        base_filters.append(partido_clause)
    perfil_clause = ci_in(Mandato.perfil_parlamentar, perfil_parlamentar)
    if perfil_clause is not None:
        base_filters.append(perfil_clause)
    espectro_clause = ci_in(Mandato.espectro_politico, espectro_politico)
    if espectro_clause is not None:
        base_filters.append(espectro_clause)
    if search:
        base_filters.append(_ci_like(Mandato.nome_parlamentar, search))

    # last_login range filters
    last_login_from = _to_naive_utc(from_dt)
    if last_login_from is not None:
        base_filters.append(Mandato.last_login_at >= last_login_from)
    last_login_to = _to_naive_utc(to_dt)
    if last_login_to is not None:
        base_filters.append(Mandato.last_login_at <= last_login_to)

    # Total count
    count_stmt = select(func.count()).select_from(Mandato)
    for f in base_filters:
        count_stmt = count_stmt.where(f)
    total_count = session.scalar(count_stmt) or 0

    # Fetch ordered ids first
    id_stmt = select(Mandato.id)
    for f in base_filters:
        id_stmt = id_stmt.where(f)

    if order_field == "nome_parlamentar":
        col = func.lower(func.coalesce(Mandato.nome_parlamentar, ""))
        order_exprs = [col.desc() if desc else col.asc(), Mandato.id.asc()]
    elif order_field == "created_at":
        order_exprs = [Mandato.created_at.desc() if desc else Mandato.created_at.asc(), Mandato.id.asc()]
    elif order_field == "last_login":
        order_exprs = [
            *_nulls_last_sort(Mandato.last_login_at, desc=desc),
            Mandato.id.asc(),
        ]
    else:
        order_exprs = [Mandato.id.asc()]

    id_stmt = id_stmt.order_by(*order_exprs).limit(limit).offset(offset)
    mandato_ids = list(session.execute(id_stmt).scalars().all())

    if not mandato_ids:
        return {"mandatos": [], "total": total_count, "limit": limit, "offset": offset}

    # Load mandatos with users
    mandatos = session.execute(
        select(Mandato)
        .options(selectinload(Mandato.users))
        .where(Mandato.id.in_(mandato_ids))
    ).scalars().all()
    mandato_by_id: Dict[int, Mandato] = {m.id: m for m in mandatos}

    # last_login: payload built from persisted mandato.last_login_*

    # numero_atividades (30d) per mandato (exclude login)
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
    activities_rows = session.execute(
        select(AuditLogORM.actor_mandato_id, func.count(AuditLogORM.id))
        .where(
            AuditLogORM.actor_mandato_id.in_(mandato_ids),
            AuditLogORM.created_at >= cutoff,
            AuditLogORM.event_type != "auth:login",
        )
        .group_by(AuditLogORM.actor_mandato_id)
    ).all()
    activities_map: Dict[int, int] = {
        mid: int(count) for mid, count in activities_rows if mid is not None
    }

    # Build response preserving order
    out: List[MandatoListOut] = []
    for mid in mandato_ids:
        m = mandato_by_id.get(mid)
        if not m:
            continue
        payload = serialize_mandato(m, include_users=True)

        # gerente users (Manager/Admin)
        gerente = []
        for u in getattr(m, "users", []) or []:
            level = (getattr(u, "permission_level", None) or "").lower()
            if level not in {PermissionLevel.admin.value.lower(), PermissionLevel.manager.value.lower()}:
                continue
            nome = f"{getattr(u, 'first_name', '') or ''} {getattr(u, 'last_name', '') or ''}".strip() or None
            gerente.append({"id": u.id, "nome": nome, "email": u.email})

        payload["gerente"] = gerente
        last_login_payload = None
        last_login_user_id = getattr(m, "last_login_user_id", None)
        last_login_at = getattr(m, "last_login_at", None)
        if last_login_user_id and last_login_at:
            email = None
            for u in getattr(m, "users", []) or []:
                if getattr(u, "id", None) == last_login_user_id:
                    email = getattr(u, "email", None)
                    break
            if not email:
                u = session.get(UserORM, last_login_user_id)
                email = getattr(u, "email", None) if u else None
            if email:
                last_login_payload = {"email": email, "date": last_login_at}

        payload["last_login"] = last_login_payload
        payload["numero_atividades"] = activities_map.get(mid, 0)

        out.append(MandatoListOut(**payload))

    return {"mandatos": out, "total": total_count, "limit": limit, "offset": offset}


@public_router.get("/{mandato_id_or_slug}", response_model=MandatoOut)
def get_mandato(mandato_id_or_slug: str, session: Session = Depends(get_session)):
    """Retorna um mandato por ID numérico ou slug. Endpoint público (sem autenticação)."""
    obj = resolve_mandato_public(session, mandato_id_or_slug)
    return MandatoOut(**serialize_mandato(obj, include_users=True))


@router.put("/{mandato_id}", response_model=MandatoOut)
def update_mandato(mandato_id: int, updated: MandatoSchema, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    obj = resolve_mandato_with_permissions(session, current_user, mandato_id)
    update_data = updated.model_dump(exclude_unset=True, exclude={"slug", "profile_image_url"})
    for k, v in update_data.items():
        setattr(obj, k, v)

    # Handle slug update
    requested_slug = updated.slug if "slug" in updated.model_fields_set else None
    if requested_slug is not None:
        if requested_slug.strip():
            existing = session.scalar(
                select(Mandato).where(Mandato.slug == requested_slug.strip()).where(Mandato.id != mandato_id)
            )
            if existing:
                raise HTTPException(status_code=409, detail=f"Slug '{requested_slug}' já está em uso")
            obj.slug = requested_slug.strip()
        else:
            # Empty slug: regenerate from current nome_parlamentar
            obj.slug = generate_unique_slug(
                getattr(obj, "nome_parlamentar", None),
                session,
                mandato_id=mandato_id,
                fallback_id=mandato_id,
            )
    elif "nome_parlamentar" in updated.model_fields_set and not getattr(obj, "slug", None):
        # If nome changed and there's no slug yet, generate one
        obj.slug = generate_unique_slug(
            updated.nome_parlamentar, session, mandato_id=mandato_id, fallback_id=mandato_id
        )

    session.add(obj)
    session.commit()
    session.refresh(obj)
    return MandatoOut(**serialize_mandato(obj, include_users=True))


_AVATAR_PLACEHOLDER: bytes = open(
    os.path.join(os.path.dirname(__file__), "..", "assets", "avatar.png"), "rb"
).read()


@public_router.get("/{mandato_id}/profile_image")
async def get_profile_image(mandato_id: int):
    """Serve a imagem de perfil do mandato. Retorna placeholder se não houver imagem."""
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if bucket_name:
        try:
            from google.cloud import storage as gcs
            ensure_google_credentials_file()
            blob = gcs.Client().bucket(bucket_name).blob(f"mandatos/{mandato_id}/profile.jpg")
            if blob.exists():
                blob.reload()
                return Response(
                    content=blob.download_as_bytes(),
                    media_type="image/jpeg",
                    # no-cache: sempre valida com o servidor antes de usar cache
                    headers={"Cache-Control": "no-cache", "ETag": str(blob.generation)},
                )
        except Exception as exc:
            logger.warning("Falha ao buscar imagem de perfil do GCS: %s", exc)

    return Response(
        content=_AVATAR_PLACEHOLDER,
        media_type="image/png",
        headers={"Cache-Control": "no-cache"},
    )


@router.put("/{mandato_id}/profile_image", response_model=dict)
async def update_profile_image(
    mandato_id: int,
    file: UploadFile = File(..., description="Imagem de perfil (JPEG, PNG ou WebP). Será redimensionada para 400x400."),
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Upload e processa a imagem de perfil do mandato (400×400 center-crop JPEG)."""
    resolve_mandato_with_permissions(session, current_user, mandato_id)

    content_type = file.content_type or ""
    raw_bytes = await file.read()

    try:
        processed = resize_and_crop(raw_bytes, content_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except OSError as exc:
        raise HTTPException(status_code=422, detail=f"Não foi possível processar a imagem: {exc}")

    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        raise HTTPException(status_code=500, detail="GCS_BUCKET_NAME não configurado")

    try:
        from google.cloud import storage as gcs
        ensure_google_credentials_file()
        blob = gcs.Client().bucket(bucket_name).blob(f"mandatos/{mandato_id}/profile.jpg")
        blob.upload_from_string(processed, content_type="image/jpeg")
    except Exception as exc:
        logger.error("Falha ao fazer upload da imagem de perfil: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Falha ao salvar imagem no GCS")

    return {"profile_image_url": f"/mandatos/{mandato_id}/profile_image?v={int(time.time())}"}


@router.delete("/{mandato_id}")
def delete_mandato(mandato_id: int, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    # Only admin/manager can delete mandatos
    if current_user.permission_level not in {PermissionLevel.admin.value, PermissionLevel.manager.value}:
        raise HTTPException(status_code=403, detail="Not authorized to delete mandatos")
    obj = session.get(Mandato, mandato_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Mandato not found")
    session.delete(obj)
    session.commit()
    return {"detail": "Mandato deleted"}


class MandatoUserAdd(BaseModel):
    email: EmailStr


@router.get("/{mandato_id}/users", response_model=dict)
def list_mandato_users(
    mandato_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of users to return"),
    offset: int = Query(0, ge=0, description="Number of users to skip"),
):
    obj = resolve_mandato_with_permissions(session, current_user, mandato_id)
    
    # Get total count and paginate the users list
    all_users = obj.users
    total_count = len(all_users)
    paginated_users = all_users[offset:offset + limit]
    
    out: List[UserOut] = []
    for u in paginated_users:
        data = UserSchema.model_validate(u, from_attributes=True).model_dump()
        out.append(UserOut(**data, id=u.id))
    
    return {
        "users": out,
        "total": total_count,
        "limit": limit,
        "offset": offset
    }


@router.post("/{mandato_id}/users", response_model=List[UserOut])
def add_user_to_mandato(
    mandato_id: int,
    body: MandatoUserAdd,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    Adiciona um usuário ao mandato.
    - Se o usuário já existe: adiciona ao mandato (comportamento anterior)
    - Se o usuário não existe: cria usuário inativo e envia email de ativação
    """
    # Permissão: Admin ou Manager
    if current_user.permission_level not in {PermissionLevel.admin.value, PermissionLevel.manager.value}:
        raise HTTPException(status_code=403, detail="Not authorized to modify mandato users")
    
    mandato = session.get(Mandato, mandato_id)
    if not mandato:
        raise HTTPException(status_code=404, detail="Mandato not found")
    
    # Verifica se usuário já existe
    user = session.scalar(select(UserORM).where(UserORM.email == body.email))
    
    if user:
        # Usuário já existe
        if user not in mandato.users:
            # Adiciona ao mandato
            mandato.users.append(user)
            session.add(mandato)
            session.commit()
            session.refresh(mandato)
        elif user.permission_level == PermissionLevel.invited and not user.is_active:
            # Usuário já no mandato como Invited: reenvia email de ativação
            # Gera novo token de ativação (válido por 7 dias)
            token_str = secrets.token_urlsafe(32)
            expires = timedelta(days=7)
            
            activation_token = UserActivationTokenORM(
                token=token_str,
                user_id=user.id,
                mandato_id=mandato.id,
                expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + expires,
                used=False
            )
            session.add(activation_token)
            session.commit()
            
            # Envia email de ativação
            email_service = get_email_service()
            logger.info(f"Re-sending activation email to existing invited user {user.email} for mandato {mandato_id}")
            logger.debug(f"Email service configured: {email_service.is_configured}")
            
            if email_service.is_configured:
                frontend_url = get_frontend_url()
                activation_link = f"{frontend_url}/register-member?token={token_str}"
                logger.debug(f"Activation link generated: {activation_link}")
                
                if not user.email:
                    raise HTTPException(status_code=400, detail="Usuário sem email cadastrado")
                status_code = email_service.send_email(
                    recipients=user.email,
                    subject="Convite para participar do AssessorAI",
                    template_name="user_activation.md",
                    template_context={
                        "mandato_nome": mandato.nome_parlamentar or "um mandato",
                        "activation_link": activation_link
                    }
                )
                
                if status_code and 200 <= status_code < 300:
                    logger.info(f"Activation email re-sent successfully to {user.email}, status: {status_code}")
                else:
                    logger.warning(f"Failed to re-send activation email to {user.email}, status: {status_code}")
            else:
                logger.error(f"Cannot re-send activation email to {user.email}: email service not configured. Check SENDGRID_API_KEY and SENDGRID_SENDER_EMAIL environment variables.")
            
            session.refresh(mandato)
    else:
        # Usuário não existe: cria usuário inativo e envia email de ativação
        
        # Gera senha temporária aleatória
        temp_password = secrets.token_urlsafe(16)
        
        # Cria usuário inativo com apenas email e permissão 'invited'
        new_user = UserORM(
            email=body.email,
            first_name=None,
            last_name=None,
            phone=None,
            permission_level=PermissionLevel.invited.value,
            lgpd_check=False,
            role=None,
            hashed_password=get_password_hash(temp_password),
            is_active=False
        )
        session.add(new_user)
        session.flush()  # Para obter o user.id
        
        # Adiciona ao mandato
        mandato.users.append(new_user)
        session.add(mandato)
        session.flush()
        
        # Gera token de ativação (válido por 7 dias)
        token_str = secrets.token_urlsafe(32)
        expires = timedelta(days=7)
        
        activation_token = UserActivationTokenORM(
            token=token_str,
            user_id=new_user.id,
            mandato_id=mandato.id,
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + expires,
            used=False
        )
        session.add(activation_token)
        session.commit()
        
        # Envia email de ativação
        email_service = get_email_service()
        logger.info(f"Attempting to send activation email to {body.email} for mandato {mandato_id}")
        logger.debug(f"Email service configured: {email_service.is_configured}")
        
        if email_service.is_configured:
            frontend_url = get_frontend_url()
            activation_link = f"{frontend_url}/register-member?token={token_str}"
            logger.debug(f"Activation link generated: {activation_link}")
            
            status_code = email_service.send_email(
                recipients=body.email,
                subject="Convite para participar do AssessorAI",
                template_name="user_activation.md",
                template_context={
                    "mandato_nome": mandato.nome_parlamentar or "um mandato",
                    "activation_link": activation_link
                }
            )
            
            if status_code and 200 <= status_code < 300:
                logger.info(f"Activation email sent successfully to {body.email}, status: {status_code}")
            else:
                logger.warning(f"Failed to send activation email to {body.email}, status: {status_code}")
        else:
            logger.error(f"Cannot send activation email to {body.email}: email service not configured. Check SENDGRID_API_KEY and SENDGRID_SENDER_EMAIL environment variables.")
        
        session.refresh(mandato)
    
    # Retorna lista atualizada de usuários
    out: List[UserOut] = []
    for u in mandato.users:
        data = UserSchema.model_validate(u, from_attributes=True).model_dump()
        out.append(UserOut(**data, id=u.id))
    return out


@router.delete("/{mandato_id}/users/{user_id}", response_model=List[UserOut])
def remove_user_from_mandato(
    mandato_id: int,
    user_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    if current_user.permission_level not in {PermissionLevel.admin, PermissionLevel.manager}:
        raise HTTPException(status_code=403, detail="Not authorized to modify mandato users")

    mandato = session.get(Mandato, mandato_id)
    if not mandato:
        raise HTTPException(status_code=404, detail="Mandato not found")

    user = session.get(UserORM, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user in mandato.users:
        mandato.users.remove(user)

        # If this user was tracked as the mandato's last_login user, clear it.
        if getattr(mandato, "last_login_user_id", None) == user_id:
            mandato.last_login_user_id = None
            mandato.last_login_at = None
        session.add(mandato)
        session.commit()
        session.refresh(mandato)

    out: List[UserOut] = []
    for u in mandato.users:
        data = UserSchema.model_validate(u, from_attributes=True).model_dump()
        out.append(UserOut(**data, id=u.id))
    return out
