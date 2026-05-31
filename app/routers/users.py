from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core import database
from app.core.deps import get_current_user, require_permission
from app.models.pagination import PaginatedResponse
from app.models.user import UserCreate, UserResponse, UserUpdate, UserUpdateAdmin
from app.services.audit_service import log_audit

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)


@router.put("/me", response_model=UserResponse)
async def update_me(body: UserUpdate, current_user: dict = Depends(get_current_user)):
    fields, values = [], []
    for field, value in body.model_dump(exclude_none=True).items():
        fields.append(f"{field} = ${len(values) + 2}")
        values.append(value)

    if not fields:
        return UserResponse(**current_user)

    values.insert(0, current_user["id"])
    row = await database.fetchrow(
        f"UPDATE users SET {', '.join(fields)} WHERE id = $1 "
        "RETURNING id, name, email, role, organ, avatar_url, is_active, created_at",
        *values,
    )
    return UserResponse(**dict(row))





# ── Admin endpoints ──────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str | None = None,
    search: str | None = None,
    codg_usuario: str | None = Query(default=None, max_length=120),
    is_active: bool | None = None,
    _: dict = Depends(require_permission("admin.users.manage")),
):
    conditions = ["TRUE"]
    params: list = []

    if role:
        params.append(role)
        conditions.append(f"role = ${len(params)}")
    if is_active is not None:
        params.append(is_active)
        conditions.append(f"is_active = ${len(params)}")
    if codg_usuario:
        params.append(codg_usuario)
        conditions.append(f"codg_usuario = ${len(params)}")
    if search:
        params.append(f"%{search}%")
        conditions.append(f"(name ILIKE ${len(params)} OR email ILIKE ${len(params)} OR codg_usuario ILIKE ${len(params)})")

    where = " AND ".join(conditions)
    total = await database.fetchval(f"SELECT COUNT(*) FROM users WHERE {where}", *params)

    params += [(page - 1) * page_size, page_size]
    rows = await database.fetch(
        f"SELECT id, name, email, codg_usuario, role, organ, avatar_url, is_active, created_at "
        f"FROM users WHERE {where} ORDER BY created_at DESC "
        f"OFFSET ${len(params) - 1} LIMIT ${len(params)}",
        *params,
    )
    items = [UserResponse(**dict(r)) for r in rows]
    return PaginatedResponse.build(items, total, page, page_size)


@router.get("/codg-usuario/{codg_usuario}", response_model=UserResponse)
async def get_user_by_codg_usuario(
    codg_usuario: str,
    _: dict = Depends(get_current_user),
):
    row = await database.fetchrow(
        "SELECT id, name, email, codg_usuario, role, organ, avatar_url, is_active, created_at "
        "FROM users WHERE codg_usuario = $1",
        codg_usuario,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return UserResponse(**dict(row))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID, _: dict = Depends(require_permission("admin.users.manage"))):
    row = await database.fetchrow(
        "SELECT id, name, email, codg_usuario, role, organ, avatar_url, is_active, created_at "
        "FROM users WHERE id = $1",
        user_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return UserResponse(**dict(row))


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    request: Request,
    current_user: dict = Depends(require_permission("admin.users.manage")),
):
    if body.email:
        existing = await database.fetchval("SELECT id FROM users WHERE email = $1", body.email)
        if existing:
            raise HTTPException(status_code=409, detail="E-mail já cadastrado")

    if body.codg_usuario:
        existing_codg = await database.fetchval("SELECT id FROM users WHERE codg_usuario = $1", body.codg_usuario)
        if existing_codg:
            raise HTTPException(status_code=409, detail="Código de usuário já cadastrado")

    row = await database.fetchrow(
        "INSERT INTO users (name, email, codg_usuario, role, organ) "
        "VALUES ($1, $2, $3, $4, $5) "
        "RETURNING id, name, email, codg_usuario, role, organ, avatar_url, is_active, created_at",
        body.name,
        body.email,
        body.codg_usuario,
        body.role,
        body.organ,
    )
    await log_audit(
        user_id=current_user["id"],
        action="USER_CREATE",
        entity="user",
        entity_id=row["id"],
        metadata={"role": row["role"], "email": row["email"]},
        request=request,
    )
    return UserResponse(**dict(row))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    body: UserUpdateAdmin,
    request: Request,
    current_user: dict = Depends(require_permission("admin.users.manage")),
):
    fields, values = [], [user_id]
    for field, value in body.model_dump(exclude_none=True).items():
        fields.append(f"{field} = ${len(values) + 1}")
        values.append(value)

    if not fields:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    row = await database.fetchrow(
        f"UPDATE users SET {', '.join(fields)} WHERE id = $1 "
        "RETURNING id, name, email, codg_usuario, role, organ, avatar_url, is_active, created_at",
        *values,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    await log_audit(
        user_id=current_user["id"],
        action="USER_UPDATE",
        entity="user",
        entity_id=user_id,
        metadata={"fields": list(body.model_dump(exclude_none=True).keys())},
        request=request,
    )
    return UserResponse(**dict(row))





@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    request: Request,
    current_user: dict = Depends(require_permission("admin.users.manage")),
):
    result = await database.execute(
        "UPDATE users SET is_active = FALSE WHERE id = $1", user_id
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    await log_audit(
        user_id=current_user["id"],
        action="USER_DEACTIVATE",
        entity="user",
        entity_id=user_id,
        request=request,
    )
    return {"message": "Usuário desativado"}
