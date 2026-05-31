import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

from fastapi import Depends, HTTPException, Request, status
from starlette.datastructures import Headers

from app.core import database
from app.services.auth_service import AuthService


def _claim(claims: dict, *keys: str) -> str | None:
    for key in keys:
        value = claims.get(key)
        if value is None:
            continue
        normalized = str(value).strip()
        if normalized:
            return normalized
    return None


def _header(headers: Headers, key: str) -> str | None:
    value = headers.get(key)
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _role_from_portal_roles(headers: Headers) -> str | None:
    roles_header = _header(headers, "x-goia-user-roles")
    if not roles_header:
        return None

    roles = [role.strip().lower() for role in roles_header.split(",") if role.strip()]
    normalized = " ".join(roles)

    if "admin" in normalized or "administrador" in normalized:
        return "admin"
    if "gestor_produto" in normalized or "gestor produto" in normalized:
        return "gestor_produto"
    if "curador_modelos" in normalized or "curador modelos" in normalized:
        return "curador_modelos"
    if "curador" in normalized:
        return "curador"
    if "gestor" in normalized:
        return "gestor"
    if "servidor" in normalized:
        return "servidor"

    return None


def _user_payload_from_claims(claims: dict, headers: Headers) -> dict:
    codg_usuario = _claim(claims, "sub")
    name = _header(headers, "x-goia-user-name") or _claim(
        claims,
        "name",
        "given_name",
        "preferred_username",
    ) or codg_usuario
    email = _header(headers, "x-goia-user-email") or _claim(
        claims,
        "email_corporativo",
        "email",
        "email_pessoal",
    )
    has_email_claim = email is not None
    organ = _header(headers, "x-goia-user-organ") or _claim(
        claims,
        "org_name",
        "organ",
        "orgao",
        "organization",
        "lotacao",
    ) or "Estado de Goiás"

    if not codg_usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "codg_usuario": codg_usuario,
        "name": name or codg_usuario,
        "email": email,
        "email_from_claim": has_email_claim,
        "organ": organ,
        "role": _role_from_portal_roles(headers) or "servidor",
    }


async def get_current_user(
    request: Request,
    auth: dict = Depends(AuthService.verify_login),
) -> dict:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not auth:
        logging.warning("Autenticação falhou: Nenhum token fornecido ou token inválido.")
        raise credentials_exc

    payload = _user_payload_from_claims(auth, request.headers)
    logging.info(f"Payload do usuário extraído: {payload}")

    row = await database.fetchrow(
        "SELECT id, name, email, role, organ, avatar_url, is_active, created_at "
        "FROM users WHERE codg_usuario = $1",
        payload["codg_usuario"],
    )

    if row is None:
        logging.info(f"Usuário com codg_usuario {payload['codg_usuario']} não encontrado. Tentando buscar por email.")
        if payload["email"]:
            row = await database.fetchrow(
                "SELECT id, name, email, role, organ, avatar_url, is_active, created_at "
                "FROM users WHERE email = $1",
                payload["email"],
            )

    if row is None:
        logging.info(f"Usuário não encontrado. Criando novo usuário com payload: {payload}")
        row = await database.fetchrow(
            "INSERT INTO users (name, email, codg_usuario, role, organ) "
            "VALUES ($1, $2, $3, $4::user_role, $5) "
            "RETURNING id, name, email, role, organ, avatar_url, is_active, created_at",
            payload["name"],
            payload["email"],
            payload["codg_usuario"],
            payload["role"],
            payload["organ"],
        )
    else:
        logging.info(f"Usuário encontrado: {row}")

    if row is None or not row["is_active"]:
        logging.warning(f"Usuário inativo ou não encontrado: {payload}")
        raise credentials_exc

    logging.info(f"Usuário autenticado com sucesso: {row}")
    request.state.user_id = str(row["id"])
    return dict(row)


def require_roles(*roles: str):
    async def _check(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente",
            )
        return current_user

    return _check


def require_permission(permission_key: str):
    async def _check(current_user: dict = Depends(get_current_user)) -> dict:
        from app.services.permission_service import user_has_permission

        if not await user_has_permission(current_user["role"], permission_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente",
            )
        return current_user

    return _check


def require_any_permission(*permission_keys: str):
    async def _check(current_user: dict = Depends(get_current_user)) -> dict:
        from app.services.permission_service import user_has_permission

        for permission_key in permission_keys:
            if await user_has_permission(current_user["role"], permission_key):
                return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão insuficiente",
        )

    return _check


def require_curation_access():
    """Admin, gestor ou curador — acesso à fila de curadoria."""
    return require_roles("admin", "gestor", "curador")


def require_model_access_curation():
    """Admin ou curador_modelos — curadoria de acesso a modelos."""
    return require_roles("admin", "curador_modelos")
