from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.core import database
from app.core.deps import require_permission
from app.models.ai_model import AIModelCreate, AIModelResponse, AIModelUpdate
from app.services.benchmarking_service import BenchmarkingService

router = APIRouter(prefix="/models", tags=["models"])


def _row_to_model(row) -> AIModelResponse:
    return AIModelResponse.model_validate(dict(row))


@router.get("", response_model=list[AIModelResponse])
async def list_models(
    category: str | None = None,
    status: str | None = None,
    search: str | None = None,
    featured: bool | None = None,
    current_user: dict = Depends(require_permission("models.catalog.view")),
):
    conditions = ["is_active = TRUE"]
    params: list = []

    if category:
        params.append(category)
        conditions.append(f"category = ${len(params)}::model_category")
    if status:
        params.append(status)
        conditions.append(f"status = ${len(params)}::model_status")
    if featured is not None:
        params.append(featured)
        conditions.append(f"is_featured = ${len(params)}")
    if search:
        params.append(f"%{search}%")
        conditions.append(
            f"(name ILIKE ${len(params)} OR description ILIKE ${len(params)})"
        )

    where = " AND ".join(conditions)
    params.append(current_user["id"])
    user_id_param = len(params)
    rows = await database.fetch(
        f"""
        SELECT
            am.*,
            COALESCE(mas.has_any_access_request, FALSE) AS user_has_any_access_request,
            COALESCE(mas.pending_count, 0) AS user_pending_requests_count,
            COALESCE(mas.approved_count, 0) AS user_approved_requests_count,
            COALESCE(mas.revocation_requested_count, 0) AS user_revocation_requested_count
        FROM modelos am
        LEFT JOIN (
            SELECT
                model_id,
                TRUE AS has_any_access_request,
                COUNT(*) FILTER (WHERE status = 'pendente') AS pending_count,
                COUNT(*) FILTER (WHERE status = 'aprovado') AS approved_count,
                COUNT(*) FILTER (WHERE status = 'revogacao_solicitada') AS revocation_requested_count
            FROM model_access_requests
            WHERE user_id = ${user_id_param}
            GROUP BY model_id
        ) mas ON mas.model_id = am.id
        WHERE {where.replace("is_active", "am.is_active")}
        ORDER BY am.sort_order, am.name
        """,
        *params,
    )
    return [_row_to_model(r) for r in rows]


@router.get("/{slug}", response_model=AIModelResponse)
async def get_model(
    slug: str,
    current_user: dict = Depends(require_permission("models.catalog.view")),
):
    row = await database.fetchrow(
        """
        SELECT
            am.*,
            COALESCE(mas.has_any_access_request, FALSE) AS user_has_any_access_request,
            COALESCE(mas.pending_count, 0) AS user_pending_requests_count,
            COALESCE(mas.approved_count, 0) AS user_approved_requests_count,
            COALESCE(mas.revocation_requested_count, 0) AS user_revocation_requested_count
        FROM modelos am
        LEFT JOIN (
            SELECT
                model_id,
                TRUE AS has_any_access_request,
                COUNT(*) FILTER (WHERE status = 'pendente') AS pending_count,
                COUNT(*) FILTER (WHERE status = 'aprovado') AS approved_count,
                COUNT(*) FILTER (WHERE status = 'revogacao_solicitada') AS revocation_requested_count
            FROM model_access_requests
            WHERE user_id = $2
            GROUP BY model_id
        ) mas ON mas.model_id = am.id
        WHERE am.slug = $1 AND am.is_active = TRUE
        """,
        slug,
        current_user["id"],
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    return _row_to_model(row)


@router.post("", response_model=AIModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    body: AIModelCreate,
    background_tasks: BackgroundTasks,
    _: dict = Depends(require_permission("admin.models.manage")),
):
    existing = await database.fetchval(
        "SELECT id FROM modelos WHERE slug = $1", body.slug
    )
    if existing:
        raise HTTPException(status_code=409, detail="Slug já cadastrado")

    row = await database.fetchrow(
        """
        INSERT INTO modelos
            (name, slug, provider, category, description, capabilities, status,
             context_window, usage_limit, tags, is_new, is_featured, sort_order,
             requires_access_approval, access_summary, access_documentation,
             default_endpoint_base, default_auth_scheme)
        VALUES ($1,$2,$3,$4::model_category,$5,$6,$7::model_status,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18)
        RETURNING *
        """,
        body.name,
        body.slug,
        body.provider,
        body.category,
        body.description,
        body.capabilities,
        body.status,
        body.context_window,
        body.usage_limit,
        body.tags,
        body.is_new,
        body.is_featured,
        body.sort_order,
        body.requires_access_approval,
        body.access_summary,
        body.access_documentation,
        body.default_endpoint_base,
        body.default_auth_scheme,
    )
    await BenchmarkingService.ensure_registered_from_model_create(row["id"])
    background_tasks.add_task(BenchmarkingService.run_model_from_registration, row["id"])
    return _row_to_model(row)


@router.put("/{model_id}", response_model=AIModelResponse)
async def update_model(
    model_id: UUID,
    body: AIModelUpdate,
    _: dict = Depends(require_permission("admin.models.manage")),
):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    fields, values = [], [model_id]
    type_casts = {"category": "::model_category", "status": "::model_status"}
    for field, value in data.items():
        cast = type_casts.get(field, "")
        fields.append(f"{field} = ${len(values) + 1}{cast}")
        values.append(value)

    row = await database.fetchrow(
        f"UPDATE modelos SET {', '.join(fields)} WHERE id = $1 RETURNING *",
        *values,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    return _row_to_model(row)


@router.delete("/{model_id}")
async def delete_model(
    model_id: UUID, _: dict = Depends(require_permission("admin.models.manage"))
):
    result = await database.execute(
        "UPDATE modelos SET is_active = FALSE WHERE id = $1", model_id
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    return {"message": "Modelo desativado"}
