import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core import database
from app.core.deps import require_permission
from app.models.audit import AuditLogResponse
from app.models.pagination import PaginatedResponse

router = APIRouter(prefix="/audit", tags=["audit"])


def _metadata_to_details(metadata: dict) -> str | None:
    if not metadata:
        return None
    parts = []
    for key in ("target_user_id", "model_id", "prompt_id", "request_id"):
        if metadata.get(key):
            parts.append(f"{key}={metadata[key]}")
    if parts:
        return " | ".join(parts)
    return json.dumps(metadata, ensure_ascii=False)


def _coerce_metadata(value) -> dict:
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


def _row_to_response(row) -> AuditLogResponse:
    data = dict(row)
    metadata = _coerce_metadata(data.get("metadata"))
    return AuditLogResponse(
        id=data["id"],
        user_id=data.get("user_id"),
        user_name=data.get("user_name"),
        user_email=data.get("user_email"),
        action=data["action"],
        entity=data["entity"],
        entity_id=data.get("entity_id"),
        metadata=metadata,
        details=_metadata_to_details(metadata),
        ip_address=str(data["ip_address"]) if data.get("ip_address") is not None else None,
        user_agent=data.get("user_agent"),
        created_at=data["created_at"],
    )


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    search: str | None = None,
    action: str | None = None,
    entity: str | None = None,
    user_id: UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    _: dict = Depends(require_permission("admin.audit.view")),
):
    conditions = ["TRUE"]
    params: list = []

    if action:
        params.append(action)
        conditions.append(f"al.action = ${len(params)}")
    if entity:
        params.append(entity)
        conditions.append(f"al.entity = ${len(params)}")
    if user_id:
        params.append(user_id)
        conditions.append(f"al.user_id = ${len(params)}")
    if date_from:
        params.append(date_from)
        conditions.append(f"al.created_at >= ${len(params)}::timestamptz")
    if date_to:
        params.append(date_to)
        conditions.append(f"al.created_at <= ${len(params)}::timestamptz")
    if search:
        params.append(f"%{search}%")
        conditions.append(
            f"(u.name ILIKE ${len(params)} OR u.email ILIKE ${len(params)} OR al.entity ILIKE ${len(params)} OR al.action ILIKE ${len(params)})"
        )

    where = " AND ".join(conditions)
    total = await database.fetchval(
        f"""
        SELECT COUNT(*)
        FROM audit_logs al
        LEFT JOIN users u ON u.id = al.user_id
        WHERE {where}
        """,
        *params,
    )

    offset = (page - 1) * page_size
    params.extend([page_size, offset])
    rows = await database.fetch(
        f"""
        SELECT
            al.id, al.user_id, u.name AS user_name, u.email AS user_email,
            al.action, al.entity, al.entity_id, al.metadata,
            al.ip_address::text AS ip_address, al.user_agent, al.created_at
        FROM audit_logs al
        LEFT JOIN users u ON u.id = al.user_id
        WHERE {where}
        ORDER BY al.created_at DESC
        LIMIT ${len(params) - 1} OFFSET ${len(params)}
        """,
        *params,
    )
    items = [_row_to_response(row) for row in rows]
    return PaginatedResponse.build(items, total, page, page_size)


@router.get("/{audit_id}", response_model=AuditLogResponse)
async def get_audit_log(
    audit_id: UUID,
    _: dict = Depends(require_permission("admin.audit.view")),
):
    row = await database.fetchrow(
        """
        SELECT
            al.id, al.user_id, u.name AS user_name, u.email AS user_email,
            al.action, al.entity, al.entity_id, al.metadata,
            al.ip_address::text AS ip_address, al.user_agent, al.created_at
        FROM audit_logs al
        LEFT JOIN users u ON u.id = al.user_id
        WHERE al.id = $1
        """,
        audit_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Registro de auditoria não encontrado")
    return _row_to_response(row)
