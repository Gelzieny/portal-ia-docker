from collections.abc import Iterable
from typing import Any

from fastapi import HTTPException, Request, status

from app.core import database
from app.services.audit_service import log_audit

ROLES = ["admin", "gestor", "curador", "curador_modelos", "gestor_produto", "servidor"]
ADMIN_REQUIRED_PERMISSIONS = {
    "admin.users.manage",
    "admin.permissions.manage",
    "admin.audit.view",
}
GLOBAL_REQUIRED_PERMISSIONS = {"app.home.view"}
DEFAULT_ROLE_PERMISSIONS = {
    "admin": {
        "app.home.view",
        "models.catalog.view",
        "models.my_access.view",
        "prompts.library.view",
        "prompts.my.view",
        "mcp.catalog.view",
        "docs.portal.view",
        "news.portal.view",
        "admin.dashboard.view",
        "admin.users.manage",
        "admin.models.manage",
        "admin.model_access.manage",
        "admin.prompts.manage",
        "admin.prompt_curation.manage",
        "admin.mcp.manage",
        "admin.docs.manage",
        "admin.news.manage",
        "admin.notifications.manage",
        "admin.audit.view",
        "admin.permissions.manage",
        "ideas.portal.view",
        "ideas.create",
        "ideas.vote",
        "ideas.comment",
        "ideas.comment.react",
        "ideas.own.manage",
        "ideas.curation.manage",
        "ideas.roadmap.manage",
        "roadmap.view",
        "admin.idea_versions.manage",
    },
    "gestor": {
        "app.home.view",
        "models.catalog.view",
        "models.my_access.view",
        "prompts.library.view",
        "prompts.my.view",
        "mcp.catalog.view",
        "docs.portal.view",
        "news.portal.view",
        "admin.dashboard.view",
        "admin.models.manage",
        "admin.prompts.manage",
        "admin.prompt_curation.manage",
        "admin.mcp.manage",
        "admin.docs.manage",
        "admin.news.manage",
        "ideas.portal.view",
        "ideas.create",
        "ideas.vote",
        "ideas.comment",
        "ideas.comment.react",
        "ideas.own.manage",
        "roadmap.view",
    },
    "curador": {
        "app.home.view",
        "models.catalog.view",
        "models.my_access.view",
        "prompts.library.view",
        "prompts.my.view",
        "mcp.catalog.view",
        "docs.portal.view",
        "news.portal.view",
        "admin.prompt_curation.manage",
        "ideas.portal.view",
        "ideas.create",
        "ideas.vote",
        "ideas.comment",
        "ideas.comment.react",
        "ideas.own.manage",
        "roadmap.view",
    },
    "curador_modelos": {
        "app.home.view",
        "models.catalog.view",
        "models.my_access.view",
        "prompts.library.view",
        "prompts.my.view",
        "mcp.catalog.view",
        "docs.portal.view",
        "news.portal.view",
        "admin.model_access.manage",
        "ideas.portal.view",
        "ideas.create",
        "ideas.vote",
        "ideas.comment",
        "ideas.comment.react",
        "ideas.own.manage",
        "roadmap.view",
    },
    "gestor_produto": {
        "app.home.view",
        "models.catalog.view",
        "models.my_access.view",
        "prompts.library.view",
        "prompts.my.view",
        "mcp.catalog.view",
        "docs.portal.view",
        "news.portal.view",
        "ideas.portal.view",
        "ideas.create",
        "ideas.vote",
        "ideas.comment",
        "ideas.comment.react",
        "ideas.own.manage",
        "ideas.curation.manage",
        "ideas.roadmap.manage",
        "roadmap.view",
        "admin.idea_versions.manage",
    },
    "servidor": {
        "app.home.view",
        "models.catalog.view",
        "models.my_access.view",
        "prompts.library.view",
        "prompts.my.view",
        "mcp.catalog.view",
        "docs.portal.view",
        "news.portal.view",
        "ideas.portal.view",
        "ideas.create",
        "ideas.vote",
        "ideas.comment",
        "ideas.comment.react",
        "ideas.own.manage",
        "roadmap.view",
    },
}


def _required_permissions_for_role(role: str) -> set[str]:
    required = set(GLOBAL_REQUIRED_PERMISSIONS)
    if role == "admin":
        required.update(ADMIN_REQUIRED_PERMISSIONS)
    return required


def _ensure_role(role: str) -> None:
    if role not in ROLES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Papel não encontrado")


def _row_to_feature(row) -> dict[str, Any]:
    return {
        "key": row["key"],
        "name": row["name"],
        "description": row["description"],
        "area": row["area"],
        "menu_label": row["menu_label"],
        "menu_path": row["menu_path"],
        "sort_order": row["sort_order"],
        "is_active": row["is_active"],
        "is_system": row["is_system"],
    }


async def list_enabled_permissions_for_role(role: str) -> list[str]:
    _ensure_role(role)
    required = sorted(_required_permissions_for_role(role))
    defaults = sorted(DEFAULT_ROLE_PERMISSIONS[role])
    rows = await database.fetch(
        """
        SELECT f.key
        FROM app_features f
        LEFT JOIN role_feature_permissions rfp
          ON rfp.feature_key = f.key
         AND rfp.role = $1::user_role
        WHERE (
            rfp.is_enabled = TRUE
            OR f.key = ANY($2::text[])
            OR (rfp.feature_key IS NULL AND f.key = ANY($3::text[]))
          )
          AND f.is_active = TRUE
        ORDER BY f.sort_order, f.name
        """,
        role,
        required,
        defaults,
    )
    return [row["key"] for row in rows]


async def user_has_permission(role: str, permission_key: str) -> bool:
    _ensure_role(role)
    if permission_key in _required_permissions_for_role(role):
        return True
    row = await database.fetchrow(
        """
        SELECT f.is_active, rfp.is_enabled
        FROM app_features f
        LEFT JOIN role_feature_permissions rfp
          ON rfp.feature_key = f.key
         AND rfp.role = $1::user_role
        WHERE f.key = $2
        """,
        role,
        permission_key,
    )
    if row is None:
        return permission_key in DEFAULT_ROLE_PERMISSIONS[role]
    if not row["is_active"]:
        return False
    if row["is_enabled"] is not None:
        return bool(row["is_enabled"])
    return permission_key in DEFAULT_ROLE_PERMISSIONS[role]


async def get_permissions_for_role(role: str) -> dict[str, Any]:
    _ensure_role(role)
    required = sorted(_required_permissions_for_role(role))
    defaults = sorted(DEFAULT_ROLE_PERMISSIONS[role])
    rows = await database.fetch(
        """
        SELECT f.*
        FROM app_features f
        LEFT JOIN role_feature_permissions rfp
          ON rfp.feature_key = f.key
         AND rfp.role = $1::user_role
        WHERE (
            rfp.is_enabled = TRUE
            OR f.key = ANY($2::text[])
            OR (rfp.feature_key IS NULL AND f.key = ANY($3::text[]))
          )
          AND f.is_active = TRUE
        ORDER BY f.sort_order, f.name
        """,
        role,
        required,
        defaults,
    )
    features = [_row_to_feature(row) for row in rows]
    return {
        "role": role,
        "permissions": [feature["key"] for feature in features],
        "features": features,
    }


async def list_features() -> list[dict[str, Any]]:
    rows = await database.fetch(
        """
        SELECT *
        FROM app_features
        WHERE is_active = TRUE
        ORDER BY sort_order, area, name
        """
    )
    return [_row_to_feature(row) for row in rows]


async def get_permissions_matrix() -> dict[str, Any]:
    rows = await database.fetch(
        """
        SELECT
          f.key, f.name, f.description, f.area, f.menu_label, f.menu_path, f.sort_order,
          role_value::text AS role, COALESCE(rfp.is_enabled, FALSE) AS is_enabled,
          rfp.updated_at
        FROM app_features f
        CROSS JOIN unnest(enum_range(NULL::user_role)) AS role_value
        LEFT JOIN role_feature_permissions rfp
          ON rfp.feature_key = f.key
         AND rfp.role = role_value
        WHERE f.is_active = TRUE
        ORDER BY f.sort_order, f.name, role_value::text
        """
    )

    by_key: dict[str, dict[str, Any]] = {}
    roles = [role for role in ROLES]
    for row in rows:
        feature = by_key.setdefault(
            row["key"],
            {
                "key": row["key"],
                "name": row["name"],
                "description": row["description"],
                "area": row["area"],
                "menu_label": row["menu_label"],
                "menu_path": row["menu_path"],
                "sort_order": row["sort_order"],
                "is_required": row["key"] in GLOBAL_REQUIRED_PERMISSIONS,
                "grants": {role: False for role in roles},
                "updated_at_by_role": {role: None for role in roles},
            },
        )
        role = row["role"]
        if role in roles:
            feature["grants"][role] = row["is_enabled"]
            feature["updated_at_by_role"][role] = row["updated_at"]
            if row["key"] in _required_permissions_for_role(role):
                feature["grants"][role] = True
                feature["is_required"] = True

    return {"roles": roles, "features": list(by_key.values())}


async def _ensure_features_exist(permission_keys: Iterable[str]) -> None:
    keys = sorted(set(permission_keys))
    if not keys:
        return
    rows = await database.fetch("SELECT key FROM app_features WHERE key = ANY($1::text[])", keys)
    existing = {row["key"] for row in rows}
    missing = sorted(set(keys) - existing)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permissões desconhecidas: {', '.join(missing)}",
        )


def _normalize_permissions(role: str, permission_keys: Iterable[str]) -> set[str]:
    normalized = set(permission_keys)
    normalized.update(_required_permissions_for_role(role))
    return normalized


async def update_role_permissions(
    *,
    role: str,
    permission_keys: list[str],
    actor: dict,
    request: Request | None = None,
    audit_action: str = "ROLE_PERMISSION_UPDATE",
) -> dict[str, Any]:
    _ensure_role(role)
    normalized = _normalize_permissions(role, permission_keys)
    await _ensure_features_exist(normalized)
    before = set(await list_enabled_permissions_for_role(role))

    async with database.get_connection() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO role_feature_permissions (role, feature_key, is_enabled)
                SELECT $1::user_role, key, FALSE
                FROM app_features
                ON CONFLICT (role, feature_key) DO NOTHING
                """,
                role,
            )
            await conn.execute(
                """
                UPDATE role_feature_permissions
                SET is_enabled = feature_key = ANY($2::text[]),
                    updated_at = NOW()
                WHERE role = $1::user_role
                """,
                role,
                sorted(normalized),
            )

    after = set(await list_enabled_permissions_for_role(role))
    added = sorted(after - before)
    removed = sorted(before - after)
    await log_audit(
        user_id=actor.get("id"),
        action=audit_action,
        entity="role_feature_permissions",
        entity_id=None,
        metadata={"role": role, "added": added, "removed": removed},
        request=request,
    )
    return await get_permissions_matrix()


async def reset_role_defaults(
    *,
    role: str,
    actor: dict,
    request: Request | None = None,
) -> dict[str, Any]:
    _ensure_role(role)
    defaults = sorted(DEFAULT_ROLE_PERMISSIONS[role])
    return await update_role_permissions(
        role=role,
        permission_keys=defaults,
        actor=actor,
        request=request,
        audit_action="ROLE_PERMISSION_RESET_DEFAULTS",
    )
