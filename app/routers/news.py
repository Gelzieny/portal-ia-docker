from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core import database
from app.core.deps import require_any_permission, require_permission
from app.models.news import NewsCreate, NewsResponse, NewsUpdate

router = APIRouter(prefix="/news", tags=["news"])


def _row_to_news(row) -> NewsResponse:
    return NewsResponse.model_validate(dict(row))


# ── Public endpoints ──────────────────────────────────────────────────────────

@router.get("", response_model=list[NewsResponse])
async def list_news(
    limit: int = 10,
    search: str | None = None,
    category: str | None = None,
    _: dict = Depends(require_any_permission("news.portal.view", "admin.news.manage")),
):
    filters = ["is_published = TRUE"]
    values: list = []

    if category:
        values.append(category)
        filters.append(f"category = ${len(values)}::news_category")

    if search:
        values.append(f"%{search}%")
        filters.append(f"(title ILIKE ${len(values)} OR summary ILIKE ${len(values)})")

    where = " AND ".join(filters)
    values.append(limit)

    rows = await database.fetch(
        f"""
        SELECT * FROM news
        WHERE {where}
        ORDER BY published_at DESC NULLS LAST, created_at DESC
        LIMIT ${len(values)}
        """,
        *values,
    )
    return [_row_to_news(r) for r in rows]


@router.get("/{news_id}", response_model=NewsResponse)
async def get_news(
    news_id: UUID,
    _: dict = Depends(require_any_permission("news.portal.view", "admin.news.manage")),
):
    row = await database.fetchrow("SELECT * FROM news WHERE id = $1", news_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Notícia não encontrada")
    return _row_to_news(row)


# ── Admin CRUD ────────────────────────────────────────────────────────────────

@router.get("/admin/all", response_model=list[NewsResponse])
async def admin_list_news(_: dict = Depends(require_permission("admin.news.manage"))):
    rows = await database.fetch(
        "SELECT * FROM news ORDER BY created_at DESC"
    )
    return [_row_to_news(r) for r in rows]


@router.post("", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
async def create_news(
    body: NewsCreate,
    _: dict = Depends(require_permission("admin.news.manage")),
):
    from datetime import datetime, timezone
    published_at = body.published_at
    if body.is_published and published_at is None:
        published_at = datetime.now(timezone.utc)

    row = await database.fetchrow(
        """
        INSERT INTO news (category, title, summary, content, link, reading_time, is_published, published_at)
        VALUES ($1::news_category, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
        """,
        body.category, body.title, body.summary, body.content,
        body.link, body.reading_time, body.is_published, published_at,
    )
    return _row_to_news(row)


@router.put("/{news_id}", response_model=NewsResponse)
async def update_news(
    news_id: UUID,
    body: NewsUpdate,
    _: dict = Depends(require_permission("admin.news.manage")),
):
    from datetime import datetime, timezone

    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    # Auto-set published_at when publishing for the first time
    if data.get("is_published") is True and "published_at" not in data:
        existing = await database.fetchrow(
            "SELECT published_at FROM news WHERE id = $1", news_id
        )
        if existing and existing["published_at"] is None:
            data["published_at"] = datetime.now(timezone.utc)

    data["updated_at"] = datetime.now(timezone.utc)

    fields, values = [], [news_id]
    for field, value in data.items():
        if field == "category":
            fields.append(f"{field} = ${len(values) + 1}::news_category")
        else:
            fields.append(f"{field} = ${len(values) + 1}")
        values.append(value)

    row = await database.fetchrow(
        f"UPDATE news SET {', '.join(fields)} WHERE id = $1 RETURNING *",
        *values,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Notícia não encontrada")
    return _row_to_news(row)


@router.delete("/{news_id}")
async def delete_news(
    news_id: UUID,
    _: dict = Depends(require_permission("admin.news.manage")),
):
    result = await database.execute("DELETE FROM news WHERE id = $1", news_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Notícia não encontrada")
    return {"message": "Notícia removida"}
