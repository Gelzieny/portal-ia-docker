from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core import database
from app.core.deps import get_current_user, require_permission
from app.models.notification import NotificationCreate, NotificationResponse, NotificationUpdate
from app.services.notification_service import create_notification as persist_notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _row_to_notif(row, is_read: bool = False) -> NotificationResponse:
    d = dict(row)
    d["is_read"] = is_read
    d["target_user_ids"] = d.get("target_user_ids") or []
    return NotificationResponse.model_validate(d)


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(current_user: dict = Depends(get_current_user)):
    rows = await database.fetch(
        """
        SELECT
            n.*,
            (nr.user_id IS NOT NULL) AS is_read
        FROM notifications n
        LEFT JOIN notification_targets nt
            ON n.id = nt.notification_id AND nt.user_id = $1
        LEFT JOIN notification_reads nr
            ON n.id = nr.notification_id AND nr.user_id = $1
        WHERE (n.is_global = TRUE OR nt.user_id IS NOT NULL)
          AND (n.expires_at IS NULL OR n.expires_at > NOW())
        ORDER BY n.created_at DESC
        """,
        current_user["id"],
    )
    return [_row_to_notif(r, bool(r["is_read"])) for r in rows]


@router.get("/unread-count")
async def unread_count(current_user: dict = Depends(get_current_user)):
    count = await database.fetchval(
        """
        SELECT COUNT(*)
        FROM notifications n
        LEFT JOIN notification_targets nt
            ON n.id = nt.notification_id AND nt.user_id = $1
        LEFT JOIN notification_reads nr
            ON n.id = nr.notification_id AND nr.user_id = $1
        WHERE (n.is_global = TRUE OR nt.user_id IS NOT NULL)
          AND (n.expires_at IS NULL OR n.expires_at > NOW())
          AND nr.user_id IS NULL
        """,
        current_user["id"],
    )
    return {"count": count}


@router.post("/{notification_id}/read")
async def mark_read(notification_id: UUID, current_user: dict = Depends(get_current_user)):
    await database.execute(
        "INSERT INTO notification_reads (user_id, notification_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
        current_user["id"], notification_id,
    )
    return {"message": "Notificação marcada como lida"}


@router.post("/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    await database.execute(
        """
        INSERT INTO notification_reads (user_id, notification_id)
        SELECT $1, n.id
        FROM notifications n
        LEFT JOIN notification_targets nt
            ON n.id = nt.notification_id AND nt.user_id = $1
        WHERE (n.is_global = TRUE OR nt.user_id IS NOT NULL)
          AND (n.expires_at IS NULL OR n.expires_at > NOW())
        ON CONFLICT DO NOTHING
        """,
        current_user["id"],
    )
    return {"message": "Todas as notificações marcadas como lidas"}


# ── Admin CRUD ────────────────────────────────────────────────────────────────

@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    body: NotificationCreate,
    _: dict = Depends(require_permission("admin.notifications.manage")),
):
    row = await persist_notification(
        type=body.type,
        title=body.title,
        message=body.message,
        link=body.link,
        is_global=body.is_global,
        expires_at=body.expires_at,
        target_user_ids=body.target_user_ids,
    )
    data = dict(row)
    data["target_user_ids"] = body.target_user_ids
    return _row_to_notif(data)


@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: UUID,
    body: NotificationUpdate,
    _: dict = Depends(require_permission("admin.notifications.manage")),
):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    fields, values = [], [notification_id]
    for field, value in data.items():
        fields.append(f"{field} = ${len(values) + 1}")
        values.append(value)
    row = await database.fetchrow(
        f"UPDATE notifications SET {', '.join(fields)} WHERE id = $1 RETURNING *", *values
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    return _row_to_notif(row)


@router.delete("/{notification_id}")
async def delete_notification(notification_id: UUID, _: dict = Depends(require_permission("admin.notifications.manage"))):
    result = await database.execute("DELETE FROM notifications WHERE id = $1", notification_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    return {"message": "Notificação removida"}
