import json
import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ConfigDict

from app.core import database
from app.core.deps import get_current_user, require_any_permission, require_permission
from app.models.mcp import (
    MCPAgentCreate,
    MCPAgentResponse,
    MCPAgentUpdate,
    MCPCategoryCreate,
    MCPCategoryResponse,
    MCPCategoryUpdate,
    MCPClientType,
    MCPConfigSnippetCreate,
    MCPConfigSnippetResponse,
    MCPConfigSnippetUpdate,
    MCPInstallCreate,
    MCPResourceCreate,
    MCPResourceResponse,
    MCPResourceUpdate,
    MCPReviewCreate,
    MCPReviewResponse,
    MCPServerCreate,
    MCPServerDetailResponse,
    MCPServerListResponse,
    MCPServerStatus,
    MCPServerUpdate,
    MCPToolCreate,
    MCPToolParam,
    MCPToolResponse,
    MCPToolUpdate,
)
from app.models.pagination import PaginatedResponse

router = APIRouter(prefix="/mcp", tags=["MCP Catalog"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    s = text.lower()
    for src, dst in [
        ("àáâãä", "a"), ("èéêë", "e"), ("ìíîï", "i"),
        ("òóôõö", "o"), ("ùúûü", "u"), ("ç", "c"),
    ]:
        if isinstance(src, str) and len(src) > 1:
            for ch in src:
                s = s.replace(ch, dst)
        else:
            s = s.replace(src, dst)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _build_category_dict(d: dict) -> dict:
    """Extract aliased cat_* columns into nested category dict."""
    if d.get("cat_id"):
        d["category"] = {
            "id": d.pop("cat_id"),
            "name": d.pop("cat_name"),
            "slug": d.pop("cat_slug"),
            "description": d.pop("cat_description", ""),
            "icon": d.pop("cat_icon"),
            "color": d.pop("cat_color"),
            "server_count": 0,
        }
    else:
        for k in ("cat_id", "cat_name", "cat_slug", "cat_description", "cat_icon", "cat_color"):
            d.pop(k, None)
        d["category"] = None
    return d


def _row_to_server_list(row) -> MCPServerListResponse:
    d = _build_category_dict(dict(row))
    return MCPServerListResponse.model_validate(d)


def _row_to_server_detail(d: dict) -> MCPServerDetailResponse:
    _build_category_dict(d)
    return MCPServerDetailResponse.model_validate(d)


def _row_to_tool(row) -> MCPToolResponse:
    d = dict(row)
    params = d.get("parameters", [])
    if isinstance(params, str):
        params = json.loads(params)
    d["parameters"] = [MCPToolParam.model_validate(p) for p in (params or [])]
    return MCPToolResponse.model_validate(d)


def _row_to_agent(row) -> MCPAgentResponse:
    return MCPAgentResponse.model_validate(dict(row))


def _row_to_resource(row) -> MCPResourceResponse:
    return MCPResourceResponse.model_validate(dict(row))


def _row_to_snippet(row) -> MCPConfigSnippetResponse:
    return MCPConfigSnippetResponse.model_validate(dict(row))


# Base SELECT for server list (uses $1 = user_id for is_favorite / is_installed)
_SERVER_LIST_SELECT = """
    SELECT
        s.id, s.name, s.slug, s.tagline, s.status, s.is_verified, s.is_featured,
        s.is_official, s.tags, s.rating_avg, s.rating_count, s.install_count,
        s.compatible_models, s.sort_order, s.is_active,
        mc.id          AS cat_id,
        mc.name        AS cat_name,
        mc.slug        AS cat_slug,
        mc.description AS cat_description,
        mc.icon        AS cat_icon,
        mc.color       AS cat_color,
        (SELECT COUNT(*) FROM mcp_tools  WHERE server_id = s.id)::int AS tool_count,
        (SELECT COUNT(*) FROM mcp_agents WHERE server_id = s.id)::int AS agent_count,
        (EXISTS (SELECT 1 FROM mcp_favorites     WHERE user_id = $1 AND server_id = s.id)) AS is_favorite,
        (EXISTS (SELECT 1 FROM mcp_installations WHERE user_id = $1 AND server_id = s.id)) AS is_installed
    FROM mcp_servers s
    LEFT JOIN mcp_categories mc ON s.category_id = mc.id
    WHERE s.is_active = TRUE
"""

# Base SELECT for detail (includes all server columns)
_SERVER_DETAIL_SELECT = """
    SELECT
        s.*,
        mc.id          AS cat_id,
        mc.name        AS cat_name,
        mc.slug        AS cat_slug,
        mc.description AS cat_description,
        mc.icon        AS cat_icon,
        mc.color       AS cat_color,
        (SELECT COUNT(*) FROM mcp_tools  WHERE server_id = s.id)::int AS tool_count,
        (SELECT COUNT(*) FROM mcp_agents WHERE server_id = s.id)::int AS agent_count,
        (EXISTS (SELECT 1 FROM mcp_favorites     WHERE user_id = $1 AND server_id = s.id)) AS is_favorite,
        (EXISTS (SELECT 1 FROM mcp_installations WHERE user_id = $1 AND server_id = s.id)) AS is_installed
    FROM mcp_servers s
    LEFT JOIN mcp_categories mc ON s.category_id = mc.id
    WHERE s.is_active = TRUE
"""


async def _fetch_server_detail(server_id: UUID, user_id: str) -> MCPServerDetailResponse:
    row = await database.fetchrow(
        _SERVER_DETAIL_SELECT + " AND s.id = $2",
        user_id, server_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Servidor MCP não encontrado")

    tools = await database.fetch(
        "SELECT * FROM mcp_tools WHERE server_id = $1 ORDER BY sort_order", server_id
    )
    agents = await database.fetch(
        "SELECT * FROM mcp_agents WHERE server_id = $1 ORDER BY sort_order", server_id
    )
    resources = await database.fetch(
        "SELECT * FROM mcp_resources WHERE server_id = $1 ORDER BY sort_order", server_id
    )
    snippets = await database.fetch(
        "SELECT * FROM mcp_config_snippets WHERE server_id = $1 ORDER BY sort_order", server_id
    )

    d = dict(row)
    d["tools"] = [_row_to_tool(t) for t in tools]
    d["agents"] = [_row_to_agent(a) for a in agents]
    d["resources"] = [_row_to_resource(r) for r in resources]
    d["config_snippets"] = [_row_to_snippet(s) for s in snippets]
    return _row_to_server_detail(d)


# ── Categories (público) ──────────────────────────────────────────────────────

@router.get("/categories", response_model=list[MCPCategoryResponse])
async def list_categories(_: dict = Depends(require_any_permission("mcp.catalog.view", "admin.mcp.manage"))):
    rows = await database.fetch(
        """
        SELECT c.*,
               (SELECT COUNT(*) FROM mcp_servers s
                WHERE s.category_id = c.id AND s.is_active = TRUE)::int AS server_count
        FROM mcp_categories c
        WHERE c.is_active = TRUE
        ORDER BY c.sort_order
        """
    )
    return [MCPCategoryResponse.model_validate(dict(r)) for r in rows]


# ── Server list ───────────────────────────────────────────────────────────────

@router.get("/servers", response_model=PaginatedResponse[MCPServerListResponse])
async def list_servers(
    category_slug: str | None = None,
    status: MCPServerStatus | None = None,
    search: str | None = None,
    is_verified: bool | None = None,
    is_featured: bool | None = None,
    is_official: bool | None = None,
    compatible_model: str | None = None,
    favorites_only: bool = False,
    installed_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_permission("mcp.catalog.view")),
):
    params: list = [current_user["id"]]
    conditions: list[str] = []

    if category_slug:
        params.append(category_slug)
        conditions.append(f"mc.slug = ${len(params)}")
    if status:
        params.append(status.value)
        conditions.append(f"s.status = ${len(params)}::mcp_server_status")
    if search:
        params.append(search)
        n = len(params)
        conditions.append(
            f"(s.name ILIKE '%' || ${n} || '%' OR s.tagline ILIKE '%' || ${n} || '%'"
            f" OR s.description ILIKE '%' || ${n} || '%'"
            f" OR EXISTS (SELECT 1 FROM unnest(s.tags) _t WHERE _t ILIKE '%' || ${n} || '%'))"
        )
    if is_verified is not None:
        params.append(is_verified)
        conditions.append(f"s.is_verified = ${len(params)}")
    if is_featured is not None:
        params.append(is_featured)
        conditions.append(f"s.is_featured = ${len(params)}")
    if is_official is not None:
        params.append(is_official)
        conditions.append(f"s.is_official = ${len(params)}")
    if compatible_model:
        params.append(compatible_model)
        n = len(params)
        conditions.append(
            f"EXISTS (SELECT 1 FROM unnest(s.compatible_models) _m WHERE _m ILIKE '%' || ${n} || '%')"
        )
    if favorites_only:
        conditions.append("EXISTS (SELECT 1 FROM mcp_favorites WHERE user_id = $1 AND server_id = s.id)")
    if installed_only:
        conditions.append("EXISTS (SELECT 1 FROM mcp_installations WHERE user_id = $1 AND server_id = s.id)")

    where_extra = (" AND " + " AND ".join(conditions)) if conditions else ""

    # COUNT query does not need user_id ($1) unless favorites/installed filters are active.
    # asyncpg raises if bound params don't match $N placeholders, so build separate params.
    if favorites_only or installed_only:
        count_params = list(params)
        count_where = where_extra
    else:
        # Shift $2 → $1, $3 → $2, … and drop user_id from params
        count_where = re.sub(r"\$(\d+)", lambda m: f"${int(m.group(1)) - 1}", where_extra)
        count_params = params[1:]

    total = await database.fetchval(
        "SELECT COUNT(*) FROM mcp_servers s"
        " LEFT JOIN mcp_categories mc ON s.category_id = mc.id"
        " WHERE s.is_active = TRUE" + count_where,
        *count_params,
    )

    offset = (page - 1) * page_size
    params.extend([page_size, offset])
    rows = await database.fetch(
        _SERVER_LIST_SELECT + where_extra
        + f" ORDER BY s.is_featured DESC, s.sort_order, s.name"
        f" LIMIT ${len(params) - 1} OFFSET ${len(params)}",
        *params,
    )

    return PaginatedResponse.build(
        items=[_row_to_server_list(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── Server detail ─────────────────────────────────────────────────────────────

@router.get("/servers/{slug}", response_model=MCPServerDetailResponse)
async def get_server(slug: str, current_user: dict = Depends(require_permission("mcp.catalog.view"))):
    row = await database.fetchrow(
        _SERVER_DETAIL_SELECT + " AND s.slug = $2",
        current_user["id"], slug,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Servidor MCP não encontrado")

    server_id = row["id"]
    tools = await database.fetch(
        "SELECT * FROM mcp_tools WHERE server_id = $1 ORDER BY sort_order", server_id
    )
    agents = await database.fetch(
        "SELECT * FROM mcp_agents WHERE server_id = $1 ORDER BY sort_order", server_id
    )
    resources = await database.fetch(
        "SELECT * FROM mcp_resources WHERE server_id = $1 ORDER BY sort_order", server_id
    )
    snippets = await database.fetch(
        "SELECT * FROM mcp_config_snippets WHERE server_id = $1 ORDER BY sort_order", server_id
    )

    d = dict(row)
    d["tools"] = [_row_to_tool(t) for t in tools]
    d["agents"] = [_row_to_agent(a) for a in agents]
    d["resources"] = [_row_to_resource(r) for r in resources]
    d["config_snippets"] = [_row_to_snippet(s) for s in snippets]
    return _row_to_server_detail(d)


# ── Favorite toggle ───────────────────────────────────────────────────────────

@router.post("/servers/{server_id}/favorite")
async def toggle_favorite(
    server_id: UUID,
    current_user: dict = Depends(require_permission("mcp.catalog.view")),
):
    exists = await database.fetchval(
        "SELECT 1 FROM mcp_favorites WHERE user_id = $1 AND server_id = $2",
        current_user["id"], server_id,
    )
    if exists:
        await database.execute(
            "DELETE FROM mcp_favorites WHERE user_id = $1 AND server_id = $2",
            current_user["id"], server_id,
        )
        return {"is_favorite": False}
    await database.execute(
        "INSERT INTO mcp_favorites (user_id, server_id) VALUES ($1, $2)",
        current_user["id"], server_id,
    )
    return {"is_favorite": True}


# ── Install / Uninstall ───────────────────────────────────────────────────────

@router.post("/servers/{server_id}/install")
async def register_install(
    server_id: UUID,
    body: MCPInstallCreate,
    current_user: dict = Depends(require_permission("mcp.catalog.view")),
):
    row = await database.fetchrow(
        """
        INSERT INTO mcp_installations (server_id, user_id, client_type)
        VALUES ($1, $2, $3::mcp_client_type)
        ON CONFLICT (server_id, user_id) DO UPDATE
            SET client_type = EXCLUDED.client_type,
                installed_at = NOW()
        RETURNING installed_at
        """,
        server_id, current_user["id"],
        body.client_type.value if body.client_type else None,
    )
    return {"is_installed": True, "installed_at": row["installed_at"]}


@router.delete("/servers/{server_id}/install")
async def remove_install(
    server_id: UUID,
    current_user: dict = Depends(require_permission("mcp.catalog.view")),
):
    await database.execute(
        "DELETE FROM mcp_installations WHERE server_id = $1 AND user_id = $2",
        server_id, current_user["id"],
    )
    return {"is_installed": False}


# ── Reviews ───────────────────────────────────────────────────────────────────

@router.get("/servers/{server_id}/reviews", response_model=PaginatedResponse[MCPReviewResponse])
async def list_reviews(
    server_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: dict = Depends(require_permission("mcp.catalog.view")),
):
    total = await database.fetchval(
        "SELECT COUNT(*) FROM mcp_reviews WHERE server_id = $1 AND is_approved = TRUE",
        server_id,
    )
    offset = (page - 1) * page_size
    rows = await database.fetch(
        """
        SELECT r.id, r.rating, r.comment, r.created_at,
               u.name AS user_name, u.organ AS user_organ
        FROM mcp_reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.server_id = $1 AND r.is_approved = TRUE
        ORDER BY r.created_at DESC
        LIMIT $2 OFFSET $3
        """,
        server_id, page_size, offset,
    )
    items = [MCPReviewResponse.model_validate(dict(r)) for r in rows]
    return PaginatedResponse.build(items=items, total=total, page=page, page_size=page_size)


@router.post("/servers/{server_id}/reviews", response_model=MCPReviewResponse, status_code=status.HTTP_201_CREATED)
async def upsert_review(
    server_id: UUID,
    body: MCPReviewCreate,
    current_user: dict = Depends(require_permission("mcp.catalog.view")),
):
    if not (1 <= body.rating <= 5):
        raise HTTPException(status_code=422, detail="rating deve estar entre 1 e 5")

    row = await database.fetchrow(
        """
        INSERT INTO mcp_reviews (server_id, user_id, rating, comment)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (server_id, user_id) DO UPDATE
            SET rating = EXCLUDED.rating,
                comment = EXCLUDED.comment
        RETURNING id, rating, comment, created_at
        """,
        server_id, current_user["id"], body.rating, body.comment,
    )
    return MCPReviewResponse.model_validate({
        **dict(row),
        "user_name": current_user["name"],
        "user_organ": current_user["organ"],
    })


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(_: dict = Depends(get_current_user)):
    total_servers = await database.fetchval(
        "SELECT COUNT(*) FROM mcp_servers WHERE is_active = TRUE"
    )
    total_tools = await database.fetchval(
        "SELECT COUNT(*) FROM mcp_tools t"
        " JOIN mcp_servers s ON t.server_id = s.id WHERE s.is_active = TRUE"
    )
    total_agents = await database.fetchval(
        "SELECT COUNT(*) FROM mcp_agents a"
        " JOIN mcp_servers s ON a.server_id = s.id WHERE s.is_active = TRUE"
    )
    total_installations = await database.fetchval("SELECT COUNT(*) FROM mcp_installations")

    top_installed = await database.fetch(
        "SELECT name, slug, install_count FROM mcp_servers"
        " WHERE is_active = TRUE ORDER BY install_count DESC LIMIT 5"
    )
    installs_by_organ = await database.fetch(
        """
        SELECT u.organ, COUNT(*)::int AS count
        FROM mcp_installations mi
        JOIN users u ON mi.user_id = u.id
        GROUP BY u.organ
        ORDER BY count DESC
        LIMIT 10
        """
    )
    return {
        "total_servers": total_servers,
        "total_tools": total_tools,
        "total_agents": total_agents,
        "total_installations": total_installations,
        "top_installed": [dict(r) for r in top_installed],
        "installs_by_organ": [dict(r) for r in installs_by_organ],
    }


# ── Admin / Gestor: Server CRUD ───────────────────────────────────────────────

@router.post("/servers", response_model=MCPServerDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    body: MCPServerCreate,
    current_user: dict = Depends(require_permission("admin.mcp.manage")),
):
    slug = body.slug or _slugify(body.name)
    row = await database.fetchrow(
        """
        INSERT INTO mcp_servers
            (name, slug, tagline, description, category_id, status,
             is_verified, is_featured, is_official,
             repository_url, docs_url, homepage_url,
             version, license, compatible_models,
             author_name, author_org, submitted_by, tags)
        VALUES ($1,$2,$3,$4,$5,$6::mcp_server_status,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19)
        RETURNING id
        """,
        body.name, slug, body.tagline, body.description, body.category_id,
        body.status.value, body.is_verified, body.is_featured, body.is_official,
        body.repository_url, body.docs_url, body.homepage_url,
        body.version, body.license, body.compatible_models,
        body.author_name, body.author_org, current_user["id"], body.tags,
    )
    return await _fetch_server_detail(row["id"], current_user["id"])


@router.put("/servers/{server_id}", response_model=MCPServerDetailResponse)
async def update_server(
    server_id: UUID,
    body: MCPServerUpdate,
    current_user: dict = Depends(require_permission("admin.mcp.manage")),
):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    fields, values = [], [server_id]
    for field, value in data.items():
        if field == "status":
            fields.append(f"{field} = ${len(values) + 1}::mcp_server_status")
            values.append(value.value if isinstance(value, MCPServerStatus) else value)
        else:
            fields.append(f"{field} = ${len(values) + 1}")
            values.append(value)

    result = await database.execute(
        f"UPDATE mcp_servers SET {', '.join(fields)} WHERE id = $1 AND is_active = TRUE",
        *values,
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Servidor MCP não encontrado")
    return await _fetch_server_detail(server_id, current_user["id"])


@router.delete("/servers/{server_id}")
async def delete_server(
    server_id: UUID,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    result = await database.execute(
        "UPDATE mcp_servers SET is_active = FALSE WHERE id = $1", server_id
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Servidor MCP não encontrado")
    return {"message": "Servidor desativado"}


@router.delete("/servers/{server_id}/permanent")
async def permanent_delete_server(
    server_id: UUID,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    row = await database.fetchrow(
        "SELECT is_active FROM mcp_servers WHERE id = $1", server_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Servidor MCP não encontrado")
    if row["is_active"]:
        raise HTTPException(status_code=400, detail="Desative o servidor antes de excluí-lo permanentemente")

    await database.execute("DELETE FROM mcp_servers WHERE id = $1", server_id)
    return {"message": "Servidor excluído permanentemente"}


# ── Admin / Gestor: Tools CRUD ────────────────────────────────────────────────

@router.post("/servers/{server_id}/tools", response_model=MCPToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    server_id: UUID,
    body: MCPToolCreate,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    row = await database.fetchrow(
        """
        INSERT INTO mcp_tools (server_id, name, description, parameters, return_type, example_call, sort_order)
        VALUES ($1,$2,$3,$4::jsonb,$5,$6,$7)
        RETURNING *
        """,
        server_id, body.name, body.description,
        json.dumps([p.model_dump() for p in body.parameters]),
        body.return_type, body.example_call, body.sort_order,
    )
    return _row_to_tool(row)


@router.put("/servers/{server_id}/tools/{tool_id}", response_model=MCPToolResponse)
async def update_tool(
    server_id: UUID,
    tool_id: UUID,
    body: MCPToolUpdate,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    fields, values = [], [tool_id, server_id]
    for field, value in data.items():
        if field == "parameters":
            fields.append(f"{field} = ${len(values) + 1}::jsonb")
            values.append(json.dumps([p.model_dump() for p in value]))
        else:
            fields.append(f"{field} = ${len(values) + 1}")
            values.append(value)

    row = await database.fetchrow(
        f"UPDATE mcp_tools SET {', '.join(fields)} WHERE id = $1 AND server_id = $2 RETURNING *",
        *values,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Tool não encontrada")
    return _row_to_tool(row)


@router.delete("/servers/{server_id}/tools/{tool_id}")
async def delete_tool(
    server_id: UUID,
    tool_id: UUID,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    result = await database.execute(
        "DELETE FROM mcp_tools WHERE id = $1 AND server_id = $2", tool_id, server_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Tool não encontrada")
    return {"message": "Tool removida"}


# ── Admin / Gestor: Agents CRUD ───────────────────────────────────────────────

@router.post("/servers/{server_id}/agents", response_model=MCPAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    server_id: UUID,
    body: MCPAgentCreate,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    row = await database.fetchrow(
        """
        INSERT INTO mcp_agents (server_id, name, description, capabilities, base_model, system_prompt, sort_order)
        VALUES ($1,$2,$3,$4,$5,$6,$7)
        RETURNING *
        """,
        server_id, body.name, body.description,
        body.capabilities, body.base_model, body.system_prompt, body.sort_order,
    )
    return _row_to_agent(row)


@router.put("/servers/{server_id}/agents/{agent_id}", response_model=MCPAgentResponse)
async def update_agent(
    server_id: UUID,
    agent_id: UUID,
    body: MCPAgentUpdate,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    fields, values = [], [agent_id, server_id]
    for field, value in data.items():
        fields.append(f"{field} = ${len(values) + 1}")
        values.append(value)

    row = await database.fetchrow(
        f"UPDATE mcp_agents SET {', '.join(fields)} WHERE id = $1 AND server_id = $2 RETURNING *",
        *values,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Agent não encontrado")
    return _row_to_agent(row)


@router.delete("/servers/{server_id}/agents/{agent_id}")
async def delete_agent(
    server_id: UUID,
    agent_id: UUID,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    result = await database.execute(
        "DELETE FROM mcp_agents WHERE id = $1 AND server_id = $2", agent_id, server_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Agent não encontrado")
    return {"message": "Agent removido"}


# ── Admin / Gestor: Resources CRUD ───────────────────────────────────────────

@router.post("/servers/{server_id}/resources", response_model=MCPResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    server_id: UUID,
    body: MCPResourceCreate,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    row = await database.fetchrow(
        """
        INSERT INTO mcp_resources (server_id, name, uri_template, description, mime_type, sort_order)
        VALUES ($1,$2,$3,$4,$5,$6)
        RETURNING *
        """,
        server_id, body.name, body.uri_template, body.description, body.mime_type, body.sort_order,
    )
    return _row_to_resource(row)


@router.put("/servers/{server_id}/resources/{resource_id}", response_model=MCPResourceResponse)
async def update_resource(
    server_id: UUID,
    resource_id: UUID,
    body: MCPResourceUpdate,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    fields, values = [], [resource_id, server_id]
    for field, value in data.items():
        fields.append(f"{field} = ${len(values) + 1}")
        values.append(value)

    row = await database.fetchrow(
        f"UPDATE mcp_resources SET {', '.join(fields)} WHERE id = $1 AND server_id = $2 RETURNING *",
        *values,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Resource não encontrado")
    return _row_to_resource(row)


@router.delete("/servers/{server_id}/resources/{resource_id}")
async def delete_resource(
    server_id: UUID,
    resource_id: UUID,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    result = await database.execute(
        "DELETE FROM mcp_resources WHERE id = $1 AND server_id = $2", resource_id, server_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Resource não encontrado")
    return {"message": "Resource removido"}


# ── Admin / Gestor: Config Snippets CRUD ─────────────────────────────────────

@router.post("/servers/{server_id}/snippets", response_model=MCPConfigSnippetResponse, status_code=status.HTTP_201_CREATED)
async def create_snippet(
    server_id: UUID,
    body: MCPConfigSnippetCreate,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    row = await database.fetchrow(
        """
        INSERT INTO mcp_config_snippets (server_id, client_type, label, config_json, notes, sort_order)
        VALUES ($1,$2::mcp_client_type,$3,$4,$5,$6)
        RETURNING *
        """,
        server_id, body.client_type.value, body.label, body.config_json, body.notes, body.sort_order,
    )
    return _row_to_snippet(row)


@router.put("/servers/{server_id}/snippets/{snippet_id}", response_model=MCPConfigSnippetResponse)
async def update_snippet(
    server_id: UUID,
    snippet_id: UUID,
    body: MCPConfigSnippetUpdate,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    fields, values = [], [snippet_id, server_id]
    for field, value in data.items():
        if field == "client_type":
            fields.append(f"{field} = ${len(values) + 1}::mcp_client_type")
            values.append(value.value if isinstance(value, MCPClientType) else value)
        else:
            fields.append(f"{field} = ${len(values) + 1}")
            values.append(value)

    row = await database.fetchrow(
        f"UPDATE mcp_config_snippets SET {', '.join(fields)} WHERE id = $1 AND server_id = $2 RETURNING *",
        *values,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Snippet não encontrado")
    return _row_to_snippet(row)


@router.delete("/servers/{server_id}/snippets/{snippet_id}")
async def delete_snippet(
    server_id: UUID,
    snippet_id: UUID,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    result = await database.execute(
        "DELETE FROM mcp_config_snippets WHERE id = $1 AND server_id = $2", snippet_id, server_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Snippet não encontrado")
    return {"message": "Snippet removido"}


# ── Admin: Review moderation ──────────────────────────────────────────────────

@router.put("/reviews/{review_id}/approve")
async def approve_review(review_id: UUID, _: dict = Depends(require_permission("admin.mcp.manage"))):
    row = await database.fetchrow(
        "UPDATE mcp_reviews SET is_approved = NOT is_approved WHERE id = $1 RETURNING is_approved",
        review_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    return {"is_approved": row["is_approved"]}


@router.delete("/reviews/{review_id}")
async def delete_review(review_id: UUID, _: dict = Depends(require_permission("admin.mcp.manage"))):
    result = await database.execute("DELETE FROM mcp_reviews WHERE id = $1", review_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    return {"message": "Avaliação removida"}


# ── Admin: All servers (including inactive) ───────────────────────────────────

@router.get("/admin/servers", response_model=PaginatedResponse[MCPServerListResponse])
async def admin_list_servers(
    search: str | None = None,
    category_slug: str | None = None,
    status: MCPServerStatus | None = None,
    is_verified: bool | None = None,
    include_inactive: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    current_user: dict = Depends(require_permission("admin.mcp.manage")),
):
    params: list = []
    conditions: list[str] = []

    if not include_inactive:
        conditions.append("s.is_active = TRUE")
    if search:
        params.append(search)
        n = len(params)
        conditions.append(
            f"(s.name ILIKE '%' || ${n} || '%' OR s.slug ILIKE '%' || ${n} || '%')"
        )
    if category_slug:
        params.append(category_slug)
        conditions.append(f"mc.slug = ${len(params)}")
    if status:
        params.append(status.value)
        conditions.append(f"s.status = ${len(params)}::mcp_server_status")
    if is_verified is not None:
        params.append(is_verified)
        conditions.append(f"s.is_verified = ${len(params)}")

    where_extra = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    base = """
        SELECT
            s.id, s.name, s.slug, s.tagline, s.status, s.is_verified, s.is_featured,
            s.is_official, s.tags, s.rating_avg, s.rating_count, s.install_count,
            s.compatible_models, s.sort_order, s.is_active,
            mc.id AS cat_id, mc.name AS cat_name, mc.slug AS cat_slug,
            mc.description AS cat_description, mc.icon AS cat_icon, mc.color AS cat_color,
            (SELECT COUNT(*) FROM mcp_tools  WHERE server_id = s.id)::int AS tool_count,
            (SELECT COUNT(*) FROM mcp_agents WHERE server_id = s.id)::int AS agent_count,
            FALSE AS is_favorite, FALSE AS is_installed
        FROM mcp_servers s
        LEFT JOIN mcp_categories mc ON s.category_id = mc.id
    """

    total = await database.fetchval(
        f"SELECT COUNT(*) FROM mcp_servers s LEFT JOIN mcp_categories mc ON s.category_id = mc.id{where_extra}",
        *params,
    )
    offset = (page - 1) * page_size
    params.extend([page_size, offset])
    rows = await database.fetch(
        base + where_extra + f" ORDER BY s.is_active DESC, s.sort_order, s.name LIMIT ${len(params)-1} OFFSET ${len(params)}",
        *params,
    )
    return PaginatedResponse.build(
        items=[_row_to_server_list(r) for r in rows],
        total=total, page=page, page_size=page_size,
    )


# ── Admin: All reviews ────────────────────────────────────────────────────────

class AdminReviewResponse(MCPReviewResponse):
    server_name: str
    server_slug: str
    is_approved: bool

    model_config = ConfigDict(from_attributes=True)


@router.get("/admin/reviews")
async def admin_list_reviews(
    server_id: UUID | None = None,
    is_approved: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    conditions = []
    params: list = []

    if server_id:
        params.append(server_id)
        conditions.append(f"r.server_id = ${len(params)}")
    if is_approved is not None:
        params.append(is_approved)
        conditions.append(f"r.is_approved = ${len(params)}")

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    total = await database.fetchval(
        f"SELECT COUNT(*) FROM mcp_reviews r{where}", *params
    )
    offset = (page - 1) * page_size
    params.extend([page_size, offset])
    rows = await database.fetch(
        f"""
        SELECT r.id, r.rating, r.comment, r.is_approved, r.created_at,
               u.name AS user_name, u.organ AS user_organ,
               s.name AS server_name, s.slug AS server_slug
        FROM mcp_reviews r
        JOIN users u ON r.user_id = u.id
        JOIN mcp_servers s ON r.server_id = s.id
        {where}
        ORDER BY r.created_at DESC
        LIMIT ${len(params)-1} OFFSET ${len(params)}
        """,
        *params,
    )
    items = [dict(r) for r in rows]
    return {"items": items, "total": total, "page": page, "page_size": page_size,
            "pages": -(-total // page_size)}


# ── Admin: Categories CRUD ────────────────────────────────────────────────────

@router.post("/categories", response_model=MCPCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    body: MCPCategoryCreate,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    slug = body.slug or _slugify(body.name)
    row = await database.fetchrow(
        """
        INSERT INTO mcp_categories (name, slug, description, icon, color, sort_order)
        VALUES ($1,$2,$3,$4,$5,$6)
        RETURNING *, 0::int AS server_count
        """,
        body.name, slug, body.description, body.icon, body.color, body.sort_order,
    )
    return MCPCategoryResponse.model_validate(dict(row))


@router.put("/categories/{category_id}", response_model=MCPCategoryResponse)
async def update_category(
    category_id: UUID,
    body: MCPCategoryUpdate,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    fields, values = [], [category_id]
    for field, value in data.items():
        fields.append(f"{field} = ${len(values) + 1}")
        values.append(value)

    row = await database.fetchrow(
        f"UPDATE mcp_categories SET {', '.join(fields)} WHERE id = $1 RETURNING *",
        *values,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    count = await database.fetchval(
        "SELECT COUNT(*) FROM mcp_servers WHERE category_id = $1 AND is_active = TRUE",
        category_id,
    )
    return MCPCategoryResponse.model_validate({**dict(row), "server_count": count})


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: UUID,
    _: dict = Depends(require_permission("admin.mcp.manage")),
):
    result = await database.execute(
        "UPDATE mcp_categories SET is_active = FALSE WHERE id = $1", category_id
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return {"message": "Categoria desativada"}
