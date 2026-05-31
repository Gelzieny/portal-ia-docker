from typing import Any
from uuid import UUID

from fastapi import HTTPException, status

from app.core import database
from app.models.idea import IdeaCommentCreate, IdeaReaction, IdeaRoadmapUpdate, IdeaVersionCreate, IdeaVersionUpdate, IdeaCreate, IdeaUpdate
from app.services.audit_service import log_audit
from app.services.notification_service import create_notification


def _row_to_dict(row) -> dict[str, Any]:
    return dict(row)


async def list_topics() -> list[dict[str, Any]]:
    rows = await database.fetch(
        """
        SELECT *
        FROM idea_topics
        WHERE is_active = TRUE
        ORDER BY sort_order, name
        """
    )
    return [_row_to_dict(row) for row in rows]


async def list_versions(*, include_inactive: bool = False) -> list[dict[str, Any]]:
    conditions = []
    if not include_inactive:
        conditions.append("is_active = TRUE")

    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = await database.fetch(
        f"""
        SELECT *
        FROM idea_versions
        {where_sql}
        ORDER BY sort_order, name
        """
    )
    return [_row_to_dict(row) for row in rows]


async def create_version(*, body: IdeaVersionCreate, user_id: UUID, request=None) -> dict[str, Any]:
    row = await database.fetchrow(
        """
        INSERT INTO idea_versions (name, description, forecast, sort_order, is_active, created_by)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
        """,
        body.name,
        body.description,
        body.forecast,
        body.sort_order,
        body.is_active,
        user_id,
    )
    await log_audit(
        user_id=user_id,
        action="IDEA_VERSION_CREATE",
        entity="idea_version",
        entity_id=row["id"],
        metadata={"name": body.name},
        request=request,
    )
    return _row_to_dict(row)


async def update_version(*, version_id: UUID, body: IdeaVersionUpdate, user_id: UUID, request=None) -> dict[str, Any]:
    current = await database.fetchrow("SELECT * FROM idea_versions WHERE id = $1", version_id)
    if current is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Versão não encontrada")

    data = body.model_dump(exclude_unset=True)
    if not data:
        return _row_to_dict(current)

    fields = []
    values: list[Any] = [version_id]
    for key, value in data.items():
        values.append(value)
        fields.append(f"{key} = ${len(values)}")
    values.append(user_id)

    row = await database.fetchrow(
        f"""
        UPDATE idea_versions
        SET {', '.join(fields)}, updated_at = NOW()
        WHERE id = $1
        RETURNING *
        """,
        *values[:-1],
    )
    await log_audit(
        user_id=user_id,
        action="IDEA_VERSION_UPDATE",
        entity="idea_version",
        entity_id=version_id,
        metadata={"changed_fields": sorted(data.keys())},
        request=request,
    )
    return _row_to_dict(row)


async def delete_or_deactivate_version(*, version_id: UUID, user_id: UUID, request=None) -> None:
    current = await database.fetchrow("SELECT * FROM idea_versions WHERE id = $1", version_id)
    if current is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Versão não encontrada")

    usage_count = await database.fetchval("SELECT COUNT(*) FROM ideas WHERE version_id = $1", version_id)
    if usage_count:
        await database.execute(
            "UPDATE idea_versions SET is_active = FALSE, updated_at = NOW() WHERE id = $1",
            version_id,
        )
    else:
        await database.execute("DELETE FROM idea_versions WHERE id = $1", version_id)

    await log_audit(
        user_id=user_id,
        action="IDEA_VERSION_DELETE",
        entity="idea_version",
        entity_id=version_id,
        metadata={"deactivated": bool(usage_count), "usage_count": int(usage_count or 0)},
        request=request,
    )


async def _ensure_topics_exist(topic_ids: list[UUID]) -> None:
    if len(set(topic_ids)) != len(topic_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tópicos duplicados")
    if len(topic_ids) > 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Escolha no máximo 3 tópicos")
    if not topic_ids:
        return

    rows = await database.fetch(
        "SELECT id FROM idea_topics WHERE id = ANY($1::uuid[]) AND is_active = TRUE",
        topic_ids,
    )
    existing = {row["id"] for row in rows}
    missing = [topic_id for topic_id in topic_ids if topic_id not in existing]
    if missing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tópico inválido")


async def _topics_for_ideas(idea_ids: list[UUID]) -> dict[UUID, list[dict[str, Any]]]:
    if not idea_ids:
        return {}
    rows = await database.fetch(
        """
        SELECT itl.idea_id, t.*
        FROM idea_topic_links itl
        JOIN idea_topics t ON t.id = itl.topic_id
        WHERE itl.idea_id = ANY($1::uuid[])
        ORDER BY t.sort_order, t.name
        """,
        idea_ids,
    )
    result: dict[UUID, list[dict[str, Any]]] = {idea_id: [] for idea_id in idea_ids}
    for row in rows:
        data = _row_to_dict(row)
        idea_id = data.pop("idea_id")
        result.setdefault(idea_id, []).append(data)
    return result


async def _get_idea_detail_row(idea_id: UUID, user_id: UUID) -> dict[str, Any] | None:
    return await database.fetchrow(
        """
        SELECT
          i.*,
          u.name AS author_name,
          u.organ AS author_organ,
          ivs.name AS version_name,
          ivs.forecast AS version_forecast,
          COALESCE(v.vote_count, 0)::int AS vote_count,
          COALESCE(c.comment_count, 0)::int AS comment_count,
          EXISTS (
            SELECT 1 FROM idea_votes iv
            WHERE iv.idea_id = i.id AND iv.user_id = $2
          ) AS user_has_voted
        FROM ideas i
        JOIN users u ON u.id = i.author_id
        LEFT JOIN idea_versions ivs ON ivs.id = i.version_id
        LEFT JOIN (
          SELECT idea_id, COUNT(*) AS vote_count
          FROM idea_votes
          GROUP BY idea_id
        ) v ON v.idea_id = i.id
        LEFT JOIN (
          SELECT idea_id, COUNT(*) AS comment_count
          FROM idea_comments
          WHERE moderation_status = 'publicado'
          GROUP BY idea_id
        ) c ON c.idea_id = i.id
        WHERE i.id = $1
          AND i.deleted_at IS NULL
          AND (i.author_id = $2 OR i.moderation_status = 'publicada')
        """,
        idea_id,
        user_id,
    )


def _can_author_change(row: dict[str, Any], user_id: UUID) -> bool:
    return row["author_id"] == user_id and row["moderation_status"] == "aguardando_curadoria"


async def _build_idea_detail(row, user_id: UUID) -> dict[str, Any]:
    data = _row_to_dict(row)
    topics = await _topics_for_ideas([data["id"]])
    data["topics"] = topics.get(data["id"], [])
    data.setdefault("vote_count", 0)
    data.setdefault("comment_count", 0)
    data.setdefault("user_has_voted", False)
    data["can_edit"] = _can_author_change(data, user_id)
    data["can_delete"] = _can_author_change(data, user_id)
    return data


async def get_idea_detail(idea_id: UUID, user_id: UUID) -> dict[str, Any]:
    row = await _get_idea_detail_row(idea_id, user_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ideia não encontrada")
    return await _build_idea_detail(row, user_id)


async def _ensure_public_idea(idea_id: UUID) -> None:
    row = await database.fetchrow(
        """
        SELECT id
        FROM ideas
        WHERE id = $1
          AND deleted_at IS NULL
          AND moderation_status = 'publicada'
        """,
        idea_id,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ideia não encontrada")


async def list_my_ideas(
    *,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
    moderation_status: str | None = None,
    search: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    params: list[Any] = [user_id]
    conditions = ["i.author_id = $1", "i.deleted_at IS NULL"]

    if moderation_status:
        params.append(moderation_status)
        conditions.append(f"i.moderation_status = ${len(params)}::idea_moderation_status")

    if search:
        params.append(f"%{search.strip()}%")
        conditions.append(f"(i.title ILIKE ${len(params)} OR i.description ILIKE ${len(params)})")

    where_sql = " AND ".join(conditions)
    total = await database.fetchval(f"SELECT COUNT(*) FROM ideas i WHERE {where_sql}", *params)

    params.extend([page_size, (page - 1) * page_size])
    rows = await database.fetch(
        f"""
        SELECT
          i.*,
          u.name AS author_name,
          u.organ AS author_organ,
          ivs.name AS version_name,
          ivs.forecast AS version_forecast,
          COALESCE(v.vote_count, 0)::int AS vote_count,
          COALESCE(c.comment_count, 0)::int AS comment_count,
          FALSE AS user_has_voted
        FROM ideas i
        JOIN users u ON u.id = i.author_id
        LEFT JOIN idea_versions ivs ON ivs.id = i.version_id
        LEFT JOIN (
          SELECT idea_id, COUNT(*) AS vote_count
          FROM idea_votes
          GROUP BY idea_id
        ) v ON v.idea_id = i.id
        LEFT JOIN (
          SELECT idea_id, COUNT(*) AS comment_count
          FROM idea_comments
          WHERE moderation_status = 'publicado'
          GROUP BY idea_id
        ) c ON c.idea_id = i.id
        WHERE {where_sql}
        ORDER BY i.created_at DESC
        LIMIT ${len(params) - 1} OFFSET ${len(params)}
        """,
        *params,
    )
    items = []
    topics = await _topics_for_ideas([row["id"] for row in rows])
    for row in rows:
        data = _row_to_dict(row)
        data["topics"] = topics.get(data["id"], [])
        data["can_edit"] = _can_author_change(data, user_id)
        data["can_delete"] = _can_author_change(data, user_id)
        items.append(data)
    return items, int(total or 0)


async def list_public_ideas(
    *,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    topic_id: UUID | None = None,
    status_filter: str | None = None,
    sort_by: str = "trending",
) -> tuple[list[dict[str, Any]], int]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    params: list[Any] = []
    conditions = ["i.deleted_at IS NULL", "i.moderation_status = 'publicada'"]

    if search:
        params.append(f"%{search.strip()}%")
        conditions.append(f"(i.title ILIKE ${len(params)} OR i.description ILIKE ${len(params)})")

    if topic_id:
        params.append(topic_id)
        conditions.append(
            f"EXISTS (SELECT 1 FROM idea_topic_links itl WHERE itl.idea_id = i.id AND itl.topic_id = ${len(params)})"
        )

    if status_filter:
        params.append(status_filter)
        conditions.append(f"i.idea_status = ${len(params)}::idea_status")

    where_sql = " AND ".join(conditions)
    total = await database.fetchval(f"SELECT COUNT(*) FROM ideas i WHERE {where_sql}", *params)

    params.extend([user_id, page_size, (page - 1) * page_size])
    sort_sql = {
        "latest": "i.published_at DESC NULLS LAST, i.created_at DESC",
        "most_votes": "vote_count DESC, i.published_at DESC NULLS LAST",
        "least_votes": "vote_count ASC, i.published_at DESC NULLS LAST",
        "most_comments": "comment_count DESC, i.published_at DESC NULLS LAST",
        "trending": "trending_score DESC, i.published_at DESC NULLS LAST",
    }.get(sort_by, "trending_score DESC, i.published_at DESC NULLS LAST")

    rows = await database.fetch(
        f"""
        WITH listed AS (
          SELECT
            i.*,
            u.name AS author_name,
            u.organ AS author_organ,
            ivs.name AS version_name,
            ivs.forecast AS version_forecast,
            COALESCE(v.vote_count, 0)::int AS vote_count,
            COALESCE(c.comment_count, 0)::int AS comment_count,
            (
              COALESCE(rv.recent_vote_count, 0) * 3 +
              COALESCE(rc.recent_comment_count, 0) * 2 +
              COALESCE(v.vote_count, 0) * 0.35 +
              COALESCE(c.comment_count, 0) * 0.25 +
              GREATEST(0, 15 - EXTRACT(DAY FROM NOW() - COALESCE(i.published_at, i.created_at))) * 0.2
            )::float AS trending_score,
            EXISTS (
              SELECT 1 FROM idea_votes iv
              WHERE iv.idea_id = i.id AND iv.user_id = ${len(params) - 2}
            ) AS user_has_voted
          FROM ideas i
          JOIN users u ON u.id = i.author_id
          LEFT JOIN idea_versions ivs ON ivs.id = i.version_id
          LEFT JOIN (
            SELECT idea_id, COUNT(*) AS vote_count
            FROM idea_votes
            GROUP BY idea_id
          ) v ON v.idea_id = i.id
          LEFT JOIN (
            SELECT idea_id, COUNT(*) AS comment_count
            FROM idea_comments
            WHERE moderation_status = 'publicado'
            GROUP BY idea_id
          ) c ON c.idea_id = i.id
          LEFT JOIN (
            SELECT idea_id, COUNT(*) AS recent_vote_count
            FROM idea_votes
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY idea_id
          ) rv ON rv.idea_id = i.id
          LEFT JOIN (
            SELECT idea_id, COUNT(*) AS recent_comment_count
            FROM idea_comments
            WHERE created_at >= NOW() - INTERVAL '30 days'
              AND moderation_status = 'publicado'
            GROUP BY idea_id
          ) rc ON rc.idea_id = i.id
          WHERE {where_sql}
        )
        SELECT * FROM listed i
        ORDER BY {sort_sql}
        LIMIT ${len(params) - 1} OFFSET ${len(params)}
        """,
        *params,
    )
    topics = await _topics_for_ideas([row["id"] for row in rows])
    items = []
    for row in rows:
        data = _row_to_dict(row)
        data["topics"] = topics.get(data["id"], [])
        data["can_edit"] = False
        data["can_delete"] = False
        items.append(data)
    return items, int(total or 0)


async def get_public_roadmap(*, user_id: UUID) -> list[dict[str, Any]]:
    rows = await database.fetch(
        """
        SELECT
          i.*,
          u.name AS author_name,
          u.organ AS author_organ,
          ivs.name AS version_name,
          ivs.description AS version_description,
          ivs.forecast AS version_forecast,
          ivs.sort_order AS version_sort_order,
          ivs.is_active AS version_is_active,
          ivs.created_by AS version_created_by,
          ivs.created_at AS version_created_at,
          ivs.updated_at AS version_updated_at,
          COALESCE(v.vote_count, 0)::int AS vote_count,
          COALESCE(c.comment_count, 0)::int AS comment_count,
          EXISTS (
            SELECT 1 FROM idea_votes iv
            WHERE iv.idea_id = i.id AND iv.user_id = $1
          ) AS user_has_voted
        FROM ideas i
        JOIN users u ON u.id = i.author_id
        JOIN idea_versions ivs ON ivs.id = i.version_id
        LEFT JOIN (
          SELECT idea_id, COUNT(*) AS vote_count
          FROM idea_votes
          GROUP BY idea_id
        ) v ON v.idea_id = i.id
        LEFT JOIN (
          SELECT idea_id, COUNT(*) AS comment_count
          FROM idea_comments
          WHERE moderation_status = 'publicado'
          GROUP BY idea_id
        ) c ON c.idea_id = i.id
        WHERE i.deleted_at IS NULL
          AND i.moderation_status = 'publicada'
          AND i.idea_status IS NOT NULL
          AND i.version_id IS NOT NULL
        ORDER BY
          ivs.sort_order,
          ivs.name,
          CASE i.idea_status
            WHEN 'em_desenvolvimento' THEN 1
            WHEN 'planejada' THEN 2
            WHEN 'concluida' THEN 3
            ELSE 4
          END,
          COALESCE(v.vote_count, 0) DESC,
          i.published_at DESC NULLS LAST
        """,
        user_id,
    )

    topics = await _topics_for_ideas([row["id"] for row in rows])
    grouped: dict[UUID, dict[str, Any]] = {}
    for row in rows:
        data = _row_to_dict(row)
        version_id = data["version_id"]
        if version_id not in grouped:
            grouped[version_id] = {
                "version": {
                    "id": version_id,
                    "name": data["version_name"],
                    "description": data["version_description"],
                    "forecast": data["version_forecast"],
                    "sort_order": data["version_sort_order"],
                    "is_active": data["version_is_active"],
                    "created_by": data["version_created_by"],
                    "created_at": data["version_created_at"],
                    "updated_at": data["version_updated_at"],
                },
                "ideas": [],
            }

        data["topics"] = topics.get(data["id"], [])
        data["can_edit"] = False
        data["can_delete"] = False
        grouped[version_id]["ideas"].append(data)

    return list(grouped.values())


async def add_vote(*, idea_id: UUID, user_id: UUID) -> dict[str, Any]:
    row = await database.fetchrow(
        """
        SELECT id
        FROM ideas
        WHERE id = $1
          AND deleted_at IS NULL
          AND moderation_status = 'publicada'
        """,
        idea_id,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ideia não encontrada")

    await database.execute(
        """
        INSERT INTO idea_votes (idea_id, user_id)
        VALUES ($1, $2)
        ON CONFLICT DO NOTHING
        """,
        idea_id,
        user_id,
    )
    return await get_idea_detail(idea_id, user_id)


async def remove_vote(*, idea_id: UUID, user_id: UUID) -> dict[str, Any]:
    row = await database.fetchrow(
        """
        SELECT id
        FROM ideas
        WHERE id = $1
          AND deleted_at IS NULL
          AND moderation_status = 'publicada'
        """,
        idea_id,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ideia não encontrada")

    await database.execute(
        "DELETE FROM idea_votes WHERE idea_id = $1 AND user_id = $2",
        idea_id,
        user_id,
    )
    return await get_idea_detail(idea_id, user_id)


async def list_comments(*, idea_id: UUID, user_id: UUID, include_hidden: bool = False) -> list[dict[str, Any]]:
    await _ensure_public_idea(idea_id)
    status_filter = "" if include_hidden else "AND c.moderation_status = 'publicado'"
    rows = await database.fetch(
        f"""
        SELECT
          c.*,
          u.name AS author_name,
          u.organ AS author_organ,
          ur.reaction AS user_reaction
        FROM idea_comments c
        JOIN users u ON u.id = c.author_id
        LEFT JOIN idea_comment_reactions ur
          ON ur.comment_id = c.id AND ur.user_id = $2
        WHERE c.idea_id = $1
          {status_filter}
        ORDER BY
          c.parent_id NULLS FIRST,
          c.created_at ASC
        """,
        idea_id,
        user_id,
    )
    comment_ids = [row["id"] for row in rows]
    reaction_rows = await database.fetch(
        """
        SELECT comment_id, reaction, COUNT(*)::int AS count
        FROM idea_comment_reactions
        WHERE comment_id = ANY($1::uuid[])
        GROUP BY comment_id, reaction
        """,
        comment_ids,
    ) if comment_ids else []

    reactions: dict[UUID, dict[str, int]] = {comment_id: {} for comment_id in comment_ids}
    for row in reaction_rows:
        reactions[row["comment_id"]][row["reaction"]] = row["count"]

    by_id: dict[UUID, dict[str, Any]] = {}
    roots: list[dict[str, Any]] = []
    for row in rows:
        data = _row_to_dict(row)
        data["reactions"] = reactions.get(data["id"], {})
        data["replies"] = []
        by_id[data["id"]] = data

    for data in by_id.values():
        parent_id = data["parent_id"]
        if parent_id is None:
            roots.append(data)
        elif parent_id in by_id:
            by_id[parent_id]["replies"].append(data)

    return roots


async def list_admin_comments(*, idea_id: UUID, user_id: UUID) -> list[dict[str, Any]]:
    return await list_comments(idea_id=idea_id, user_id=user_id, include_hidden=True)


async def create_comment(*, idea_id: UUID, body: IdeaCommentCreate, user_id: UUID) -> dict[str, Any]:
    await _ensure_public_idea(idea_id)
    row = await database.fetchrow(
        """
        INSERT INTO idea_comments (idea_id, author_id, content)
        VALUES ($1, $2, $3)
        RETURNING *
        """,
        idea_id,
        user_id,
        body.content,
    )
    return _row_to_dict(row)


async def create_reply(*, idea_id: UUID, parent_id: UUID, body: IdeaCommentCreate, user_id: UUID) -> dict[str, Any]:
    await _ensure_public_idea(idea_id)
    parent = await database.fetchrow(
        """
        SELECT id, parent_id
        FROM idea_comments
        WHERE id = $1
          AND idea_id = $2
          AND moderation_status = 'publicado'
        """,
        parent_id,
        idea_id,
    )
    if parent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentário não encontrado")
    if parent["parent_id"] is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não é permitido responder uma resposta")

    row = await database.fetchrow(
        """
        INSERT INTO idea_comments (idea_id, parent_id, author_id, content)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """,
        idea_id,
        parent_id,
        user_id,
        body.content,
    )
    return _row_to_dict(row)


async def set_comment_reaction(*, comment_id: UUID, reaction: IdeaReaction, user_id: UUID) -> dict[str, Any]:
    row = await database.fetchrow(
        """
        SELECT c.id, c.idea_id
        FROM idea_comments c
        JOIN ideas i ON i.id = c.idea_id
        WHERE c.id = $1
          AND c.moderation_status = 'publicado'
          AND i.deleted_at IS NULL
          AND i.moderation_status = 'publicada'
        """,
        comment_id,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentário não encontrado")

    await database.execute(
        """
        INSERT INTO idea_comment_reactions (comment_id, user_id, reaction)
        VALUES ($1, $2, $3)
        ON CONFLICT (comment_id, user_id)
        DO UPDATE SET reaction = EXCLUDED.reaction, created_at = NOW()
        """,
        comment_id,
        user_id,
        reaction.value,
    )
    return {"idea_id": row["idea_id"], "comment_id": comment_id, "reaction": reaction.value}


async def remove_comment_reaction(*, comment_id: UUID, reaction: IdeaReaction, user_id: UUID) -> None:
    await database.execute(
        """
        DELETE FROM idea_comment_reactions
        WHERE comment_id = $1
          AND user_id = $2
          AND reaction = $3
        """,
        comment_id,
        user_id,
        reaction.value,
    )


async def moderate_comment(
    *,
    comment_id: UUID,
    moderator_id: UUID,
    hide: bool,
    reason: str | None = None,
    request=None,
) -> dict[str, Any]:
    row = await database.fetchrow(
        "SELECT * FROM idea_comments WHERE id = $1",
        comment_id,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentário não encontrado")
    if hide and not reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe o motivo da moderação")

    next_status = "oculto" if hide else "publicado"
    updated = await database.fetchrow(
        """
        UPDATE idea_comments
        SET moderation_status = $2::idea_comment_moderation_status,
            moderation_reason = $3,
            moderated_by = $4,
            moderated_at = NOW(),
            updated_at = NOW()
        WHERE id = $1
        RETURNING *
        """,
        comment_id,
        next_status,
        reason,
        moderator_id,
    )
    await log_audit(
        user_id=moderator_id,
        action="IDEA_COMMENT_HIDE" if hide else "IDEA_COMMENT_RESTORE",
        entity="idea_comment",
        entity_id=comment_id,
        metadata={"idea_id": str(row["idea_id"]), "reason": reason},
        request=request,
    )
    if hide and row["author_id"] != moderator_id:
        await create_notification(
            type="warning",
            title="Comentário ocultado",
            message="Um comentário seu foi ocultado pela curadoria.",
            link=f"/ideias/{row['idea_id']}",
            is_global=False,
            target_user_ids=[row["author_id"]],
        )
    return _row_to_dict(updated)


async def list_admin_ideas(
    *,
    page: int = 1,
    page_size: int = 20,
    moderation_status: str | None = None,
    search: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    params: list[Any] = []
    conditions = []

    if moderation_status:
        params.append(moderation_status)
        conditions.append(f"i.moderation_status = ${len(params)}::idea_moderation_status")

    if search:
        params.append(f"%{search.strip()}%")
        conditions.append(f"(i.title ILIKE ${len(params)} OR i.description ILIKE ${len(params)} OR u.name ILIKE ${len(params)})")

    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    total = await database.fetchval(
        f"""
        SELECT COUNT(*)
        FROM ideas i
        JOIN users u ON u.id = i.author_id
        {where_sql}
        """,
        *params,
    )

    params.extend([page_size, (page - 1) * page_size])
    rows = await database.fetch(
        f"""
        SELECT
          i.*,
          u.name AS author_name,
          u.organ AS author_organ,
          ivs.name AS version_name,
          ivs.forecast AS version_forecast,
          COALESCE(v.vote_count, 0)::int AS vote_count,
          COALESCE(c.comment_count, 0)::int AS comment_count,
          FALSE AS user_has_voted
        FROM ideas i
        JOIN users u ON u.id = i.author_id
        LEFT JOIN idea_versions ivs ON ivs.id = i.version_id
        LEFT JOIN (
          SELECT idea_id, COUNT(*) AS vote_count
          FROM idea_votes
          GROUP BY idea_id
        ) v ON v.idea_id = i.id
        LEFT JOIN (
          SELECT idea_id, COUNT(*) AS comment_count
          FROM idea_comments
          WHERE moderation_status = 'publicado'
          GROUP BY idea_id
        ) c ON c.idea_id = i.id
        {where_sql}
        ORDER BY
          CASE i.moderation_status
            WHEN 'aguardando_curadoria' THEN 0
            WHEN 'exclusao_solicitada' THEN 1
            WHEN 'publicada' THEN 2
            WHEN 'rejeitada' THEN 3
            ELSE 4
          END,
          i.created_at DESC
        LIMIT ${len(params) - 1} OFFSET ${len(params)}
        """,
        *params,
    )
    topics = await _topics_for_ideas([row["id"] for row in rows])
    items = []
    for row in rows:
        data = _row_to_dict(row)
        data["topics"] = topics.get(data["id"], [])
        data["can_edit"] = False
        data["can_delete"] = False
        items.append(data)
    return items, int(total or 0)


async def create_idea(*, body: IdeaCreate, user_id: UUID) -> dict[str, Any]:
    topic_ids = body.topic_ids
    await _ensure_topics_exist(topic_ids)
    async with database.get_connection() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO ideas (title, description, author_id)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                body.title,
                body.description,
                user_id,
            )
            if topic_ids:
                await conn.executemany(
                    """
                    INSERT INTO idea_topic_links (idea_id, topic_id)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                    """,
                    [(row["id"], topic_id) for topic_id in topic_ids],
                )
    return await get_idea_detail(row["id"], user_id)


async def update_idea(*, idea_id: UUID, body: IdeaUpdate, user_id: UUID) -> dict[str, Any]:
    topic_ids = body.topic_ids
    await _ensure_topics_exist(topic_ids)
    row = await _get_idea_detail_row(idea_id, user_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ideia não encontrada")
    data = _row_to_dict(row)
    if not _can_author_change(data, user_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ideia não pode mais ser editada diretamente",
        )

    async with database.get_connection() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                UPDATE ideas
                SET title = $1, description = $2, updated_at = NOW()
                WHERE id = $3
                """,
                body.title,
                body.description,
                idea_id,
            )
            await conn.execute("DELETE FROM idea_topic_links WHERE idea_id = $1", idea_id)
            if topic_ids:
                await conn.executemany(
                    """
                    INSERT INTO idea_topic_links (idea_id, topic_id)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                    """,
                    [(idea_id, topic_id) for topic_id in topic_ids],
                )
    return await get_idea_detail(idea_id, user_id)


async def delete_idea(*, idea_id: UUID, user_id: UUID) -> None:
    row = await _get_idea_detail_row(idea_id, user_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ideia não encontrada")
    data = _row_to_dict(row)
    if not _can_author_change(data, user_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ideia não pode mais ser excluída diretamente",
        )
    await database.execute("DELETE FROM ideas WHERE id = $1", idea_id)


async def request_idea_deletion(*, idea_id: UUID, user_id: UUID, reason: str, request=None) -> dict[str, Any]:
    row = await _get_idea_detail_row(idea_id, user_id)
    if row is None or row["author_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ideia não encontrada")
    if row["moderation_status"] != "publicada":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Apenas ideias publicadas podem receber solicitação de exclusão")
    if not reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe o motivo da solicitação")

    updated = await database.fetchrow(
        """
        UPDATE ideas
        SET moderation_status = 'exclusao_solicitada',
            deletion_requested_at = NOW(),
            deletion_request_reason = $2,
            updated_at = NOW()
        WHERE id = $1
        RETURNING *
        """,
        idea_id,
        reason,
    )
    await log_audit(
        user_id=user_id,
        action="IDEA_DELETION_REQUEST",
        entity="idea",
        entity_id=idea_id,
        metadata={"reason": reason},
        request=request,
    )
    return await get_idea_detail(updated["id"], user_id)


async def _get_admin_idea_row(idea_id: UUID) -> dict[str, Any]:
    row = await database.fetchrow(
        """
        SELECT
          i.*,
          u.name AS author_name,
          u.organ AS author_organ,
          ivs.name AS version_name,
          ivs.forecast AS version_forecast
        FROM ideas i
        JOIN users u ON u.id = i.author_id
        LEFT JOIN idea_versions ivs ON ivs.id = i.version_id
        WHERE i.id = $1
        """,
        idea_id,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ideia não encontrada")
    return _row_to_dict(row)


async def _notify_idea_author(*, idea: dict[str, Any], type: str, title: str, message: str, link: str) -> None:
    await create_notification(
        type=type,
        title=title,
        message=message,
        link=link,
        is_global=False,
        target_user_ids=[idea["author_id"]],
    )


async def approve_idea(*, idea_id: UUID, reviewer_id: UUID, reason: str | None = None, request=None) -> dict[str, Any]:
    idea = await _get_admin_idea_row(idea_id)
    if idea["moderation_status"] == "excluida":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ideia excluída não pode ser publicada")

    row = await database.fetchrow(
        """
        UPDATE ideas
        SET moderation_status = 'publicada',
            curation_notes = $2,
            rejection_reason = NULL,
            deletion_requested_at = NULL,
            deletion_request_reason = NULL,
            deleted_at = NULL,
            published_at = COALESCE(published_at, NOW()),
            reviewed_by = $3,
            reviewed_at = NOW(),
            updated_at = NOW()
        WHERE id = $1
        RETURNING *
        """,
        idea_id,
        reason,
        reviewer_id,
    )
    await _notify_idea_author(
        idea=idea,
        type="success",
        title="Ideia publicada",
        message=f'Sua ideia "{idea["title"]}" foi aprovada e publicada.',
        link=f"/ideias/{idea_id}",
    )
    await log_audit(
        user_id=reviewer_id,
        action="IDEA_APPROVE",
        entity="idea",
        entity_id=idea_id,
        metadata={"previous_moderation_status": idea["moderation_status"], "reason": reason},
        request=request,
    )
    return await _build_idea_detail(row, reviewer_id)


async def reject_idea(*, idea_id: UUID, reviewer_id: UUID, reason: str, request=None) -> dict[str, Any]:
    if not reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe o motivo da rejeição")
    idea = await _get_admin_idea_row(idea_id)
    if idea["moderation_status"] == "excluida":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ideia excluída não pode ser rejeitada")

    row = await database.fetchrow(
        """
        UPDATE ideas
        SET moderation_status = 'rejeitada',
            rejection_reason = $2,
            curation_notes = $2,
            reviewed_by = $3,
            reviewed_at = NOW(),
            updated_at = NOW()
        WHERE id = $1
        RETURNING *
        """,
        idea_id,
        reason,
        reviewer_id,
    )
    await _notify_idea_author(
        idea=idea,
        type="warning",
        title="Ideia rejeitada",
        message=f'Sua ideia "{idea["title"]}" foi rejeitada pela curadoria.',
        link="/minhas-ideias",
    )
    await log_audit(
        user_id=reviewer_id,
        action="IDEA_REJECT",
        entity="idea",
        entity_id=idea_id,
        metadata={"previous_moderation_status": idea["moderation_status"], "reason": reason},
        request=request,
    )
    return await _build_idea_detail(row, reviewer_id)


async def remove_policy_violation(*, idea_id: UUID, reviewer_id: UUID, reason: str, request=None) -> dict[str, Any]:
    if not reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe o motivo da exclusão")
    idea = await _get_admin_idea_row(idea_id)
    row = await database.fetchrow(
        """
        UPDATE ideas
        SET moderation_status = 'excluida',
            rejection_reason = $2,
            curation_notes = $2,
            deleted_at = NOW(),
            reviewed_by = $3,
            reviewed_at = NOW(),
            updated_at = NOW()
        WHERE id = $1
        RETURNING *
        """,
        idea_id,
        reason,
        reviewer_id,
    )
    await _notify_idea_author(
        idea=idea,
        type="error",
        title="Ideia excluída",
        message=f'Sua ideia "{idea["title"]}" foi excluída por violação de política.',
        link="/minhas-ideias",
    )
    await log_audit(
        user_id=reviewer_id,
        action="IDEA_REMOVE_POLICY_VIOLATION",
        entity="idea",
        entity_id=idea_id,
        metadata={"previous_moderation_status": idea["moderation_status"], "reason": reason},
        request=request,
    )
    return await _build_idea_detail(row, reviewer_id)


async def approve_deletion_request(*, idea_id: UUID, reviewer_id: UUID, reason: str | None = None, request=None) -> dict[str, Any]:
    idea = await _get_admin_idea_row(idea_id)
    if idea["moderation_status"] != "exclusao_solicitada":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ideia não possui solicitação de exclusão pendente")

    row = await database.fetchrow(
        """
        UPDATE ideas
        SET moderation_status = 'excluida',
            deleted_at = NOW(),
            reviewed_by = $2,
            reviewed_at = NOW(),
            curation_notes = $3,
            updated_at = NOW()
        WHERE id = $1
        RETURNING *
        """,
        idea_id,
        reviewer_id,
        reason,
    )
    await _notify_idea_author(
        idea=idea,
        type="success",
        title="Exclusão aprovada",
        message=f'Sua solicitação de exclusão da ideia "{idea["title"]}" foi aprovada.',
        link="/minhas-ideias",
    )
    await log_audit(
        user_id=reviewer_id,
        action="IDEA_DELETION_APPROVE",
        entity="idea",
        entity_id=idea_id,
        metadata={"request_reason": idea["deletion_request_reason"], "review_reason": reason},
        request=request,
    )
    return await _build_idea_detail(row, reviewer_id)


async def deny_deletion_request(*, idea_id: UUID, reviewer_id: UUID, reason: str, request=None) -> dict[str, Any]:
    if not reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe o motivo da decisão")
    idea = await _get_admin_idea_row(idea_id)
    if idea["moderation_status"] != "exclusao_solicitada":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ideia não possui solicitação de exclusão pendente")

    row = await database.fetchrow(
        """
        UPDATE ideas
        SET moderation_status = 'publicada',
            deletion_requested_at = NULL,
            deletion_request_reason = NULL,
            reviewed_by = $2,
            reviewed_at = NOW(),
            curation_notes = $3,
            updated_at = NOW()
        WHERE id = $1
        RETURNING *
        """,
        idea_id,
        reviewer_id,
        reason,
    )
    await _notify_idea_author(
        idea=idea,
        type="warning",
        title="Exclusão negada",
        message=f'Sua solicitação de exclusão da ideia "{idea["title"]}" foi negada pela curadoria.',
        link=f"/ideias/{idea_id}",
    )
    await log_audit(
        user_id=reviewer_id,
        action="IDEA_DELETION_DENY",
        entity="idea",
        entity_id=idea_id,
        metadata={"request_reason": idea["deletion_request_reason"], "review_reason": reason},
        request=request,
    )
    return await _build_idea_detail(row, reviewer_id)


async def update_idea_roadmap(
    *,
    idea_id: UUID,
    body: IdeaRoadmapUpdate,
    reviewer_id: UUID,
    request=None,
) -> dict[str, Any]:
    idea = await _get_admin_idea_row(idea_id)
    if idea["moderation_status"] != "publicada":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Apenas ideias publicadas podem ir para o roadmap")

    next_status = body.idea_status.value if body.idea_status else None
    next_version_id = body.version_id if next_status else None
    if next_status and not next_version_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Versão obrigatória para status de roadmap")

    if next_version_id:
        version = await database.fetchrow(
            "SELECT id FROM idea_versions WHERE id = $1 AND is_active = TRUE",
            next_version_id,
        )
        if version is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Versão inválida ou inativa")

    row = await database.fetchrow(
        """
        UPDATE ideas
        SET idea_status = $2::idea_status,
            version_id = $3,
            updated_at = NOW()
        WHERE id = $1
        RETURNING *
        """,
        idea_id,
        next_status,
        next_version_id,
    )
    await log_audit(
        user_id=reviewer_id,
        action="IDEA_ROADMAP_UPDATE",
        entity="idea",
        entity_id=idea_id,
        metadata={
            "previous_status": idea["idea_status"],
            "new_status": next_status,
            "previous_version_id": str(idea["version_id"]) if idea["version_id"] else None,
            "new_version_id": str(next_version_id) if next_version_id else None,
        },
        request=request,
    )
    return await get_idea_detail(row["id"], reviewer_id)


async def find_similar_ideas(
    *,
    title: str,
    description: str = "",
    topic_ids: list[UUID] | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    topic_ids = topic_ids or []
    await _ensure_topics_exist(topic_ids)
    limit = min(max(limit, 1), 10)
    rows = await database.fetch(
        """
        WITH topic_matches AS (
          SELECT idea_id, COUNT(*)::int AS topic_match_count
          FROM idea_topic_links
          WHERE topic_id = ANY($3::uuid[])
          GROUP BY idea_id
        ),
        engagement AS (
          SELECT
            i.id AS idea_id,
            COUNT(DISTINCT v.user_id)::int AS vote_count,
            COUNT(DISTINCT c.id)::int AS comment_count
          FROM ideas i
          LEFT JOIN idea_votes v ON v.idea_id = i.id
          LEFT JOIN idea_comments c ON c.idea_id = i.id AND c.moderation_status = 'publicado'
          GROUP BY i.id
        )
        SELECT
          i.id,
          i.title,
          i.description,
          i.moderation_status,
          i.idea_status,
          i.published_at,
          i.created_at,
          COALESCE(e.vote_count, 0) AS vote_count,
          COALESCE(e.comment_count, 0) AS comment_count,
          COALESCE(tm.topic_match_count, 0) AS topic_match_count,
          (
            GREATEST(similarity(i.title, $1), similarity(i.description, $2)) +
            LEAST(COALESCE(tm.topic_match_count, 0), 3) * 0.12
          )::float AS similarity_score
        FROM ideas i
        LEFT JOIN topic_matches tm ON tm.idea_id = i.id
        LEFT JOIN engagement e ON e.idea_id = i.id
        WHERE i.deleted_at IS NULL
          AND i.moderation_status = 'publicada'
          AND (
            similarity(i.title, $1) > 0.12
            OR similarity(i.description, $2) > 0.08
            OR COALESCE(tm.topic_match_count, 0) > 0
          )
        ORDER BY similarity_score DESC, vote_count DESC, i.published_at DESC NULLS LAST
        LIMIT $4
        """,
        title,
        description,
        topic_ids,
        limit,
    )
    return [_row_to_dict(row) for row in rows]
