from asyncio import gather

from fastapi import APIRouter, Depends

from app.core import database
from app.core.deps import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
async def get_stats(_: dict = Depends(get_current_user)):
    (
        total_models,
        total_users,
        total_prompts,
        top_rated_rows,
        most_used_rows,
        community_total,
        community_pending,
        community_public,
        top_contributors_rows,
    ) = await gather(
        database.fetchval("SELECT COUNT(*) FROM modelos WHERE is_active = TRUE"),
        database.fetchval("SELECT COUNT(*) FROM users WHERE is_active = TRUE"),
        database.fetchval(
            """
            SELECT COUNT(*)
            FROM prompts
            WHERE is_active = TRUE
              AND publication_status = 'publico'
            """
        ),
        database.fetch(
            """
            SELECT id, title, rating_avg, rating_count
            FROM prompts
            WHERE is_active = TRUE
              AND publication_status = 'publico'
              AND rating_count > 0
            ORDER BY rating_avg DESC, rating_count DESC
            LIMIT 5
            """
        ),
        database.fetch(
            """
            SELECT id, title, usage_count
            FROM prompts
            WHERE is_active = TRUE
              AND publication_status = 'publico'
            ORDER BY usage_count DESC
            LIMIT 5
            """
        ),
        # ── Comunidade ──────────────────────────────────────────────────────────
        database.fetchval(
            "SELECT COUNT(*) FROM prompts WHERE source = 'comunidade' AND is_active = TRUE"
        ),
        database.fetchval(
            """
            SELECT COUNT(*) FROM prompts
            WHERE source = 'comunidade'
              AND is_active = TRUE
              AND publication_status IN ('aguardando', 'em_revisao')
            """
        ),
        database.fetchval(
            """
            SELECT COUNT(*) FROM prompts
            WHERE source = 'comunidade'
              AND is_active = TRUE
              AND publication_status = 'publico'
            """
        ),
        database.fetch(
            """
            SELECT u.name, u.organ, COUNT(p.id) AS approved_count
            FROM prompts p
            JOIN users u ON p.author_id = u.id
            WHERE p.source = 'comunidade'
              AND p.publication_status = 'publico'
              AND p.is_active = TRUE
              AND u.is_active = TRUE
            GROUP BY u.id, u.name, u.organ
            ORDER BY approved_count DESC
            LIMIT 5
            """
        ),
    )

    return {
        "total_models": total_models,
        "total_users": total_users,
        "total_prompts": total_prompts,
        "uptime_percent": 99.9,
        "top_rated_prompts": [
            {
                "id": str(r["id"]),
                "title": r["title"],
                "rating_avg": float(r["rating_avg"]),
                "rating_count": r["rating_count"],
            }
            for r in top_rated_rows
        ],
        "most_used_prompts": [
            {"id": str(r["id"]), "title": r["title"], "usage_count": r["usage_count"]}
            for r in most_used_rows
        ],
        # ── Comunidade ──────────────────────────────────────────────────────────
        "community_prompts_total": community_total,
        "community_prompts_pending": community_pending,
        "community_prompts_public": community_public,
        "top_community_contributors": [
            {
                "name": r["name"],
                "organ": r["organ"],
                "approved_count": r["approved_count"],
            }
            for r in top_contributors_rows
        ],
    }
