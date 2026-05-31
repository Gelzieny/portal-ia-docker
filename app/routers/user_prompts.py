import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core import database
from app.core.deps import require_permission
from app.models.pagination import PaginatedResponse
from app.models.prompt import PromptResponse
from app.models.user_prompt import (
    PromptArchiveBody,
    PromptForkCreate,
    PromptForkResponse,
    PromptPublicationDecision,
    PromptReassign,
    PromptReportCreate,
    PromptReportDecision,
    PromptReportResponse,
    PromptVersionResponse,
    UserPromptSave,
    UserPromptSubmit,
)

router = APIRouter(tags=["User Prompts & Curation"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_prompt(row, *, is_owner: bool = False) -> PromptResponse:
    """Converte asyncpg Row em PromptResponse, tratando category e author."""
    d = dict(row)
    if isinstance(d.get("variables"), str):
        d["variables"] = json.loads(d["variables"])

    # Categoria aninhada (presente quando a query faz JOIN em prompt_categories)
    if d.get("cat_id"):
        d["category"] = {
            "id": d.pop("cat_id"),
            "name": d.pop("cat_name"),
            "slug": d.pop("cat_slug"),
            "color": d.pop("cat_color"),
            "icon": d.pop("cat_icon", "FileText"),
            "description": d.pop("cat_description", ""),
            "sort_order": d.pop("cat_sort_order"),
            "prompt_count": d.pop("cat_prompt_count", 0),
        }
    else:
        for k in ("cat_id", "cat_name", "cat_slug", "cat_color", "cat_icon",
                  "cat_description", "cat_sort_order", "cat_prompt_count"):
            d.pop(k, None)
        d["category"] = None

    # Autor (presente quando a query faz JOIN em users)
    author_name = d.pop("author_name", None)
    author_organ = d.pop("author_organ", None)
    if author_name:
        d["author"] = {
            "id": d.get("author_id"),
            "name": d.get("original_author_name") or author_name,
            "organ": author_organ or "",
        }
    else:
        d["author"] = None

    # Campos com default nos selects — garantir que existam
    d.setdefault("is_favorite", False)
    d.setdefault("user_has_used", False)
    d.setdefault("is_owner", is_owner)
    d.setdefault("user_has_reported", False)

    return PromptResponse.model_validate(d)


def _simple_response(row: dict, *, is_owner: bool = True) -> PromptResponse:
    """Converte resultado de INSERT/UPDATE simples (sem JOIN) em PromptResponse."""
    d = dict(row) if not isinstance(row, dict) else row
    if isinstance(d.get("variables"), str):
        d["variables"] = json.loads(d["variables"])
    for k in ("cat_id", "cat_name", "cat_slug", "cat_color", "cat_icon",
              "cat_description", "cat_sort_order", "cat_prompt_count"):
        d.pop(k, None)
    d.update(
        category=None, author=None,
        is_favorite=False, user_has_used=False,
        is_owner=is_owner, user_has_reported=False,
    )
    return PromptResponse.model_validate(d)


# ── Query templates ───────────────────────────────────────────────────────────

_MY_SELECT = """
    p.*,
    pc.id          AS cat_id,
    pc.name        AS cat_name,
    pc.slug        AS cat_slug,
    pc.color       AS cat_color,
    pc.icon        AS cat_icon,
    pc.description AS cat_description,
    pc.sort_order  AS cat_sort_order,
    0              AS cat_prompt_count,
    (pf.user_id IS NOT NULL) AS is_favorite,
    (EXISTS (
        SELECT 1 FROM prompt_usages pu
        WHERE pu.prompt_id = p.id AND pu.user_id = $1
    )) AS user_has_used,
    TRUE  AS is_owner,
    FALSE AS user_has_reported
"""

_MY_FROM = """
    FROM prompts p
    LEFT JOIN prompt_categories pc ON p.category_id = pc.id
    LEFT JOIN prompt_favorites  pf ON p.id = pf.prompt_id AND pf.user_id = $1
    WHERE p.author_id = $1 AND p.source = 'comunidade'
"""

_CUR_SELECT = """
    p.*,
    pc.id          AS cat_id,
    pc.name        AS cat_name,
    pc.slug        AS cat_slug,
    pc.color       AS cat_color,
    pc.icon        AS cat_icon,
    pc.description AS cat_description,
    pc.sort_order  AS cat_sort_order,
    0              AS cat_prompt_count,
    FALSE          AS is_favorite,
    FALSE          AS user_has_used,
    FALSE          AS is_owner,
    FALSE          AS user_has_reported,
    COALESCE(p.original_author_name, u.name) AS author_name,
    COALESCE(u.organ, '')                    AS author_organ
"""

_CUR_FROM = """
    FROM prompts p
    LEFT JOIN prompt_categories pc ON p.category_id = pc.id
    LEFT JOIN users u ON p.author_id = u.id
"""

_VERSION_QUERY = """
    SELECT pv.version_number, pv.title, pv.approved_at, u.name AS approved_by_name
    FROM prompt_versions pv
    LEFT JOIN users u ON pv.approved_by = u.id
    WHERE pv.prompt_id = $1
    ORDER BY pv.version_number DESC
"""


async def _notify(title: str, message: str, link: str | None = None, ntype: str = "info") -> None:
    """Cria notificação global.
    TODO: evoluir para sistema per-user (requer migration com user_id em notifications).
    """
    await database.execute(
        "INSERT INTO notifications (type, title, message, link, is_global) "
        "VALUES ($1::notification_type, $2, $3, $4, TRUE)",
        ntype, title, message, link,
    )


# ─────────────────────────────────────────────────────────────────────────────
# MY PROMPTS — CRUD do criador
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/my-prompts", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_my_prompt(
    body: UserPromptSave,
    current_user: dict = Depends(require_permission("prompts.my.view")),
):
    row = await database.fetchrow(
        """
        INSERT INTO prompts
            (title, description, content, category_id, difficulty, tags, variables,
             model_id, author_id, original_author_name, source,
             publication_status, is_public, is_active)
        VALUES ($1,$2,$3,$4,$5::prompt_difficulty,$6,$7::jsonb,$8,$9,$10,
                'comunidade', $11::prompt_publication_status, FALSE, TRUE)
        RETURNING *
        """,
        body.title, body.description, body.content,
        body.category_id, body.difficulty, body.tags,
        json.dumps(body.variables), body.model_id,
        current_user["id"], current_user["name"],
        body.save_as,
    )
    return _simple_response(dict(row))


@router.get("/my-prompts", response_model=PaginatedResponse[PromptResponse])
async def list_my_prompts(
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_permission("prompts.my.view")),
):
    params: list = [current_user["id"]]
    conditions: list[str] = []

    if status_filter:
        params.append(status_filter)
        conditions.append(f"p.publication_status = ${len(params)}::prompt_publication_status")
    if search:
        params.append(f"%{search}%")
        conditions.append(f"(p.title ILIKE ${len(params)} OR p.description ILIKE ${len(params)})")

    extra = (" AND " + " AND ".join(conditions)) if conditions else ""

    total = await database.fetchval(
        f"SELECT COUNT(*) {_MY_FROM}{extra}", *params
    )
    offset = (page - 1) * page_size
    params.extend([page_size, offset])
    rows = await database.fetch(
        f"SELECT {_MY_SELECT} {_MY_FROM}{extra}"
        f" ORDER BY p.updated_at DESC"
        f" LIMIT ${len(params) - 1} OFFSET ${len(params)}",
        *params,
    )
    return PaginatedResponse.build([_build_prompt(r) for r in rows], total, page, page_size)


# ATENÇÃO: /fork/{original_id} deve ficar antes de /{prompt_id} para evitar
# que o FastAPI tente resolver "fork" como UUID e retorne 422.
@router.post("/my-prompts/fork/{original_id}", response_model=PromptForkResponse, status_code=status.HTTP_201_CREATED)
async def fork_prompt(
    original_id: UUID,
    body: PromptForkCreate,
    current_user: dict = Depends(require_permission("prompts.my.view")),
):
    original = await database.fetchrow(
        "SELECT * FROM prompts WHERE id = $1 AND publication_status = 'publico' AND is_active = TRUE",
        original_id,
    )
    if original is None:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")

    variables = original["variables"]
    if not isinstance(variables, str):
        variables = json.dumps(variables)

    fork = await database.fetchrow(
        """
        INSERT INTO prompts
            (title, description, content, category_id, difficulty, tags, variables,
             model_id, author_id, original_author_name, source,
             publication_status, is_public, is_active)
        VALUES ($1,$2,$3,$4,$5::prompt_difficulty,$6,$7::jsonb,$8,$9,$10,
                'comunidade','privado',FALSE,TRUE)
        RETURNING id
        """,
        f"[Fork] {original['title']}", original["description"],
        original["content"], original["category_id"],
        original["difficulty"], original["tags"], variables,
        original["model_id"], current_user["id"], current_user["name"],
    )
    fork_id = fork["id"]
    await database.execute(
        "INSERT INTO prompt_forks (original_id, fork_id, fork_message) VALUES ($1,$2,$3)",
        original_id, fork_id, body.fork_message,
    )
    return PromptForkResponse(
        fork_id=fork_id,
        message="Fork criado com sucesso. Edite e submeta para publicação quando estiver pronto.",
    )


@router.get("/my-prompts/{prompt_id}", response_model=PromptResponse)
async def get_my_prompt(
    prompt_id: UUID,
    current_user: dict = Depends(require_permission("prompts.my.view")),
):
    row = await database.fetchrow(
        f"SELECT {_MY_SELECT} {_MY_FROM} AND p.id = $2",
        current_user["id"], prompt_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    if row["author_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")

    result = _build_prompt(row)
    version_rows = await database.fetch(_VERSION_QUERY, prompt_id)
    result.versions = [PromptVersionResponse.model_validate(dict(r)) for r in version_rows]
    return result


@router.put("/my-prompts/{prompt_id}", response_model=PromptResponse)
async def update_my_prompt(
    prompt_id: UUID,
    body: UserPromptSave,
    current_user: dict = Depends(require_permission("prompts.my.view")),
):
    prompt = await database.fetchrow(
        "SELECT * FROM prompts WHERE id = $1 AND author_id = $2 AND source = 'comunidade'",
        prompt_id, current_user["id"],
    )
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    if prompt["publication_status"] == "arquivado":
        raise HTTPException(status_code=400, detail="Restaure o prompt antes de editá-lo")

    re_submitted = False

    # Prompts públicos ou em revisão: snapshot + re-aprovação obrigatória
    if prompt["publication_status"] in ("publico", "em_revisao"):
        new_status = "aguardando"
        variables = prompt["variables"]
        if not isinstance(variables, str):
            variables = json.dumps(variables)
        await database.execute(
            """
            INSERT INTO prompt_versions
                (prompt_id, version_number, title, description, content, variables, tags,
                 approved_by, approved_at)
            VALUES ($1,$2,$3,$4,$5,$6::jsonb,$7,$8,COALESCE($9, NOW()))
            ON CONFLICT (prompt_id, version_number) DO NOTHING
            """,
            prompt_id, prompt["version"],
            prompt["title"], prompt["description"], prompt["content"],
            variables, prompt["tags"],
            prompt["reviewed_by"], prompt["reviewed_at"],
        )
        re_submitted = True
    elif prompt["publication_status"] in ("rascunho", "privado"):
        # Respeita o que o usuário escolheu (rascunho ou privado)
        new_status = body.save_as
    else:
        # aguardando — mantém status, apenas atualiza conteúdo
        new_status = prompt["publication_status"]

    row = await database.fetchrow(
        """
        UPDATE prompts SET
            title      = $2, description = $3, content    = $4,
            category_id = $5, difficulty = $6::prompt_difficulty,
            tags        = $7, variables  = $8::jsonb, model_id = $9,
            publication_status = $10::prompt_publication_status,
            is_public  = (CASE WHEN $10 = 'publico' THEN TRUE ELSE FALSE END),
            updated_at = NOW()
        WHERE id = $1
        RETURNING *
        """,
        prompt_id, body.title, body.description, body.content,
        body.category_id, body.difficulty, body.tags,
        json.dumps(body.variables), body.model_id, new_status,
    )

    if re_submitted:
        await _notify(
            title="Prompt atualizado aguarda re-aprovação",
            message=f"'{body.title}' foi editado por {current_user['name']} e precisa de nova análise.",
            link="/admin/curation",
        )

    return _simple_response(dict(row))


@router.delete("/my-prompts/{prompt_id}")
async def archive_my_prompt(
    prompt_id: UUID,
    current_user: dict = Depends(require_permission("prompts.my.view")),
):
    result = await database.execute(
        """
        UPDATE prompts
        SET publication_status = 'arquivado', is_public = FALSE,
            is_active = FALSE, updated_at = NOW()
        WHERE id = $1 AND author_id = $2 AND source = 'comunidade'
          AND publication_status != 'arquivado'
        """,
        prompt_id, current_user["id"],
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Prompt não encontrado ou já arquivado")
    return {"archived": True}


@router.post("/my-prompts/{prompt_id}/make-private", response_model=PromptResponse)
async def make_prompt_private(
    prompt_id: UUID,
    current_user: dict = Depends(require_permission("prompts.my.view")),
):
    """Promove um rascunho para privado sem precisar passar pelo formulário completo."""
    row = await database.fetchrow(
        """
        UPDATE prompts
        SET publication_status = 'privado', updated_at = NOW()
        WHERE id = $1 AND author_id = $2 AND source = 'comunidade'
          AND publication_status = 'rascunho'
        RETURNING *
        """,
        prompt_id, current_user["id"],
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Prompt não encontrado ou não está em rascunho")
    return _simple_response(dict(row))


@router.post("/my-prompts/{prompt_id}/restore", response_model=PromptResponse)
async def restore_my_prompt(
    prompt_id: UUID,
    current_user: dict = Depends(require_permission("prompts.my.view")),
):
    row = await database.fetchrow(
        """
        UPDATE prompts
        SET publication_status = 'privado', is_active = TRUE, updated_at = NOW()
        WHERE id = $1 AND author_id = $2 AND source = 'comunidade'
          AND publication_status = 'arquivado'
        RETURNING *
        """,
        prompt_id, current_user["id"],
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Prompt não encontrado ou não está arquivado")
    return _simple_response(dict(row))


@router.post("/my-prompts/{prompt_id}/submit", response_model=PromptResponse)
async def submit_my_prompt(
    prompt_id: UUID,
    body: UserPromptSubmit,
    current_user: dict = Depends(require_permission("prompts.my.view")),
):
    prompt = await database.fetchrow(
        "SELECT * FROM prompts WHERE id = $1 AND author_id = $2 AND source = 'comunidade'",
        prompt_id, current_user["id"],
    )
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    if prompt["publication_status"] != "privado":
        raise HTTPException(
            status_code=400,
            detail=f"Apenas prompts privados podem ser submetidos. Status atual: {prompt['publication_status']}",
        )
    if not all([prompt["title"], prompt["content"], prompt["category_id"]]):
        raise HTTPException(
            status_code=400,
            detail="Preencha título, conteúdo e categoria antes de submeter para aprovação",
        )

    row = await database.fetchrow(
        """
        UPDATE prompts
        SET publication_status = 'aguardando',
            submission_notes   = $2,
            submitted_at       = NOW(),
            updated_at         = NOW()
        WHERE id = $1
        RETURNING *
        """,
        prompt_id, body.submission_notes,
    )
    await _notify(
        title="Novo prompt aguarda curadoria",
        message=f"'{prompt['title']}' — enviado por {current_user['name']} ({current_user.get('organ', '')})",
        link="/admin/curation",
    )
    return _simple_response(dict(row))


@router.post("/my-prompts/{prompt_id}/withdraw", response_model=PromptResponse)
async def withdraw_my_prompt(
    prompt_id: UUID,
    current_user: dict = Depends(require_permission("prompts.my.view")),
):
    row = await database.fetchrow(
        """
        UPDATE prompts
        SET publication_status = 'privado', submitted_at = NULL, updated_at = NOW()
        WHERE id = $1 AND author_id = $2 AND source = 'comunidade'
          AND publication_status = 'aguardando'
        RETURNING *
        """,
        prompt_id, current_user["id"],
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Prompt não encontrado ou não está aguardando aprovação")
    return _simple_response(dict(row))


# ─────────────────────────────────────────────────────────────────────────────
# REPORTS — qualquer usuário autenticado
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/prompts/{prompt_id}/report", status_code=status.HTTP_201_CREATED)
async def report_prompt(
    prompt_id: UUID,
    body: PromptReportCreate,
    current_user: dict = Depends(require_permission("prompts.library.view")),
):
    prompt = await database.fetchrow(
        "SELECT author_id, title, publication_status FROM prompts WHERE id = $1",
        prompt_id,
    )
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    if prompt["publication_status"] not in ("publico", "em_revisao"):
        raise HTTPException(status_code=400, detail="Apenas prompts públicos podem ser denunciados")
    if str(prompt["author_id"]) == str(current_user["id"]):
        raise HTTPException(status_code=400, detail="Não é possível denunciar seu próprio prompt")

    try:
        await database.execute(
            """
            INSERT INTO prompt_reports (prompt_id, reporter_id, reason, description)
            VALUES ($1, $2, $3::report_reason, $4)
            """,
            prompt_id, current_user["id"], body.reason.value, body.description,
        )
    except Exception:
        raise HTTPException(status_code=409, detail="Você já denunciou este prompt")

    # O trigger handle_prompt_report cuida de report_count e em_revisao.
    # Verificamos aqui para emitir notificação se atingiu o threshold.
    report_count = await database.fetchval(
        "SELECT report_count FROM prompts WHERE id = $1", prompt_id
    )
    if report_count and report_count >= 3:
        await _notify(
            title="Prompt movido para revisão",
            message=f"'{prompt['title']}' recebeu {report_count} denúncias e foi movido para revisão.",
            link="/admin/curation?status=em_revisao",
            ntype="warning",
        )

    return {"reported": True}


@router.get("/prompts/{prompt_id}/report-status")
async def get_report_status(
    prompt_id: UUID,
    current_user: dict = Depends(require_permission("prompts.library.view")),
):
    exists = await database.fetchval(
        "SELECT 1 FROM prompt_reports WHERE prompt_id = $1 AND reporter_id = $2",
        prompt_id, current_user["id"],
    )
    return {"has_reported": exists is not None}


# ─────────────────────────────────────────────────────────────────────────────
# CURATION — admin, gestor, curador
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/curation/prompts", response_model=PaginatedResponse[PromptResponse])
async def curation_list_prompts(
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: dict = Depends(require_permission("admin.prompt_curation.manage")),
):
    if status_filter in ("aguardando", "em_revisao"):
        where = f"WHERE p.publication_status = '{status_filter}'"
    else:
        where = "WHERE p.publication_status IN ('aguardando', 'em_revisao')"

    total = await database.fetchval(f"SELECT COUNT(*) {_CUR_FROM} {where}")
    offset = (page - 1) * page_size
    rows = await database.fetch(
        f"SELECT {_CUR_SELECT} {_CUR_FROM} {where}"
        f" ORDER BY p.submitted_at ASC NULLS LAST, p.created_at ASC"
        f" LIMIT $1 OFFSET $2",
        page_size, offset,
    )
    return PaginatedResponse.build([_build_prompt(r) for r in rows], total, page, page_size)


# ATENÇÃO: /count ANTES de /{prompt_id} para evitar "count" ser resolvido como UUID
@router.get("/curation/prompts/count")
async def curation_count(
    _: dict = Depends(require_permission("admin.prompt_curation.manage")),
):
    row = await database.fetchrow(
        """
        SELECT
            COUNT(*) FILTER (WHERE publication_status = 'aguardando') AS aguardando,
            COUNT(*) FILTER (WHERE publication_status = 'em_revisao')  AS em_revisao,
            COUNT(*)                                                    AS total
        FROM prompts
        WHERE publication_status IN ('aguardando', 'em_revisao')
        """
    )
    return dict(row)


@router.get("/curation/prompts/{prompt_id}", response_model=PromptResponse)
async def curation_get_prompt(
    prompt_id: UUID,
    _: dict = Depends(require_permission("admin.prompt_curation.manage")),
):
    row = await database.fetchrow(
        f"SELECT {_CUR_SELECT} {_CUR_FROM} WHERE p.id = $1",
        prompt_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")

    result = _build_prompt(row)
    version_rows = await database.fetch(_VERSION_QUERY, prompt_id)
    result.versions = [PromptVersionResponse.model_validate(dict(r)) for r in version_rows]
    return result


@router.put("/curation/prompts/{prompt_id}/decide", response_model=PromptResponse)
async def curation_decide(
    prompt_id: UUID,
    body: PromptPublicationDecision,
    curator: dict = Depends(require_permission("admin.prompt_curation.manage")),
):
    prompt = await database.fetchrow(
        "SELECT * FROM prompts WHERE id = $1 AND publication_status IN ('aguardando', 'em_revisao')",
        prompt_id,
    )
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt não encontrado na fila de curadoria")

    if body.action == "aprovar":
        # Snapshot da versão que está sendo aprovada
        variables = prompt["variables"]
        if not isinstance(variables, str):
            variables = json.dumps(variables)
        await database.execute(
            """
            INSERT INTO prompt_versions
                (prompt_id, version_number, title, description, content,
                 variables, tags, approved_by, approved_at)
            VALUES ($1,$2,$3,$4,$5,$6::jsonb,$7,$8,NOW())
            """,
            prompt_id, (prompt["version"] or 0) + 1,
            prompt["title"], prompt["description"], prompt["content"],
            variables, prompt["tags"], curator["id"],
        )
        row = await database.fetchrow(
            """
            UPDATE prompts
            SET publication_status = 'publico',
                is_public          = TRUE,
                reviewed_by        = $2,
                reviewed_at        = NOW(),
                review_notes       = $3,
                version            = version + 1,
                updated_at         = NOW()
            WHERE id = $1
            RETURNING *
            """,
            prompt_id, curator["id"], body.review_notes,
        )
        await _notify(
            title="Prompt aprovado e publicado",
            message=f"'{prompt['title']}' foi aprovado e está disponível na galeria.",
            link="/prompts",
            ntype="success",
        )
    else:  # negar
        row = await database.fetchrow(
            """
            UPDATE prompts
            SET publication_status = 'privado',
                is_public          = FALSE,
                reviewed_by        = $2,
                reviewed_at        = NOW(),
                review_notes       = $3,
                updated_at         = NOW()
            WHERE id = $1
            RETURNING *
            """,
            prompt_id, curator["id"], body.review_notes,
        )
        await _notify(
            title="Prompt não aprovado",
            message=f"'{prompt['title']}' não foi aprovado. Motivo: {body.review_notes}",
            link="/meus-prompts",
            ntype="warning",
        )

    return _simple_response(dict(row), is_owner=False)


@router.put("/curation/prompts/{prompt_id}/archive")
async def curation_archive(
    prompt_id: UUID,
    body: PromptArchiveBody,
    _: dict = Depends(require_permission("admin.prompt_curation.manage")),
):
    result = await database.execute(
        """
        UPDATE prompts
        SET publication_status = 'arquivado', is_public = FALSE,
            review_notes = $2, updated_at = NOW()
        WHERE id = $1
          AND publication_status IN ('publico', 'em_revisao', 'aguardando')
        """,
        prompt_id, body.reason,
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    return {"archived": True}


@router.put("/curation/prompts/{prompt_id}/restore-public")
async def curation_restore_public(
    prompt_id: UUID,
    _: dict = Depends(require_permission("admin.prompt_curation.manage")),
):
    row = await database.fetchrow(
        """
        UPDATE prompts
        SET publication_status = 'publico', is_public = TRUE,
            report_count = 0, updated_at = NOW()
        WHERE id = $1 AND publication_status = 'em_revisao'
        RETURNING id
        """,
        prompt_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Prompt não encontrado ou não está em revisão")
    # Descartar todas as denúncias pendentes deste prompt
    await database.execute(
        "UPDATE prompt_reports SET status = 'descartado' WHERE prompt_id = $1 AND status = 'pendente'",
        prompt_id,
    )
    return {"restored": True}


@router.put("/curation/prompts/{prompt_id}/reassign")
async def curation_reassign(
    prompt_id: UUID,
    body: PromptReassign,
    _: dict = Depends(require_permission("admin.prompt_curation.manage")),
):
    new_author = await database.fetchrow(
        "SELECT id, name FROM users WHERE id = $1 AND is_active = TRUE",
        body.new_author_id,
    )
    if new_author is None:
        raise HTTPException(status_code=404, detail="Usuário de destino não encontrado ou inativo")

    result = await database.execute(
        """
        UPDATE prompts
        SET author_id = $2, updated_at = NOW()
        WHERE id = $1 AND source = 'comunidade'
        """,
        prompt_id, body.new_author_id,
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Prompt não encontrado")

    await _notify(
        title="Prompt atribuído a você",
        message=f"Um prompt foi atribuído à sua conta.",
        link="/meus-prompts",
    )
    return {"reassigned": True, "new_author_name": new_author["name"]}


@router.get("/curation/reports", response_model=PaginatedResponse[PromptReportResponse])
async def curation_list_reports(
    prompt_id: UUID | None = None,
    reason: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _: dict = Depends(require_permission("admin.prompt_curation.manage")),
):
    conditions = []
    params: list = []

    # Por padrão, mostrar apenas pendentes; curador pode pedir outras
    if status_filter:
        params.append(status_filter)
        conditions.append(f"pr.status = ${len(params)}::report_status")
    else:
        conditions.append("pr.status = 'pendente'")

    if prompt_id:
        params.append(prompt_id)
        conditions.append(f"pr.prompt_id = ${len(params)}")
    if reason:
        params.append(reason)
        conditions.append(f"pr.reason = ${len(params)}::report_reason")

    where = "WHERE " + " AND ".join(conditions)
    total = await database.fetchval(
        f"SELECT COUNT(*) FROM prompt_reports pr {where}", *params
    )
    offset = (page - 1) * page_size
    params.extend([page_size, offset])
    rows = await database.fetch(
        f"""
        SELECT pr.*
        FROM prompt_reports pr
        {where}
        ORDER BY pr.created_at ASC
        LIMIT ${len(params) - 1} OFFSET ${len(params)}
        """,
        *params,
    )
    items = [PromptReportResponse.model_validate(dict(r)) for r in rows]
    return PaginatedResponse.build(items, total, page, page_size)


@router.put("/curation/reports/{report_id}/decide", response_model=PromptReportResponse)
async def curation_decide_report(
    report_id: UUID,
    body: PromptReportDecision,
    curator: dict = Depends(require_permission("admin.prompt_curation.manage")),
):
    row = await database.fetchrow(
        """
        UPDATE prompt_reports
        SET status           = $2::report_status,
            resolved_by      = $3,
            resolved_at      = NOW(),
            resolution_notes = $4
        WHERE id = $1 AND status = 'pendente'
        RETURNING *
        """,
        report_id, body.action, curator["id"], body.resolution_notes,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Denúncia não encontrada ou já resolvida")

    # Se descartada e não há mais denúncias pendentes, retornar prompt para público
    if body.action == "descartado":
        pending = await database.fetchval(
            "SELECT COUNT(*) FROM prompt_reports WHERE prompt_id = $1 AND status = 'pendente'",
            row["prompt_id"],
        )
        if pending == 0:
            await database.execute(
                """
                UPDATE prompts
                SET publication_status = 'publico', is_public = TRUE,
                    report_count = 0, updated_at = NOW()
                WHERE id = $1 AND publication_status = 'em_revisao'
                """,
                row["prompt_id"],
            )

    return PromptReportResponse.model_validate(dict(row))
