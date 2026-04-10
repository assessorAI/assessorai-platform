import logging
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.session import get_session
from ..db.models import User as UserORM, Mandato as MandatoORM, AuthToken
from ..models import PermissionLevel
from datetime import datetime, timezone
from ..services.vector_store import VectorStorePgVector
from ..services.embeddings import get_embedding_provider
from ..services.embeddings import EmbeddingProvider


logger = logging.getLogger(__name__)
# DEBUG level is controlled by the DEBUG env var in main.py


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")



def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> UserORM:
    """Valida o usuário autenticado via Bearer token e retorna o User ORM."""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    auth_token = session.scalar(select(AuthToken).where(AuthToken.token == token))
    if not auth_token or auth_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return auth_token.user


def resolve_mandato_with_permissions(
    session: Session,
    current_user: UserORM,
    mandato_id: Optional[int],
) -> MandatoORM:
    """Resolve a Mandato respecting permissions.
    - If mandato_id provided: allow only if admin/manager or user is member.
    - If not provided: inherit from user; if none or multiple, raise 400.
    """
    logger.debug(
        "Resolve mandato: mandato_id=%s user_id=%s level=%s",
        mandato_id, getattr(current_user, "id", None), getattr(current_user, "permission_level", None)
    )
    if mandato_id:
        mandato = session.get(MandatoORM, mandato_id)
        if not mandato:
            logger.debug("Mandato %s não encontrado", mandato_id)
            raise HTTPException(status_code=404, detail="Mandato não encontrado")
        # Only admin/manager or users associated with mandato allowed
        if not (getattr(current_user, "permission_level", None) in (PermissionLevel.admin.value, PermissionLevel.manager.value)
                or any(u.id == current_user.id for u in mandato.users)):
            logger.debug("Sem permissão: user_id=%s não pertence ao mandato %s e não é admin/manager",
                         getattr(current_user, "id", None), mandato_id)
            raise HTTPException(status_code=403, detail="Sem permissão para acessar este mandato")
        return mandato

    # inherit from user's mandates
    user_mandatos = list(current_user.mandatos or [])
    logger.debug("Usuário possui %d mandatos associados", len(user_mandatos))
    if len(user_mandatos) == 0:
        raise HTTPException(status_code=400, detail="Usuário não está vinculado a mandato. Informe mandato_id.")
    if len(user_mandatos) > 1:
        raise HTTPException(status_code=400, detail="Usuário possui múltiplos mandatos. Informe mandato_id.")
    return user_mandatos[0]


def _lookup_mandato_by_id_or_slug(session: Session, mandato_id_or_slug: str) -> MandatoORM:
    """Lookup a Mandato by numeric ID or slug without any permission check."""
    try:
        numeric_id = int(mandato_id_or_slug)
        mandato = session.get(MandatoORM, numeric_id)
    except (ValueError, TypeError):
        mandato = session.scalar(
            select(MandatoORM).where(MandatoORM.slug == mandato_id_or_slug)
        )
    if not mandato:
        raise HTTPException(status_code=404, detail="Mandato não encontrado")
    return mandato


def resolve_mandato_by_id_or_slug(
    session: Session,
    current_user: UserORM,
    mandato_id_or_slug: str,
) -> MandatoORM:
    """Resolve a Mandato by numeric ID or by slug, then check permissions.

    Tries to parse ``mandato_id_or_slug`` as an integer first; falls back to
    a slug lookup when the value is not numeric.
    """
    logger.debug(
        "Resolve mandato by id_or_slug: value=%s user_id=%s",
        mandato_id_or_slug, getattr(current_user, "id", None),
    )
    mandato = _lookup_mandato_by_id_or_slug(session, mandato_id_or_slug)

    # Permission check: admin/manager or member
    is_privileged = getattr(current_user, "permission_level", None) in (
        PermissionLevel.admin.value, PermissionLevel.manager.value
    )
    is_member = any(u.id == current_user.id for u in mandato.users)
    if not (is_privileged or is_member):
        raise HTTPException(status_code=403, detail="Sem permissão para acessar este mandato")

    return mandato


def resolve_mandato_public(session: Session, mandato_id_or_slug: str) -> MandatoORM:
    """Resolve a Mandato by numeric ID or slug without any authentication/permission check."""
    logger.debug("Resolve mandato public: value=%s", mandato_id_or_slug)
    return _lookup_mandato_by_id_or_slug(session, mandato_id_or_slug)


def require_roles(*allowed_roles):
    """Dependency factory to require user permission levels."""
    def _require(current_user: UserORM = Depends(get_current_user)):
        level = getattr(current_user, "permission_level", None)
        if level not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        return current_user
    return Depends(_require)


require_admin_user = require_roles(PermissionLevel.admin.value)



def get_vector_store(session: Session = Depends(get_session)) -> VectorStorePgVector:
    return VectorStorePgVector(session)



def get_embedding_provider_dep() -> EmbeddingProvider:
    return get_embedding_provider()
