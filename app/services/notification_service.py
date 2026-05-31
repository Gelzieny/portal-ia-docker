from datetime import datetime
from uuid import UUID

from app.core import database


async def create_notification(
    *,
    type: str = "info",
    title: str,
    message: str,
    link: str | None = None,
    is_global: bool = True,
    expires_at: datetime | None = None,
    target_user_ids: list[UUID | str] | None = None,
):
    targets = list(dict.fromkeys(target_user_ids or []))
    async with database.get_connection() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO notifications (type, title, message, link, is_global, expires_at)
                VALUES ($1::notification_type, $2, $3, $4, $5, $6)
                RETURNING *
                """,
                type,
                title,
                message,
                link,
                is_global,
                expires_at,
            )
            if targets:
                await conn.executemany(
                    """
                    INSERT INTO notification_targets (notification_id, user_id)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                    """,
                    [(row["id"], user_id) for user_id in targets],
                )
            return row
