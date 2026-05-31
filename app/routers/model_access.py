import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.core import database
from app.core.deps import require_permission
from app.core.security import decrypt_model_access_secret, encrypt_model_access_secret
from app.models.model_access import (
    ModelAccessCountsResponse,
    ModelAccessCredentialsResponse,
    ModelAccessCredentialsUpdate,
    ModelAccessDecision,
    ModelAccessRequestCreate,
    ModelAccessRequestResponse,
    ModelAccessRevocationDecision,
    ModelAccessRevocationRequest,
    ModelAccessRevoke,
    ModelAccessSecretRevealResponse,
    normalize_application_name,
)
from app.models.pagination import PaginatedResponse
from app.services.audit_service import log_audit
from app.services.notification_service import create_notification

router = APIRouter(prefix="/model-access", tags=["model-access"])


async def _notify_model_access_user(
    *,
    user_id: UUID,
    title: str,
    message: str,
    link: str,
    type: str = "info",
) -> None:
    await create_notification(
        type=type,
        title=title,
        message=message,
        link=link,
        is_global=False,
        target_user_ids=[user_id],
    )


def _model_display_name(row) -> str:
    return dict(row).get("model_name") or "modelo solicitado"


def _mask_secret(value: str) -> str:
    if len(value) <= 4:
        return "•" * len(value)
    return f"{value[:2]}{'•' * max(len(value) - 4, 4)}{value[-2:]}"


def _mask_key(value: str) -> str:
    if len(value) <= 6:
        return value
    return f"{value[:4]}...{value[-2:]}"


def _coerce_json_object(value) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


async def _log_audit(
    *,
    user_id: UUID,
    action: str,
    entity: str,
    entity_id: UUID,
    metadata: dict | None = None,
) -> None:
    await database.execute(
        """
        INSERT INTO audit_logs (user_id, action, entity, entity_id, metadata)
        VALUES ($1, $2, $3, $4, $5::jsonb)
        """,
        user_id,
        action,
        entity,
        entity_id,
        json.dumps(metadata or {}),
    )


def _set_no_store_header(response: Response) -> None:
    response.headers["Cache-Control"] = "private, no-store"


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


async def _upsert_credentials(
    *,
    request_id: UUID,
    endpoint_base: str,
    access_key: str,
    access_secret: str,
    public_headers: dict[str, str],
    usage_notes: str | None,
    actor_user_id: UUID,
) -> None:
    await database.execute(
        """
        INSERT INTO model_access_credentials (
            request_id, endpoint_base, access_key_encrypted, access_secret_encrypted,
            public_headers, usage_notes, is_active, created_by, updated_by
        )
        VALUES ($1, $2, $3, $4, $5::jsonb, $6, TRUE, $7, $7)
        ON CONFLICT (request_id) DO UPDATE SET
            endpoint_base = EXCLUDED.endpoint_base,
            access_key_encrypted = EXCLUDED.access_key_encrypted,
            access_secret_encrypted = EXCLUDED.access_secret_encrypted,
            public_headers = EXCLUDED.public_headers,
            usage_notes = EXCLUDED.usage_notes,
            is_active = TRUE,
            updated_by = EXCLUDED.updated_by,
            updated_at = NOW()
        """,
        request_id,
        endpoint_base.strip(),
        encrypt_model_access_secret(access_key.strip()),
        encrypt_model_access_secret(access_secret.strip()),
        json.dumps(public_headers),
        _normalize_optional_text(usage_notes) or "",
        actor_user_id,
    )


def _resolve_existing_credential_values(row) -> tuple[str | None, str | None]:
    if not row or not row.get("credential_id"):
        return None, None
    return (
        decrypt_model_access_secret(row["access_key_encrypted"]),
        decrypt_model_access_secret(row["access_secret_encrypted"]),
    )


async def _get_request_row(
    request_id: UUID, *, include_inactive_credentials: bool = False
):
    credentials_join = (
        "LEFT JOIN model_access_credentials mac ON mac.request_id = mar.id"
        if include_inactive_credentials
        else "LEFT JOIN model_access_credentials mac ON mac.request_id = mar.id AND mac.is_active = TRUE"
    )
    return await database.fetchrow(
        f"""
        SELECT
            mar.*,
            am.name AS model_name,
            am.slug AS model_slug,
            am.default_endpoint_base,
            u.name AS user_name,
            u.organ AS user_organ,
            mac.id AS credential_id,
            mac.endpoint_base,
            mac.access_key_encrypted,
            mac.access_secret_encrypted,
            COALESCE(mac.public_headers, '{{}}'::jsonb) AS public_headers,
            mac.usage_notes,
            COALESCE(mac.is_active, FALSE) AS credential_is_active
        FROM model_access_requests mar
        INNER JOIN modelos am ON am.id = mar.model_id
        INNER JOIN users u ON u.id = mar.user_id
        {credentials_join}
        WHERE mar.id = $1
        """,
        request_id,
    )


def _build_request_response(row) -> ModelAccessRequestResponse:
    data = dict(row)
    access_key = None
    access_secret_masked = None
    if data.get("credential_id") and data.get("credential_is_active"):
        decrypted_key = decrypt_model_access_secret(data["access_key_encrypted"])
        decrypted_secret = decrypt_model_access_secret(data["access_secret_encrypted"])
        access_key = _mask_key(decrypted_key)
        access_secret_masked = _mask_secret(decrypted_secret)

    return ModelAccessRequestResponse(
        id=data["id"],
        model_id=data["model_id"],
        user_id=data["user_id"],
        application_name=data["application_name"],
        status=data["status"],
        justification=data["justification"],
        intended_use=data.get("intended_use"),
        request_context=_coerce_json_object(data.get("request_context")),
        review_notes=data.get("review_notes"),
        reviewed_by=data.get("reviewed_by"),
        reviewed_at=data.get("reviewed_at"),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        model_name=data.get("model_name"),
        model_slug=data.get("model_slug"),
        user_name=data.get("user_name"),
        user_organ=data.get("user_organ"),
        has_credentials=bool(
            data.get("credential_id") and data.get("credential_is_active")
        ),
        endpoint_base=data.get("endpoint_base") or data.get("default_endpoint_base"),
        access_key=access_key,
        access_secret_masked=access_secret_masked,
        public_headers=_coerce_json_object(data.get("public_headers")),
        usage_notes=data.get("usage_notes"),
    )


async def _ensure_active_unique(
    user_id: UUID,
    model_id: UUID,
    application_name: str,
    *,
    exclude_request_id: UUID | None = None,
):
    params = [user_id, model_id, application_name.lower()]
    extra = ""
    if exclude_request_id is not None:
        params.append(exclude_request_id)
        extra = f"AND id <> ${len(params)}"
    exists = await database.fetchval(
        f"""
        SELECT id
        FROM model_access_requests
        WHERE user_id = $1
          AND model_id = $2
          AND LOWER(BTRIM(application_name)) = $3
          AND status IN ('pendente', 'aprovado', 'revogacao_solicitada')
          {extra}
        LIMIT 1
        """,
        *params,
    )
    if exists:
        raise HTTPException(
            status_code=409,
            detail="Já existe solicitação ativa para esta aplicação neste modelo",
        )


async def _ensure_model_requires_request(model_id: UUID):
    model = await database.fetchrow(
        """
        SELECT id, requires_access_approval, is_active
        FROM modelos
        WHERE id = $1
        """,
        model_id,
    )
    if model is None or not model["is_active"]:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    if not model["requires_access_approval"]:
        raise HTTPException(
            status_code=400, detail="Este modelo não exige solicitação de acesso"
        )
    return model


@router.post(
    "/requests",
    response_model=ModelAccessRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_request(
    body: ModelAccessRequestCreate,
    current_user: dict = Depends(require_permission("models.catalog.view")),
):
    await _ensure_model_requires_request(body.model_id)
    application_name = normalize_application_name(body.application_name)
    await _ensure_active_unique(current_user["id"], body.model_id, application_name)

    row = await database.fetchrow(
        """
        INSERT INTO model_access_requests (
            model_id, user_id, application_name, justification, intended_use
        )
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        body.model_id,
        current_user["id"],
        application_name,
        body.justification,
        body.intended_use,
    )
    request_row = await _get_request_row(row["id"])
    await _log_audit(
        user_id=current_user["id"],
        action="CREATE",
        entity="model_access_request",
        entity_id=row["id"],
        metadata={
            "model_id": str(body.model_id),
            "target_user_id": str(current_user["id"]),
        },
    )
    return _build_request_response(request_row)


@router.get(
    "/my-requests", response_model=PaginatedResponse[ModelAccessRequestResponse]
)
async def list_my_requests(
    status_filter: str | None = Query(None, alias="status"),
    model_id: UUID | None = None,
    application_name: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_permission("models.my_access.view")),
):
    conditions = ["mar.user_id = $1"]
    params: list = [current_user["id"]]
    if status_filter:
        params.append(status_filter)
        conditions.append(f"mar.status = ${len(params)}::model_access_request_status")
    if model_id:
        params.append(model_id)
        conditions.append(f"mar.model_id = ${len(params)}")
    if application_name:
        params.append(f"%{application_name.strip()}%")
        conditions.append(f"mar.application_name ILIKE ${len(params)}")

    where = " AND ".join(conditions)
    total = await database.fetchval(
        f"SELECT COUNT(*) FROM model_access_requests mar WHERE {where}",
        *params,
    )
    offset = (page - 1) * page_size
    params.extend([page_size, offset])
    rows = await database.fetch(
        f"""
        SELECT mar.id
        FROM model_access_requests mar
        WHERE {where}
        ORDER BY mar.created_at DESC
        LIMIT ${len(params) - 1} OFFSET ${len(params)}
        """,
        *params,
    )
    items = []
    for row in rows:
        request_row = await _get_request_row(row["id"])
        items.append(_build_request_response(request_row))
    return PaginatedResponse.build(items, total, page, page_size)


@router.get("/my-requests/{request_id}", response_model=ModelAccessRequestResponse)
async def get_my_request(
    request_id: UUID,
    current_user: dict = Depends(require_permission("models.my_access.view")),
):
    row = await _get_request_row(request_id)
    if row is None or row["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    return _build_request_response(row)


@router.get(
    "/my-requests/{request_id}/credentials",
    response_model=ModelAccessCredentialsResponse,
)
async def get_my_credentials(
    request_id: UUID,
    response: Response,
    current_user: dict = Depends(require_permission("models.my_access.view")),
):
    row = await _get_request_row(request_id)
    if row is None or row["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    if (
        row["status"] not in ("aprovado", "revogacao_solicitada")
        or not row["credential_id"]
        or not row["credential_is_active"]
    ):
        raise HTTPException(status_code=404, detail="Credenciais não disponíveis")
    _set_no_store_header(response)
    decrypted_key = decrypt_model_access_secret(row["access_key_encrypted"])
    decrypted_secret = decrypt_model_access_secret(row["access_secret_encrypted"])
    return ModelAccessCredentialsResponse(
        endpoint_base=row["endpoint_base"] or row["default_endpoint_base"],
        access_key=decrypted_key,
        access_secret_masked=_mask_secret(decrypted_secret),
        public_headers=_coerce_json_object(row.get("public_headers")),
        usage_notes=row.get("usage_notes"),
    )


@router.post(
    "/my-requests/{request_id}/credentials/reveal-secret",
    response_model=ModelAccessSecretRevealResponse,
)
async def reveal_my_secret(
    request_id: UUID,
    request: Request,
    response: Response,
    current_user: dict = Depends(require_permission("models.my_access.view")),
):
    row = await _get_request_row(request_id)
    if row is None or row["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    if (
        row["status"] not in ("aprovado", "revogacao_solicitada")
        or not row["credential_id"]
        or not row["credential_is_active"]
    ):
        raise HTTPException(status_code=404, detail="Credenciais não disponíveis")
    _set_no_store_header(response)
    await log_audit(
        user_id=current_user["id"],
        action="MODEL_ACCESS_SECRET_REVEAL",
        entity="model_access_request",
        entity_id=request_id,
        metadata={
            "model_id": str(row["model_id"]),
            "target_user_id": str(current_user["id"]),
        },
        request=request,
    )
    return ModelAccessSecretRevealResponse(
        access_secret=decrypt_model_access_secret(row["access_secret_encrypted"])
    )


@router.post("/my-requests/{request_id}/cancel")
async def cancel_my_request(
    request_id: UUID,
    current_user: dict = Depends(require_permission("models.my_access.view")),
):
    row = await database.fetchrow(
        """
        UPDATE model_access_requests
        SET status = 'cancelado', updated_at = NOW()
        WHERE id = $1 AND user_id = $2 AND status = 'pendente'
        RETURNING id
        """,
        request_id,
        current_user["id"],
    )
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Solicitação não encontrada ou não pode ser cancelada",
        )
    await _log_audit(
        user_id=current_user["id"],
        action="CANCEL",
        entity="model_access_request",
        entity_id=request_id,
    )
    return {"cancelled": True}


@router.post("/my-requests/{request_id}/request-revocation")
async def request_revocation(
    request_id: UUID,
    body: ModelAccessRevocationRequest,
    current_user: dict = Depends(require_permission("models.my_access.view")),
):
    row = await database.fetchrow(
        """
        UPDATE model_access_requests
        SET status = 'revogacao_solicitada',
            review_notes = COALESCE($3, review_notes),
            updated_at = NOW()
        WHERE id = $1 AND user_id = $2 AND status = 'aprovado'
        RETURNING id, model_id
        """,
        request_id,
        current_user["id"],
        body.review_notes,
    )
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Solicitação não encontrada ou não pode pedir revogação",
        )
    await _log_audit(
        user_id=current_user["id"],
        action="REQUEST_REVOKE",
        entity="model_access_request",
        entity_id=request_id,
        metadata={
            "model_id": str(row["model_id"]),
            "target_user_id": str(current_user["id"]),
        },
    )
    return {"requested": True}


@router.get(
    "/admin/requests", response_model=PaginatedResponse[ModelAccessRequestResponse]
)
async def admin_list_requests(
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
    model_id: UUID | None = None,
    user_id: UUID | None = None,
    application_name: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: dict = Depends(require_permission("admin.model_access.manage")),
):
    conditions = ["TRUE"]
    params: list = []
    if status_filter:
        params.append(status_filter)
        conditions.append(f"mar.status = ${len(params)}::model_access_request_status")
    if model_id:
        params.append(model_id)
        conditions.append(f"mar.model_id = ${len(params)}")
    if user_id:
        params.append(user_id)
        conditions.append(f"mar.user_id = ${len(params)}")
    if application_name:
        params.append(f"%{application_name.strip()}%")
        conditions.append(f"mar.application_name ILIKE ${len(params)}")
    if search:
        params.append(f"%{search}%")
        conditions.append(
            f"(u.name ILIKE ${len(params)} OR u.organ ILIKE ${len(params)} OR am.name ILIKE ${len(params)} OR mar.application_name ILIKE ${len(params)})"
        )
    where = " AND ".join(conditions)
    total = await database.fetchval(
        f"""
        SELECT COUNT(*)
        FROM model_access_requests mar
        INNER JOIN modelos am ON am.id = mar.model_id
        INNER JOIN users u ON u.id = mar.user_id
        WHERE {where}
        """,
        *params,
    )
    offset = (page - 1) * page_size
    params.extend([page_size, offset])
    rows = await database.fetch(
        f"""
        SELECT mar.id
        FROM model_access_requests mar
        INNER JOIN modelos am ON am.id = mar.model_id
        INNER JOIN users u ON u.id = mar.user_id
        WHERE {where}
        ORDER BY
            CASE mar.status
                WHEN 'pendente' THEN 0
                WHEN 'revogacao_solicitada' THEN 1
                ELSE 2
            END,
            mar.created_at DESC
        LIMIT ${len(params) - 1} OFFSET ${len(params)}
        """,
        *params,
    )
    items = []
    for row in rows:
        request_row = await _get_request_row(
            row["id"], include_inactive_credentials=True
        )
        items.append(_build_request_response(request_row))
    return PaginatedResponse.build(items, total, page, page_size)


@router.get("/admin/requests/count", response_model=ModelAccessCountsResponse)
async def admin_request_counts(
    _: dict = Depends(require_permission("admin.model_access.manage")),
):
    row = await database.fetchrow(
        """
        SELECT
            COUNT(*) FILTER (WHERE status = 'pendente') AS pendentes,
            COUNT(*) FILTER (WHERE status = 'revogacao_solicitada') AS revogacao_solicitada,
            COUNT(*) FILTER (WHERE status = 'aprovado') AS aprovados,
            COUNT(*) FILTER (WHERE status = 'negado') AS negados,
            COUNT(*) FILTER (WHERE status = 'revogado') AS revogados,
            COUNT(*) AS total
        FROM model_access_requests
        """
    )
    return ModelAccessCountsResponse.model_validate(dict(row))


@router.get("/admin/requests/{request_id}", response_model=ModelAccessRequestResponse)
async def admin_get_request(
    request_id: UUID,
    _: dict = Depends(require_permission("admin.model_access.manage")),
):
    row = await _get_request_row(request_id, include_inactive_credentials=True)
    if row is None:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    return _build_request_response(row)


@router.put(
    "/admin/requests/{request_id}/decide", response_model=ModelAccessRequestResponse
)
async def admin_decide_request(
    request_id: UUID,
    body: ModelAccessDecision,
    current_user: dict = Depends(require_permission("admin.model_access.manage")),
):
    row = await _get_request_row(request_id, include_inactive_credentials=True)
    if row is None or row["status"] != "pendente":
        raise HTTPException(
            status_code=404, detail="Solicitação não encontrada na fila"
        )

    if body.action == "aprovar":
        endpoint_base = _normalize_optional_text(body.endpoint_base)
        access_key = _normalize_optional_text(body.access_key)
        access_secret = _normalize_optional_text(body.access_secret)
        if not endpoint_base or not access_key or not access_secret:
            raise HTTPException(
                status_code=400,
                detail="Endpoint, access key e access secret são obrigatórios",
            )
        await _upsert_credentials(
            request_id=request_id,
            endpoint_base=endpoint_base,
            access_key=access_key,
            access_secret=access_secret,
            public_headers=body.public_headers or {},
            usage_notes=body.usage_notes,
            actor_user_id=current_user["id"],
        )
        await database.execute(
            """
            UPDATE model_access_requests
            SET status = 'aprovado',
                review_notes = $2,
                reviewed_by = $3,
                reviewed_at = NOW(),
                updated_at = NOW()
            WHERE id = $1
            """,
            request_id,
            body.review_notes,
            current_user["id"],
        )
        await _log_audit(
            user_id=current_user["id"],
            action="APPROVE",
            entity="model_access_request",
            entity_id=request_id,
            metadata={
                "model_id": str(row["model_id"]),
                "target_user_id": str(row["user_id"]),
            },
        )
        await _notify_model_access_user(
            user_id=row["user_id"],
            type="success",
            title="Acesso a modelo aprovado",
            message=f"Sua solicitação para {_model_display_name(row)} foi aprovada.",
            link=f"/meus-acessos-modelos?request={request_id}",
        )
    else:
        if not body.review_notes:
            raise HTTPException(
                status_code=400, detail="Motivo da negação é obrigatório"
            )
        await database.execute(
            """
            UPDATE model_access_requests
            SET status = 'negado',
                review_notes = $2,
                reviewed_by = $3,
                reviewed_at = NOW(),
                updated_at = NOW()
            WHERE id = $1
            """,
            request_id,
            body.review_notes,
            current_user["id"],
        )
        await _log_audit(
            user_id=current_user["id"],
            action="DENY",
            entity="model_access_request",
            entity_id=request_id,
            metadata={
                "model_id": str(row["model_id"]),
                "target_user_id": str(row["user_id"]),
            },
        )
        await _notify_model_access_user(
            user_id=row["user_id"],
            type="warning",
            title="Acesso a modelo negado",
            message=f"Sua solicitação para {_model_display_name(row)} foi negada. Consulte o parecer da curadoria.",
            link=f"/meus-acessos-modelos?request={request_id}",
        )

    updated = await _get_request_row(request_id, include_inactive_credentials=True)
    return _build_request_response(updated)


@router.put(
    "/admin/requests/{request_id}/revoke", response_model=ModelAccessRequestResponse
)
async def admin_revoke_request(
    request_id: UUID,
    body: ModelAccessRevoke,
    current_user: dict = Depends(require_permission("admin.model_access.manage")),
):
    row = await _get_request_row(request_id, include_inactive_credentials=True)
    if row is None or row["status"] != "aprovado":
        raise HTTPException(
            status_code=404, detail="Solicitação não encontrada ou não está aprovada"
        )
    await database.execute(
        "UPDATE model_access_credentials SET is_active = FALSE, updated_by = $2, updated_at = NOW() WHERE request_id = $1",
        request_id,
        current_user["id"],
    )
    await database.execute(
        """
        UPDATE model_access_requests
        SET status = 'revogado',
            review_notes = COALESCE($2, review_notes),
            reviewed_by = $3,
            reviewed_at = NOW(),
            updated_at = NOW()
        WHERE id = $1
        """,
        request_id,
        body.review_notes,
        current_user["id"],
    )
    await _log_audit(
        user_id=current_user["id"],
        action="REVOKE",
        entity="model_access_request",
        entity_id=request_id,
        metadata={
            "model_id": str(row["model_id"]),
            "target_user_id": str(row["user_id"]),
        },
    )
    await _notify_model_access_user(
        user_id=row["user_id"],
        type="warning",
        title="Acesso a modelo revogado",
        message=f"Seu acesso a {_model_display_name(row)} foi revogado.",
        link=f"/meus-acessos-modelos?request={request_id}",
    )
    updated = await _get_request_row(request_id, include_inactive_credentials=True)
    return _build_request_response(updated)


@router.put(
    "/admin/requests/{request_id}/review-revocation",
    response_model=ModelAccessRequestResponse,
)
async def admin_review_revocation(
    request_id: UUID,
    body: ModelAccessRevocationDecision,
    current_user: dict = Depends(require_permission("admin.model_access.manage")),
):
    row = await _get_request_row(request_id, include_inactive_credentials=True)
    if row is None or row["status"] != "revogacao_solicitada":
        raise HTTPException(
            status_code=404,
            detail="Solicitação não encontrada ou não aguarda revisão de revogação",
        )

    if body.action == "confirmar":
        await database.execute(
            "UPDATE model_access_credentials SET is_active = FALSE, updated_by = $2, updated_at = NOW() WHERE request_id = $1",
            request_id,
            current_user["id"],
        )
        await database.execute(
            """
            UPDATE model_access_requests
            SET status = 'revogado',
                review_notes = COALESCE($2, review_notes),
                reviewed_by = $3,
                reviewed_at = NOW(),
                updated_at = NOW()
            WHERE id = $1
            """,
            request_id,
            body.review_notes,
            current_user["id"],
        )
        await _log_audit(
            user_id=current_user["id"],
            action="REVOKE",
            entity="model_access_request",
            entity_id=request_id,
            metadata={
                "model_id": str(row["model_id"]),
                "target_user_id": str(row["user_id"]),
            },
        )
        await _notify_model_access_user(
            user_id=row["user_id"],
            type="warning",
            title="Revogação confirmada",
            message=f"A revogação do acesso a {_model_display_name(row)} foi confirmada.",
            link=f"/meus-acessos-modelos?request={request_id}",
        )
    else:
        if not body.review_notes:
            raise HTTPException(
                status_code=400, detail="Motivo para rejeitar a revogação é obrigatório"
            )
        await database.execute(
            """
            UPDATE model_access_requests
            SET status = 'aprovado',
                review_notes = $2,
                reviewed_by = $3,
                reviewed_at = NOW(),
                updated_at = NOW()
            WHERE id = $1
            """,
            request_id,
            body.review_notes,
            current_user["id"],
        )
        await database.execute(
            """
            UPDATE model_access_credentials
            SET is_active = TRUE, updated_by = $2, updated_at = NOW()
            WHERE request_id = $1
            """,
            request_id,
            current_user["id"],
        )
        await _log_audit(
            user_id=current_user["id"],
            action="REJECT_REVOKE",
            entity="model_access_request",
            entity_id=request_id,
            metadata={
                "model_id": str(row["model_id"]),
                "target_user_id": str(row["user_id"]),
            },
        )
        await _notify_model_access_user(
            user_id=row["user_id"],
            type="success",
            title="Acesso mantido",
            message=f"Sua solicitação de revogação para {_model_display_name(row)} foi rejeitada e o acesso continua ativo.",
            link=f"/meus-acessos-modelos?request={request_id}",
        )

    updated = await _get_request_row(request_id, include_inactive_credentials=True)
    return _build_request_response(updated)


@router.put(
    "/admin/requests/{request_id}/credentials",
    response_model=ModelAccessRequestResponse,
)
async def admin_update_credentials(
    request_id: UUID,
    body: ModelAccessCredentialsUpdate,
    current_user: dict = Depends(require_permission("admin.model_access.manage")),
):
    row = await _get_request_row(request_id, include_inactive_credentials=True)
    if row is None or row["status"] not in ("aprovado", "revogacao_solicitada"):
        raise HTTPException(
            status_code=404,
            detail="Solicitação não encontrada ou sem credenciais atualizáveis",
        )
    existing_key, existing_secret = _resolve_existing_credential_values(row)
    provided_fields = body.model_fields_set

    endpoint_base = (
        _normalize_optional_text(body.endpoint_base)
        if "endpoint_base" in provided_fields
        else _normalize_optional_text(
            row["endpoint_base"] or row["default_endpoint_base"]
        )
    )
    access_key = (
        _normalize_optional_text(body.access_key)
        if "access_key" in provided_fields
        else _normalize_optional_text(existing_key)
    )
    access_secret = (
        _normalize_optional_text(body.access_secret)
        if "access_secret" in provided_fields
        else _normalize_optional_text(existing_secret)
    )
    public_headers = (
        body.public_headers
        if "public_headers" in provided_fields
        else _coerce_json_object(row.get("public_headers"))
    ) or {}
    usage_notes = (
        body.usage_notes if "usage_notes" in provided_fields else row.get("usage_notes")
    )

    if not endpoint_base or not access_key or not access_secret:
        raise HTTPException(
            status_code=400,
            detail="Endpoint, access key e access secret são obrigatórios para salvar a integração",
        )

    await _upsert_credentials(
        request_id=request_id,
        endpoint_base=endpoint_base,
        access_key=access_key,
        access_secret=access_secret,
        public_headers=public_headers,
        usage_notes=usage_notes,
        actor_user_id=current_user["id"],
    )
    await _log_audit(
        user_id=current_user["id"],
        action="UPDATE",
        entity="model_access_credential",
        entity_id=request_id,
        metadata={
            "model_id": str(row["model_id"]),
            "target_user_id": str(row["user_id"]),
        },
    )
    updated = await _get_request_row(request_id, include_inactive_credentials=True)
    return _build_request_response(updated)
