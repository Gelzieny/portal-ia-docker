import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core import database
from app.core.deps import require_any_permission, require_permission
from app.models.prompt import (
    PromptCategoryResponse,
    PromptCreate,
    PromptResponse,
    PromptReviewCreate,
    PromptReviewResponse,
    PromptUpdate,
)

router = APIRouter(prefix="/prompts", tags=["prompts"])


def _row_to_prompt(row, is_favorite: bool = False, user_has_used: bool = False) -> PromptResponse:
    d = dict(row)
    d["is_favorite"] = is_favorite
    d["user_has_used"] = user_has_used
    # variables é JSONB — asyncpg retorna str se não decodificado
    if isinstance(d.get("variables"), str):
        d["variables"] = json.loads(d["variables"])
    # category aninhada (se presente nos campos)
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
    # author (presente apenas em queries que fazem JOIN em users)
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
    return PromptResponse.model_validate(d)


_LIST_QUERY = """
    SELECT
        p.*,
        pc.id           AS cat_id,
        pc.name         AS cat_name,
        pc.slug         AS cat_slug,
        pc.color        AS cat_color,
        pc.icon         AS cat_icon,
        pc.description  AS cat_description,
        pc.sort_order   AS cat_sort_order,
        (SELECT COUNT(*) FROM prompts p2
         WHERE p2.category_id = pc.id
           AND p2.is_active = TRUE AND p2.publication_status = 'publico'
        )               AS cat_prompt_count,
        (pf.user_id IS NOT NULL)  AS is_favorite,
        (EXISTS (
            SELECT 1 FROM prompt_usages pu
            WHERE pu.prompt_id = p.id AND pu.user_id = $1
        ))              AS user_has_used,
        COALESCE(p.author_id = $1, FALSE) AS is_owner,
        COALESCE((EXISTS (
            SELECT 1 FROM prompt_reports pr
            WHERE pr.prompt_id = p.id AND pr.reporter_id = $1
              AND pr.status = 'pendente'
        )), FALSE)      AS user_has_reported
    FROM prompts p
    LEFT JOIN prompt_categories pc ON p.category_id = pc.id
    LEFT JOIN prompt_favorites  pf ON p.id = pf.prompt_id AND pf.user_id = $1
    WHERE p.is_active = TRUE AND p.publication_status = 'publico'
"""


@router.get("/categories", response_model=list[PromptCategoryResponse])
async def list_categories(
    _: dict = Depends(require_any_permission(
        "prompts.library.view",
        "prompts.my.view",
        "admin.prompts.manage",
        "admin.prompt_curation.manage",
    )),
):
    rows = await database.fetch(
        """
        SELECT pc.*,
               COUNT(p.id) AS prompt_count
        FROM prompt_categories pc
        LEFT JOIN prompts p ON p.category_id = pc.id
            AND p.is_active = TRUE AND p.publication_status = 'publico'
        GROUP BY pc.id
        ORDER BY pc.sort_order
        """
    )
    return [PromptCategoryResponse.model_validate(dict(r)) for r in rows]


_SORT_MAP = {
    "recent":  "p.created_at DESC",
    "rating":  "p.rating_avg DESC, p.rating_count DESC",
    "popular": "p.usage_count DESC, p.created_at DESC",
    "uses":    "p.usage_count DESC",
}


@router.get("", response_model=list[PromptResponse])
async def list_prompts(
    category_id: UUID | None = None,
    difficulty: str | None = None,
    model_id: UUID | None = None,
    search: str | None = None,
    source: str | None = Query(None, pattern="^(oficial|comunidade)$"),
    favorites_only: bool = False,
    rating_min: float | None = Query(None, ge=1, le=5),
    sort_by: str | None = Query(None, pattern="^(recent|rating|popular|uses)$"),
    current_user: dict = Depends(require_permission("prompts.library.view")),
):
    conditions = []
    params: list = [current_user["id"]]

    if category_id:
        params.append(category_id)
        conditions.append(f"p.category_id = ${len(params)}")
    if difficulty:
        params.append(difficulty)
        conditions.append(f"p.difficulty = ${len(params)}::prompt_difficulty")
    if model_id:
        params.append(model_id)
        conditions.append(f"p.model_id = ${len(params)}")
    if search:
        params.append(f"%{search}%")
        conditions.append(f"(p.title ILIKE ${len(params)} OR p.description ILIKE ${len(params)})")
    if source:
        params.append(source)
        conditions.append(f"p.source = ${len(params)}")
    if favorites_only:
        conditions.append("pf.user_id IS NOT NULL")
    if rating_min is not None:
        params.append(rating_min)
        conditions.append(f"p.rating_avg >= ${len(params)}")

    extra = (" AND " + " AND ".join(conditions)) if conditions else ""
    order = _SORT_MAP.get(sort_by or "", "p.usage_count DESC, p.created_at DESC")
    rows = await database.fetch(
        _LIST_QUERY + extra + f" ORDER BY {order}",
        *params,
    )
    # is_owner e user_has_reported vêm direto da query como colunas booleanas
    return [_row_to_prompt(r, bool(r["is_favorite"]), bool(r["user_has_used"])) for r in rows]


# ── Admin: Review moderation ─────────────────────────────────────────────────
# NOTE: These literal-path routes MUST be registered before /{prompt_id} so
# FastAPI doesn't try to cast "admin" as UUID and return 422.

@router.get("/admin/reviews")
async def admin_list_reviews(
    search: str | None = None,
    rating_min: int | None = Query(None, ge=1, le=5),
    is_approved: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _: dict = Depends(require_any_permission("admin.prompts.manage", "admin.prompt_curation.manage")),
):
    conditions = []
    params: list = []

    if search:
        params.append(f"%{search}%")
        conditions.append(
            f"(p.title ILIKE ${len(params)} OR u.name ILIKE ${len(params)})"
        )
    if rating_min is not None:
        params.append(rating_min)
        conditions.append(f"pr.rating >= ${len(params)}")
    if is_approved is not None:
        params.append(is_approved)
        conditions.append(f"pr.is_approved = ${len(params)}")

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    total = await database.fetchval(
        f"""
        SELECT COUNT(*) FROM prompt_reviews pr
        JOIN users u ON pr.user_id = u.id
        JOIN prompts p ON pr.prompt_id = p.id
        {where}
        """,
        *params,
    )
    offset = (page - 1) * page_size
    params.extend([page_size, offset])
    rows = await database.fetch(
        f"""
        SELECT pr.id, pr.prompt_id, pr.rating, pr.comment, pr.is_approved,
               pr.used_before, pr.created_at, pr.updated_at,
               u.name AS user_name, u.organ AS user_organ,
               p.title AS prompt_title
        FROM prompt_reviews pr
        JOIN users u ON pr.user_id = u.id
        JOIN prompts p ON pr.prompt_id = p.id
        {where}
        ORDER BY pr.created_at DESC
        LIMIT ${len(params)-1} OFFSET ${len(params)}
        """,
        *params,
    )
    items = [dict(r) for r in rows]
    return {"items": items, "total": total, "page": page, "page_size": page_size,
            "pages": -(-total // page_size)}


@router.put("/reviews/{review_id}/approve")
async def admin_approve_review(
    review_id: UUID,
    _: dict = Depends(require_any_permission("admin.prompts.manage", "admin.prompt_curation.manage")),
):
    row = await database.fetchrow(
        "UPDATE prompt_reviews SET is_approved = NOT is_approved WHERE id = $1 RETURNING is_approved",
        review_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    return {"is_approved": row["is_approved"]}


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_review(
    review_id: UUID,
    _: dict = Depends(require_any_permission("admin.prompts.manage", "admin.prompt_curation.manage")),
):
    result = await database.execute(
        "DELETE FROM prompt_reviews WHERE id = $1", review_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: UUID,
    current_user: dict = Depends(require_permission("prompts.library.view")),
):
    row = await database.fetchrow(
        _LIST_QUERY + " AND p.id = $2",
        current_user["id"],
        prompt_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    return _row_to_prompt(row, bool(row["is_favorite"]), bool(row["user_has_used"]))


@router.post("/{prompt_id}/use")
async def use_prompt(
    prompt_id: UUID,
    current_user: dict = Depends(require_permission("prompts.library.view")),
):
    """Registra uso do prompt (cópia). Retorna conteúdo e incrementa contador."""
    row = await database.fetchrow(
        """
        SELECT content
        FROM prompts
        WHERE id = $1
          AND is_active = TRUE
          AND publication_status = 'publico'
        """,
        prompt_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")

    await database.execute(
        "INSERT INTO prompt_usages (prompt_id, user_id) VALUES ($1, $2)",
        prompt_id, current_user["id"],
    )
    already_reviewed = await database.fetchval(
        "SELECT 1 FROM prompt_reviews WHERE prompt_id = $1 AND user_id = $2",
        prompt_id, current_user["id"],
    )
    return {
        "content": row["content"],
        "copied": True,
        "can_review": not bool(already_reviewed),
    }


@router.post("/{prompt_id}/favorite")
async def toggle_favorite(
    prompt_id: UUID,
    current_user: dict = Depends(require_permission("prompts.library.view")),
):
    exists = await database.fetchval(
        "SELECT 1 FROM prompt_favorites WHERE user_id = $1 AND prompt_id = $2",
        current_user["id"], prompt_id,
    )
    if exists:
        await database.execute(
            "DELETE FROM prompt_favorites WHERE user_id = $1 AND prompt_id = $2",
            current_user["id"], prompt_id,
        )
        return {"is_favorite": False}
    else:
        await database.execute(
            "INSERT INTO prompt_favorites (user_id, prompt_id) VALUES ($1, $2)",
            current_user["id"], prompt_id,
        )
        return {"is_favorite": True}


# ── Reviews ──────────────────────────────────────────────────────────────────

@router.get("/{prompt_id}/reviews", response_model=list[PromptReviewResponse])
async def list_reviews(
    prompt_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: dict = Depends(require_permission("prompts.library.view")),
):
    offset = (page - 1) * page_size
    rows = await database.fetch(
        """
        SELECT pr.*,
               u.name AS user_name,
               u.organ AS user_organ
        FROM prompt_reviews pr
        JOIN users u ON pr.user_id = u.id
        WHERE pr.prompt_id = $1 AND pr.is_approved = TRUE
        ORDER BY pr.created_at DESC
        LIMIT $2 OFFSET $3
        """,
        prompt_id, page_size, offset,
    )
    return [PromptReviewResponse.model_validate(dict(r)) for r in rows]


@router.get("/{prompt_id}/my-review", response_model=PromptReviewResponse | None)
async def get_my_review(
    prompt_id: UUID,
    current_user: dict = Depends(require_permission("prompts.library.view")),
):
    row = await database.fetchrow(
        """
        SELECT pr.*,
               u.name AS user_name,
               u.organ AS user_organ
        FROM prompt_reviews pr
        JOIN users u ON pr.user_id = u.id
        WHERE pr.prompt_id = $1 AND pr.user_id = $2
        """,
        prompt_id, current_user["id"],
    )
    if row is None:
        return None
    return PromptReviewResponse.model_validate(dict(row))


@router.post(
    "/{prompt_id}/reviews",
    response_model=PromptReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_review(
    prompt_id: UUID,
    body: PromptReviewCreate,
    current_user: dict = Depends(require_permission("prompts.library.view")),
):
    row = await database.fetchrow(
        """
        INSERT INTO prompt_reviews (prompt_id, user_id, rating, comment, used_before)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (prompt_id, user_id) DO UPDATE
            SET rating      = EXCLUDED.rating,
                comment     = EXCLUDED.comment,
                used_before = EXCLUDED.used_before,
                updated_at  = NOW()
        RETURNING *
        """,
        prompt_id, current_user["id"], body.rating, body.comment, body.used_before,
    )
    user = await database.fetchrow(
        "SELECT name, organ FROM users WHERE id = $1", current_user["id"]
    )
    d = dict(row)
    d["user_name"] = user["name"] if user else None
    d["user_organ"] = user["organ"] if user else None
    return PromptReviewResponse.model_validate(d)


@router.post("/{prompt_id}/reviews/{review_id}/approve")
async def approve_review(
    prompt_id: UUID,
    review_id: UUID,
    _: dict = Depends(require_permission("admin.prompts.manage")),
):
    result = await database.execute(
        "UPDATE prompt_reviews SET is_approved = TRUE WHERE id = $1 AND prompt_id = $2",
        review_id, prompt_id,
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    return {"message": "Avaliação aprovada"}


@router.delete("/{prompt_id}/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    prompt_id: UUID,
    review_id: UUID,
    _: dict = Depends(require_permission("admin.prompts.manage")),
):
    result = await database.execute(
        "DELETE FROM prompt_reviews WHERE id = $1 AND prompt_id = $2",
        review_id, prompt_id,
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")


# ── CRUD (admin/gestor) ───────────────────────────────────────────────────────

@router.post("", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    body: PromptCreate,
    current_user: dict = Depends(require_permission("admin.prompts.manage")),
):
    row = await database.fetchrow(
        """
        INSERT INTO prompts
            (title, description, content, category_id, model_id, tags,
             difficulty, variables, author_id, source, publication_status, is_public)
        VALUES ($1,$2,$3,$4,$5,$6,$7::prompt_difficulty,$8::jsonb,$9,'oficial',
                CASE WHEN $10 THEN 'publico'::prompt_publication_status
                     ELSE 'privado'::prompt_publication_status END,
                $10)
        RETURNING *
        """,
        body.title, body.description, body.content, body.category_id, body.model_id,
        body.tags, body.difficulty, json.dumps(body.variables),
        current_user["id"], body.is_public,
    )
    return _row_to_prompt(row)


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: UUID,
    body: PromptUpdate,
    current_user: dict = Depends(require_permission("admin.prompts.manage")),
):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    type_casts = {"difficulty": "::prompt_difficulty"}
    if "is_public" in data:
        data["publication_status"] = "publico" if data["is_public"] else "privado"
        type_casts["publication_status"] = "::prompt_publication_status"
    fields, values = [], [prompt_id]
    for field, value in data.items():
        if field == "variables":
            value = json.dumps(value)
            fields.append(f"{field} = ${len(values) + 1}::jsonb")
        else:
            cast = type_casts.get(field, "")
            fields.append(f"{field} = ${len(values) + 1}{cast}")
        values.append(value)

    row = await database.fetchrow(
        f"UPDATE prompts SET {', '.join(fields)} WHERE id = $1 RETURNING *",
        *values,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    return _row_to_prompt(row)


@router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: UUID, _: dict = Depends(require_permission("admin.prompts.manage"))):
    result = await database.execute(
        "UPDATE prompts SET is_active = FALSE WHERE id = $1", prompt_id
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    return {"message": "Prompt desativado"}
