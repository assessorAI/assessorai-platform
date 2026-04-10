from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db.models import Mandato as MandatoORM
from ..db.models import User as UserORM
from ..db.session import get_session


router = APIRouter(
    prefix="/validation",
    tags=["validation"],
)


class ExistsResponse(BaseModel):
    exists: bool = Field(..., description="Indica se o registro informado já está cadastrado")


class MandatoValidationRequest(BaseModel):
    nome: str = Field(..., min_length=1, description="Nome parlamentar informado no cadastro")
    casa_legislativa: str = Field(..., min_length=1, description="Casa legislativa associada ao mandato")
    partido: Optional[str] = Field(None, description="Partido do parlamentar")
    cidade: str = Field(..., min_length=1, description="Município do mandato")
    uf: str = Field(..., min_length=1, max_length=2, description="UF do mandato")


def _normalize(value: Optional[str]) -> str:
    """Normalize strings for case-insensitive comparisons."""
    return (value or "").strip().lower()


@router.get("/email", response_model=ExistsResponse)
def validate_email(email: EmailStr, session: Session = Depends(get_session)) -> ExistsResponse:
    stmt = select(UserORM.id).where(func.lower(UserORM.email) == email.lower())
    exists = session.execute(stmt).scalar_one_or_none() is not None
    return ExistsResponse(exists=exists)


@router.get("/slug", response_model=ExistsResponse)
def validate_slug(slug: str, session: Session = Depends(get_session)) -> ExistsResponse:
    stmt = select(MandatoORM.id).where(MandatoORM.slug == slug.strip())
    exists = session.execute(stmt).scalar_one_or_none() is not None
    return ExistsResponse(exists=exists)


@router.post("/mandato", response_model=ExistsResponse)
def validate_mandato(
    payload: MandatoValidationRequest,
    session: Session = Depends(get_session),
) -> ExistsResponse:
    filters = [
        func.lower(func.coalesce(MandatoORM.nome_parlamentar, "")) == _normalize(payload.nome),
        func.lower(func.coalesce(MandatoORM.casa_legislativa, "")) == _normalize(payload.casa_legislativa),
        func.lower(func.coalesce(MandatoORM.municipio, "")) == _normalize(payload.cidade),
        func.lower(func.coalesce(MandatoORM.ue, "")) == _normalize(payload.uf),
    ]
    if payload.partido is not None:
        filters.append(
            func.lower(func.coalesce(MandatoORM.perfil_parlamentar, "")) == _normalize(payload.partido)
        )
    stmt = select(MandatoORM.id).where(*filters).limit(1)
    exists = session.execute(stmt).scalar_one_or_none() is not None
    return ExistsResponse(exists=exists)
