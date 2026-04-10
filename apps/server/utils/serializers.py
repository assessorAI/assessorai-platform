from __future__ import annotations

from typing import Any, Dict, List

from ..db.models import Mandato as MandatoORM, User as UserORM
from ..models import Mandato as MandatoSchema, User as UserSchema, UserMeOut, UserOut


def serialize_mandato(mandato: MandatoORM, *, include_users: bool = False) -> Dict[str, Any]:
    schema = MandatoSchema.model_validate(mandato, from_attributes=True)
    data = schema.model_dump(exclude={"users"})
    # profile_image_url e sempre o path fixo do endpoint — sem armazenar URL no banco
    data["profile_image_url"] = f"/mandatos/{mandato.id}/profile_image"
    if include_users:
        data["users"] = [u.id for u in getattr(mandato, "users", []) or []]
    return data


def serialize_user_core(user: UserORM, *, include_id: bool = True) -> Dict[str, Any]:
    base = UserSchema.model_validate(user, from_attributes=True).model_dump()
    if include_id:
        base["id"] = getattr(user, "id", None)
    base["last_login"] = getattr(user, "last_login_at", None)
    base["mandato"] = [serialize_mandato(m, include_users=False) for m in getattr(user, "mandatos", []) or []]
    return base


def build_user_out(user: UserORM) -> UserOut:
    return UserOut(**serialize_user_core(user))


def build_user_me_out(user: UserORM) -> UserMeOut:
    payload = serialize_user_core(user)
    mandatos: List[MandatoORM] = list(getattr(user, "mandatos", []) or [])
    if mandatos:
        first = mandatos[0]
        payload.setdefault("casa_legislativa", getattr(first, "casa_legislativa", None))
        payload.setdefault("municipio", getattr(first, "municipio", None))
        payload.setdefault("ue", getattr(first, "ue", None))
        payload.setdefault("cargo_parlamentar", getattr(first, "cargo_parlamentar", None))
    return UserMeOut(**payload)
