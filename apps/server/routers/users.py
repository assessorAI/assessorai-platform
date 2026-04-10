import secrets
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from ..db.session import get_session
from ..db.models import User as UserORM, Mandato as MandatoORM
from ..models import PermissionLevel, UserOut, UserMeOut, Mandato as MandatoSchema
from ..utils.query_params import ci_in
from ..utils.security import get_password_hash
from ..utils.serializers import build_user_me_out, build_user_out, serialize_user_core
from .deps import get_current_user

ADMIN_LEVELS = {PermissionLevel.admin.value, PermissionLevel.manager.value}


def _is_admin(user: UserORM) -> bool:
    return getattr(user, "permission_level", None) in ADMIN_LEVELS


def _require_admin(user: UserORM) -> None:
    if not _is_admin(user):
        raise HTTPException(status_code=403, detail="Not authorized")

router = APIRouter(
    prefix="/user",
    tags=["user"],
)


class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: str
    permission_level: PermissionLevel
    lgpd_check: bool
    role: str
    password: Optional[str] = Field(None, min_length=6)
    mandato: List[MandatoSchema] = Field(default_factory=list)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    permission_level: Optional[PermissionLevel] = None
    lgpd_check: Optional[bool] = None
    role: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None
    mandato: Optional[List[MandatoSchema]] = None


@router.post("/", response_model=UserOut)
def create_user(
    data: UserCreate,
    session: Session = Depends(get_session),
    current_user: UserORM = Depends(get_current_user),
):
    _require_admin(current_user)
    exists = session.scalar(select(UserORM).where(UserORM.email == data.email))
    if exists:
        raise HTTPException(status_code=400, detail="User already exists")
    raw_password = data.password or secrets.token_urlsafe(16)
    obj = UserORM(
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        permission_level=data.permission_level.value,
        lgpd_check=data.lgpd_check,
        role=data.role,
        hashed_password=get_password_hash(raw_password),
    )
    session.add(obj)
    session.flush()

    mandato_payloads: List[MandatoSchema] = list(data.mandato or [])
    if not mandato_payloads:
        default_nome = f"{data.first_name} {data.last_name}".strip() or None
        mandato_payloads = [MandatoSchema.model_construct(nome_parlamentar=default_nome)]

    for mandato_schema in mandato_payloads:
        if not isinstance(mandato_schema, MandatoSchema):
            mandato_schema = MandatoSchema.model_validate(mandato_schema)
        if mandato_schema.id:
            mandato_obj = session.get(MandatoORM, mandato_schema.id)
            if not mandato_obj:
                raise HTTPException(status_code=404, detail=f"Mandato {mandato_schema.id} not found")
            mandato_obj.users.append(obj)
        else:
            mandato_data = mandato_schema.model_dump(exclude={"id", "users"}, exclude_unset=True)
            mandato_obj = MandatoORM(**mandato_data)
            mandato_obj.users.append(obj)
            session.add(mandato_obj)

    session.commit()
    session.refresh(obj)
    return build_user_out(obj)


@router.get("/", response_model=dict)
def list_users(
    session: Session = Depends(get_session),
    current_user: UserORM = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of users to return"),
    offset: int = Query(0, ge=0, description="Number of users to skip"),
    search: Optional[str] = Query(None, description="Search by email, first_name or last_name"),
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
    role: Optional[str] = Query(
        None,
        description="Filter by role (comma-separated for multiple values, e.g. 'staff,assessor')",
    ),
    permission_level: Optional[str] = Query(
        None,
        description="Filter by permission level (comma-separated for multiple values, e.g. 'Admin,User')",
    ),
    order_by: Optional[str] = Query(
        None,
        alias="orderBy",
        description="Order by: first_name, last_name, created_at, last_login. Prefix with '-' for DESC.",
    ),
):
    _require_admin(current_user)

    allowed_order_fields = {"first_name", "last_name", "created_at", "last_login"}
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

    def _nulls_last_sort(col, *, desc: bool) -> Tuple:
        # Keep NULLs at the end in both ASC and DESC
        if desc:
            return (col.is_(None)).asc(), col.desc()
        return (col.is_(None)).asc(), col.asc()

    def _to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
        if dt is None:
            return None
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    stmt = select(UserORM)

    # Filters
    perm_clause = ci_in(UserORM.permission_level, permission_level)
    if perm_clause is not None:
        stmt = stmt.where(perm_clause)
    role_clause = ci_in(UserORM.role, role)
    if role_clause is not None:
        stmt = stmt.where(role_clause)
    if search:
        stmt = stmt.where(
            or_(
                _ci_like(UserORM.email, search),
                _ci_like(UserORM.first_name, search),
                _ci_like(UserORM.last_name, search),
            )
        )

    last_login_from = _to_naive_utc(from_dt)
    if last_login_from is not None:
        stmt = stmt.where(UserORM.last_login_at >= last_login_from)
    last_login_to = _to_naive_utc(to_dt)
    if last_login_to is not None:
        stmt = stmt.where(UserORM.last_login_at <= last_login_to)

    # Total count with same filters (without join)
    count_stmt = select(func.count()).select_from(UserORM)
    perm_clause = ci_in(UserORM.permission_level, permission_level)
    if perm_clause is not None:
        count_stmt = count_stmt.where(perm_clause)
    role_clause = ci_in(UserORM.role, role)
    if role_clause is not None:
        count_stmt = count_stmt.where(role_clause)
    if search:
        count_stmt = count_stmt.where(
            or_(
                _ci_like(UserORM.email, search),
                _ci_like(UserORM.first_name, search),
                _ci_like(UserORM.last_name, search),
            )
        )
    if last_login_from is not None:
        count_stmt = count_stmt.where(UserORM.last_login_at >= last_login_from)
    if last_login_to is not None:
        count_stmt = count_stmt.where(UserORM.last_login_at <= last_login_to)
    total_count = session.scalar(count_stmt) or 0

    # Ordering
    if order_field == "first_name":
        first = func.lower(func.coalesce(UserORM.first_name, ""))
        last = func.lower(func.coalesce(UserORM.last_name, ""))
        order_exprs = [first.desc() if desc else first.asc(), last.asc(), UserORM.id.asc()]
    elif order_field == "last_name":
        last = func.lower(func.coalesce(UserORM.last_name, ""))
        first = func.lower(func.coalesce(UserORM.first_name, ""))
        order_exprs = [last.desc() if desc else last.asc(), first.asc(), UserORM.id.asc()]
    elif order_field == "created_at":
        order_exprs = [UserORM.created_at.desc() if desc else UserORM.created_at.asc(), UserORM.id.asc()]
    elif order_field == "last_login":
        order_exprs = [*_nulls_last_sort(UserORM.last_login_at, desc=desc), UserORM.id.asc()]
    else:
        order_exprs = [UserORM.id.asc()]

    stmt = stmt.order_by(*order_exprs).limit(limit).offset(offset)

    results = session.scalars(stmt).all()
    users_out: List[UserOut] = []
    for user in results:
        payload = serialize_user_core(user)
        payload["last_login"] = getattr(user, "last_login_at", None)
        users_out.append(UserOut(**payload))

    return {"users": users_out, "total": total_count, "limit": limit, "offset": offset}


@router.get("/me", response_model=UserMeOut)
def get_user_me(current_user: UserORM = Depends(get_current_user)):
    return build_user_me_out(current_user)


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: UserORM = Depends(get_current_user),
):
    obj = session.get(UserORM, user_id)
    if not obj:
        raise HTTPException(status_code=404, detail="User not found")
    current_user_id = int(getattr(current_user, "id", 0) or 0)
    if not (_is_admin(current_user) or current_user_id == user_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    return build_user_out(obj)


@router.put("/me", response_model=UserOut)
def update_user_me(
    data: UserUpdate,
    session: Session = Depends(get_session),
    current_user: UserORM = Depends(get_current_user),
):
    obj = current_user
    payload = data.model_dump(exclude_unset=True)
    payload.pop("permission_level", None)
    payload.pop("is_active", None)
    if "password" in payload and payload["password"] is not None:
        setattr(obj, "hashed_password", get_password_hash(payload.pop("password")))
    for k, v in payload.items():
        if v is not None:
            setattr(obj, k, v)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return build_user_out(obj)


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    session: Session = Depends(get_session),
    current_user: UserORM = Depends(get_current_user),
):
    obj = session.get(UserORM, user_id)
    if not obj:
        raise HTTPException(status_code=404, detail="User not found")
    payload = data.model_dump(exclude_unset=True)
    is_admin = _is_admin(current_user)
    current_user_id = int(getattr(current_user, "id", 0) or 0)
    if not is_admin and current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if not is_admin and "permission_level" in payload:
        raise HTTPException(status_code=403, detail="Not authorized to change permission level")
    
    # Validate email uniqueness if email is being changed
    if "email" in payload and payload["email"] is not None:
        if not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to change email")
        if payload["email"] != obj.email:
            existing = session.scalar(select(UserORM).where(UserORM.email == payload["email"]))
            if existing:
                raise HTTPException(status_code=400, detail="Email already in use")
    
    mandato_payloads = payload.pop("mandato", None)
    if "password" in payload and payload["password"] is not None:
        setattr(obj, "hashed_password", get_password_hash(payload.pop("password")))
    for k, v in payload.items():
        if v is not None:
            setattr(obj, k, v if k != "permission_level" else v.value)

    if mandato_payloads is not None:
        if not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to change mandates")
        new_mandatos: List[MandatoORM] = []
        for mandato_schema in mandato_payloads or []:
            if not isinstance(mandato_schema, MandatoSchema):
                mandato_schema = MandatoSchema.model_validate(mandato_schema)
            if mandato_schema.id:
                mandato_obj = session.get(MandatoORM, mandato_schema.id)
                if not mandato_obj:
                    raise HTTPException(status_code=404, detail=f"Mandato {mandato_schema.id} not found")
            else:
                mandato_data = mandato_schema.model_dump(exclude={"id", "users"}, exclude_unset=True)
                mandato_obj = MandatoORM(**mandato_data)
                session.add(mandato_obj)
                session.flush()
            new_mandatos.append(mandato_obj)
        obj.mandatos = new_mandatos

    session.add(obj)
    session.commit()
    session.refresh(obj)
    return build_user_out(obj)


@router.delete("/{user_id}", response_model=dict)
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: UserORM = Depends(get_current_user),
):
    _require_admin(current_user)
    obj = session.get(UserORM, user_id)
    if not obj:
        raise HTTPException(status_code=404, detail="User not found")

    # Clear derived last_login pointers before deletion to avoid FK issues.
    session.query(MandatoORM).filter(MandatoORM.last_login_user_id == user_id).update(
        {"last_login_user_id": None, "last_login_at": None},
        synchronize_session=False,
    )
    session.delete(obj)
    session.commit()
    return {"detail": "User deleted"}
