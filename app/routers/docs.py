from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core import database
from app.core.deps import require_any_permission, require_permission
from app.models.doc import (
    DocArticleCreate,
    DocArticleResponse,
    DocArticleUpdate,
    DocSearchResult,
    DocSectionCreate,
    DocSectionResponse,
    DocSectionUpdate,
    DocSectionWithArticles,
)

router = APIRouter(prefix="/docs", tags=["docs"])


@router.get("/sections", response_model=list[DocSectionWithArticles])
async def get_sections(
    current_user: dict = Depends(
        require_any_permission("docs.portal.view", "admin.docs.manage")
    ),
):
    sections = await database.fetch(
        "SELECT * FROM doc_sections WHERE is_active = TRUE ORDER BY sort_order"
    )

    # Artigos: servidores veem apenas publicados
    pub_filter = (
        "" if current_user["role"] in ("admin", "gestor") else "AND da.is_published = TRUE"
    )

    result = []
    for s in sections:
        articles = await database.fetch(
            f"""
            SELECT da.*, u.name as author_name
            FROM doc_articles da
            LEFT JOIN users u ON da.author_id = u.id
            WHERE da.section_id = $1 AND da.is_active = TRUE {pub_filter}
            ORDER BY da.sort_order
            """,
            s["id"],
        )
        section_dict = dict(s)
        section_dict["articles"] = [
            DocArticleResponse.model_validate(dict(a)) for a in articles
        ]
        result.append(DocSectionWithArticles.model_validate(section_dict))
    return result


@router.get("/articles/{slug}", response_model=DocArticleResponse)
async def get_article(
    slug: str,
    current_user: dict = Depends(
        require_any_permission("docs.portal.view", "admin.docs.manage")
    ),
):
    pub_filter = (
        "" if current_user["role"] in ("admin", "gestor") else "AND da.is_published = TRUE"
    )
    row = await database.fetchrow(
        f"""
            SELECT
                da.id,
               	da.section_id,
               	da.title,
               	da.slug,
               	da.content,
               	da.reading_time,
               	da.sort_order,
               	da.author_id,
               	da.is_published,
               	da.is_active,
               	da.created_at,
               	da.updated_at,
                u.name as author_name
            FROM doc_articles da
                LEFT JOIN users u ON da.author_id = u.id
            WHERE da.slug = $1
            AND da.is_active = TRUE {pub_filter}""",
        slug,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Artigo não encontrado")
    return DocArticleResponse.model_validate(dict(row))


@router.get("/search", response_model=list[DocSearchResult])
async def search_docs(
    q: str = Query(..., min_length=2),
    current_user: dict = Depends(
        require_any_permission("docs.portal.view", "admin.docs.manage")
    ),
):
    pub_filter = (
        ""
        if current_user["role"] in ("admin", "gestor")
        else "AND a.is_published = TRUE"
    )
    rows = await database.fetch(
        f"""
        SELECT
            a.id, a.title, a.slug,
            s.title AS section_title,
            LEFT(a.content, 200) AS excerpt
        FROM doc_articles a
        JOIN doc_sections s ON a.section_id = s.id
        WHERE a.is_active = TRUE {pub_filter}
          AND to_tsvector('portuguese', a.title || ' ' || a.content)
              @@ plainto_tsquery('portuguese', $1)
        ORDER BY ts_rank(
            to_tsvector('portuguese', a.title || ' ' || a.content),
            plainto_tsquery('portuguese', $1)
        ) DESC
        LIMIT 20
        """,
        q,
    )
    return [DocSearchResult.model_validate(dict(r)) for r in rows]


# ── Sections CRUD (admin/gestor) ─────────────────────────────────────────────


@router.post(
    "/sections", response_model=DocSectionResponse, status_code=status.HTTP_201_CREATED
)
async def create_section(
    body: DocSectionCreate, _: dict = Depends(require_permission("admin.docs.manage"))
):
    row = await database.fetchrow(
        "INSERT INTO doc_sections (title, slug, sort_order, parent_id) VALUES ($1,$2,$3,$4) RETURNING *",
        body.title,
        body.slug,
        body.sort_order,
        body.parent_id,
    )
    return DocSectionResponse.model_validate(dict(row))


@router.put("/sections/{section_id}", response_model=DocSectionResponse)
async def update_section(
    section_id: UUID,
    body: DocSectionUpdate,
    _: dict = Depends(require_permission("admin.docs.manage")),
):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    fields, values = [], [section_id]
    for field, value in data.items():
        fields.append(f"{field} = ${len(values) + 1}")
        values.append(value)
    row = await database.fetchrow(
        f"UPDATE doc_sections SET {', '.join(fields)} WHERE id = $1 RETURNING *",
        *values,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Seção não encontrada")
    return DocSectionResponse.model_validate(dict(row))


@router.delete("/sections/{section_id}")
async def delete_section(
    section_id: UUID, _: dict = Depends(require_permission("admin.docs.manage"))
):
    result = await database.execute(
        "UPDATE doc_sections SET is_active = FALSE WHERE id = $1", section_id
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Seção não encontrada")
    return {"message": "Seção desativada"}


# ── Articles CRUD (admin/gestor) ─────────────────────────────────────────────


@router.post(
    "/articles", response_model=DocArticleResponse, status_code=status.HTTP_201_CREATED
)
async def create_article(
    body: DocArticleCreate,
    current_user: dict = Depends(require_permission("admin.docs.manage")),
):
    row = await database.fetchrow(
        """
        INSERT INTO doc_articles
            (section_id, title, slug, content, reading_time, sort_order, author_id, is_published)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
        RETURNING *
        """,
        body.section_id,
        body.title,
        body.slug,
        body.content,
        body.reading_time,
        body.sort_order,
        current_user["id"],
        body.is_published,
    )
    res = dict(row)
    res["author_name"] = current_user.get("name")
    return DocArticleResponse.model_validate(res)


@router.put("/articles/{article_id}", response_model=DocArticleResponse)
async def update_article(
    article_id: UUID,
    body: DocArticleUpdate,
    _: dict = Depends(require_permission("admin.docs.manage")),
):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    fields, values = [], [article_id]
    for field, value in data.items():
        fields.append(f"{field} = ${len(values) + 1}")
        values.append(value)
    row = await database.fetchrow(
        f"""
        WITH updated AS (
            UPDATE doc_articles SET {', '.join(fields)} WHERE id = $1 RETURNING *
        )
        SELECT u.*, usr.name as author_name
        FROM updated u
        LEFT JOIN users usr ON u.author_id = usr.id
        """,
        *values,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Artigo não encontrado")
    return DocArticleResponse.model_validate(dict(row))


@router.put("/articles/{article_id}/publish", response_model=DocArticleResponse)
async def toggle_publish(
    article_id: UUID, _: dict = Depends(require_permission("admin.docs.manage"))
):
    row = await database.fetchrow(
        """
        WITH updated AS (
            UPDATE doc_articles SET is_published = NOT is_published WHERE id = $1 RETURNING *
        )
        SELECT u.*, usr.name as author_name
        FROM updated u
        LEFT JOIN users usr ON u.author_id = usr.id
        """,
        article_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Artigo não encontrado")
    return DocArticleResponse.model_validate(dict(row))


@router.delete("/articles/{article_id}")
async def delete_article(
    article_id: UUID, _: dict = Depends(require_permission("admin.docs.manage"))
):
    result = await database.execute(
        "UPDATE doc_articles SET is_active = FALSE WHERE id = $1", article_id
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Artigo não encontrado")
    return {"message": "Artigo desativado"}
