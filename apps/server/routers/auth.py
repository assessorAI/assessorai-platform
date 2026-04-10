from datetime import datetime, timedelta, timezone
import os
import secrets
from typing import Optional, cast, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..models import User as UserSchema, UserOut, UserMeOut, Token
from ..models import Mandato as MandatoSchema, MandatoOut, PermissionLevel
from ..models import ForgotPasswordRequest, ResetPasswordRequest, MessageResponse
from ..models import ActivateUserRequest, ActivateUserTokenResponse

from ..db.session import get_session
from ..db.models import User as UserORM, AuthToken as AuthTokenORM, Mandato as MandatoORM
from ..db.models import PasswordResetToken as PasswordResetTokenORM, UserActivationToken as UserActivationTokenORM
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..utils.security import verify_password, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from ..utils.serializers import build_user_me_out, build_user_out, serialize_user_core
from ..services.sendgrid_service import get_email_service
from ..services.audit import AuditLogger
from ..utils.config import get_frontend_url


def utc_now_naive() -> datetime:
    """
    Returns current UTC time as naive datetime for database storage.
    Database DateTime columns are stored as naive UTC (no timezone info).
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Rate limiter for auth routes (disabled during tests to avoid accumulated rate limit errors)
limiter = Limiter(key_func=get_remote_address, enabled=not bool(os.getenv("PYTEST_CURRENT_TEST")))

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


class UserInDB(UserSchema):
    hashed_password: str  # somente para typing local
    mandato: List[MandatoOut] = Field(default_factory=list)


class UserCreate(UserSchema):
    password: str
    mandato: List[MandatoSchema] = Field(default_factory=list)
    query_params: Optional[Dict[str, str]] = Field(None, description="Query parameters do frontend (UTM, custom params, etc)")


def authenticate_user(session: Session, email: str, password: str) -> Optional[UserInDB]:
    user = session.scalar(select(UserORM).where(UserORM.email == email))
    if not user:
        return None
    
    # Verifica se o usuário está ativo
    if not getattr(user, 'is_active', True):
        return None
    
    if not verify_password(password, cast(str, user.hashed_password)):
        return None
    base_data = UserSchema.model_validate(user, from_attributes=True).model_dump()
    mandatos_payload = serialize_user_core(user, include_id=False)["mandato"]
    base_data["mandato"] = [MandatoOut(**m) for m in mandatos_payload]
    return UserInDB(**base_data, hashed_password=cast(str, user.hashed_password))


@router.post("/register", response_model=UserOut)
def register(
    user: UserCreate,
    request: Request,
    session: Session = Depends(get_session)
):
    exists = session.scalar(select(UserORM).where(UserORM.email == user.email))
    if exists:
        raise HTTPException(status_code=400, detail="User already registered")
    hashed_password = get_password_hash(user.password)
    
    # Preparar dados do usuário, excluindo campos que não vão direto pro banco
    user_data = user.model_dump(exclude={"password", "mandato", "query_params"})
    
    # Captura query params da URL
    url_query_params = dict(request.query_params)
    
    # Mescla: body JSON tem prioridade sobre URL query params
    all_params = {**url_query_params, **(user.query_params or {})}
    
    # Processar e salvar no campo acquisition_data como JSONB
    if all_params:
        acquisition_data: Dict[str, Any] = {
            **all_params,
            "captured_at": utc_now_naive().isoformat()
        }
        user_data["acquisition_data"] = acquisition_data
    
    obj = UserORM(**user_data, hashed_password=hashed_password)
    session.add(obj)
    session.flush()

    mandato_payloads: List[MandatoSchema] = list(user.mandato or [])
    if not mandato_payloads:
        default_nome = f"{user.first_name} {user.last_name}".strip() or None
        mandato_payloads = [MandatoSchema(nome_parlamentar=default_nome)]

    for mandato_schema in mandato_payloads:
        mandato_data = mandato_schema.model_dump(exclude={"id", "users"}, exclude_unset=True)
        mandato_obj = MandatoORM(**mandato_data)
        mandato_obj.users.append(obj)
        session.add(mandato_obj)

    session.commit()
    session.refresh(obj)
    return build_user_out(obj)


@router.post("/token", response_model=Token)
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):

    user = authenticate_user(session, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    login_at = utc_now_naive()
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_str = secrets.token_urlsafe(32)
    user_orm = session.scalar(select(UserORM).where(UserORM.email == user.email))
    auth_token = AuthTokenORM(token=token_str, user_id=user_orm.id, expires_at=login_at + expires)
    session.add(auth_token)
    session.commit()
    
    # Log successful login for analytics
    audit_logger = AuditLogger(session)
    first_mandato_id = None
    if user.mandato and len(user.mandato) > 0:
        first_mandato_id = user.mandato[0].id
    
    audit_logger.log(
        event_type="auth:login",
        actor_user_id=user_orm.id,
        actor_mandato_id=first_mandato_id,
        actor_permission_level=user.permission_level,
        notes=f"Login successful for {user.email}"
    )

    # Persist last login for cheap list ordering.
    # Policy: update ALL mandatos associated with the user.
    user_orm.last_login_at = login_at
    for mandato in getattr(user_orm, "mandatos", []) or []:
        mandato.last_login_at = login_at
        mandato.last_login_user_id = user_orm.id
    session.add(user_orm)
    session.commit()
    
    token_response = Token(access_token=token_str, token_type="bearer", expiration_date=auth_token.expires_at)

    return token_response


# Dependência para obter o usuário atual via OAuth2PasswordBearer
@router.get("/me", response_model=UserMeOut)
def read_users_me(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
):
    auth_token = session.scalar(select(AuthTokenORM).where(AuthTokenORM.token == token))
    if not auth_token or auth_token.expires_at < utc_now_naive():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    new_expires_at = utc_now_naive() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    auth_token.expires_at = new_expires_at
    session.commit()
    user = session.scalar(select(UserORM).where(UserORM.id == auth_token.user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return build_user_me_out(user)


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute")
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    session: Session = Depends(get_session),
):
    """
    Solicita recuperação de senha. Envia um e-mail com link de reset se o e-mail existir.
    Por segurança, sempre retorna a mesma mensagem mesmo se o e-mail não existir.
    """
    user = session.scalar(select(UserORM).where(UserORM.email == payload.email))
    
    if user:
        # Gera token único e seguro
        token_str = secrets.token_urlsafe(32)
        expires = timedelta(hours=1)
        
        reset_token = PasswordResetTokenORM(
            token=token_str,
            user_id=user.id,
            expires_at=utc_now_naive() + expires,
            used=False
        )
        session.add(reset_token)
        session.commit()
        
        # Envia e-mail com link de recuperação
        email_service = get_email_service()
        if email_service.is_configured:
            frontend_url = get_frontend_url()
            reset_link = f"{frontend_url}/reset-password?token={token_str}"
            
            email_service.send_email(
                recipients=user.email,
                subject="Recuperação de Senha - AssessorAI",
                template_name="password_reset.md",
                template_context={
                    "first_name": user.first_name or "Usuário",
                    "reset_link": reset_link
                }
            )
    
    # Resposta genérica para evitar enumeração de e-mails
    return MessageResponse(
        message="Se o e-mail informado estiver cadastrado, você receberá instruções para redefinir sua senha."
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    request: ResetPasswordRequest,
    session: Session = Depends(get_session),
):
    """
    Redefine a senha do usuário usando o token recebido por e-mail.
    """
    # Busca o token
    reset_token = session.scalar(
        select(PasswordResetTokenORM).where(PasswordResetTokenORM.token == request.token)
    )
    
    # Valida token
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado"
        )
    
    if reset_token.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este token já foi utilizado"
        )
    
    if reset_token.expires_at < utc_now_naive():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expirado"
        )
    
    # Busca usuário
    user = session.scalar(select(UserORM).where(UserORM.id == reset_token.user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Atualiza senha
    user.hashed_password = get_password_hash(request.new_password)
    
    # Marca token como usado
    reset_token.used = True
    
    session.commit()
    
    return MessageResponse(message="Senha redefinida com sucesso")


@router.get("/activate", response_model=ActivateUserTokenResponse)
def verify_activation_token(
    token: str,
    session: Session = Depends(get_session),
):
    """
    Verifica o token de ativação e retorna o email do usuário.
    O frontend usa isso para exibir o email e abrir o formulário de cadastro.
    """
    # Busca o token
    activation_token = session.scalar(
        select(UserActivationTokenORM).where(UserActivationTokenORM.token == token)
    )
    
    # Valida token
    if not activation_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado"
        )
    
    if activation_token.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este token já foi utilizado"
        )

    if activation_token.expires_at < utc_now_naive():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expirado. Solicite um novo convite ao administrador do mandato."
        )
    
    # Busca usuário
    user = session.scalar(select(UserORM).where(UserORM.id == activation_token.user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Busca mandato
    mandato = session.scalar(select(MandatoORM).where(MandatoORM.id == activation_token.mandato_id))
    mandato_nome = mandato.nome_parlamentar if mandato else None
    
    return ActivateUserTokenResponse(
        email=user.email,
        mandato_nome=mandato_nome
    )


@router.post("/activate", response_model=UserOut)
def activate_user(
    request: ActivateUserRequest,
    session: Session = Depends(get_session),
):
    """
    Ativa o usuário completando seu cadastro com os dados fornecidos.
    """
    # Busca o token
    activation_token = session.scalar(
        select(UserActivationTokenORM).where(UserActivationTokenORM.token == request.token)
    )
    
    # Valida token
    if not activation_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado"
        )
    
    if activation_token.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este token já foi utilizado"
        )

    if activation_token.expires_at < utc_now_naive():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expirado"
        )
    
    # Busca usuário
    user = session.scalar(select(UserORM).where(UserORM.id == activation_token.user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Atualiza dados do usuário
    user.first_name = request.first_name
    user.last_name = request.last_name
    user.phone = request.phone
    user.role = request.role
    user.lgpd_check = request.lgpd_check
    user.hashed_password = get_password_hash(request.password)
    user.permission_level = PermissionLevel.user.value  # Promove de 'invited' para 'user'
    user.is_active = True  # Ativa o usuário
    
    # Marca token como usado
    activation_token.used = True
    
    session.commit()
    session.refresh(user)
    
    return build_user_out(user)
