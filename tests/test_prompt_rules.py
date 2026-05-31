import os
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_DB", "goia_test")
os.environ.setdefault("POSTGRES_USER", "goia")
os.environ.setdefault("POSTGRES_PASSWORD", "goia")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("FIRST_ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("FIRST_ADMIN_PASSWORD", "secret123")

from fastapi import HTTPException

from app.models.user_prompt import UserPromptSubmit
from app.routers.prompts import use_prompt
from app.routers.stats import get_stats
from app.routers.user_prompts import submit_my_prompt


class PromptRulesTests(unittest.IsolatedAsyncioTestCase):
    async def test_use_prompt_checks_publication_status_instead_of_is_public(self):
        user_id = str(uuid4())
        prompt_id = uuid4()

        with (
            patch(
                "app.routers.prompts.database.fetchrow",
                new=AsyncMock(return_value={"content": "abc"}),
            ) as fetchrow,
            patch("app.routers.prompts.database.execute", new=AsyncMock()) as execute,
            patch(
                "app.routers.prompts.database.fetchval",
                new=AsyncMock(return_value=None),
            ),
        ):
            result = await use_prompt(prompt_id, {"id": user_id})

        query = fetchrow.await_args.args[0]
        self.assertIn("publication_status = 'publico'", query)
        self.assertNotIn("is_public = TRUE", query)
        execute.assert_awaited_once()
        self.assertTrue(result["copied"])

    async def test_stats_queries_filter_by_publication_status(self):
        fetchval = AsyncMock(side_effect=[7, 10, 4, 8, 3, 2])
        fetch = AsyncMock(
            side_effect=[
                [
                    {
                        "id": uuid4(),
                        "title": "Prompt A",
                        "rating_avg": 4.9,
                        "rating_count": 12,
                    }
                ],
                [{"id": uuid4(), "title": "Prompt B", "usage_count": 99}],
                [{"name": "Ana", "organ": "SEI", "approved_count": 5}],
            ]
        )

        with (
            patch("app.routers.stats.database.fetchval", new=fetchval),
            patch("app.routers.stats.database.fetch", new=fetch),
        ):
            result = await get_stats({})

        fetchval_queries = [call.args[0] for call in fetchval.await_args_list]
        fetch_queries = [call.args[0] for call in fetch.await_args_list]
        all_queries = fetchval_queries + fetch_queries

        self.assertTrue(
            all(
                "publication_status = 'publico'" in q
                or "publication_status IN ('aguardando', 'em_revisao')" in q
                or "source = 'comunidade'" in q
                or "modelos" in q
                or "users" in q
                for q in all_queries
            )
        )
        self.assertEqual(result["total_prompts"], 4)
        self.assertEqual(result["top_rated_prompts"][0]["title"], "Prompt A")
        self.assertEqual(result["most_used_prompts"][0]["title"], "Prompt B")

    async def test_submit_my_prompt_stores_submission_notes_separately(self):
        prompt_id = uuid4()
        current_user = {"id": str(uuid4()), "name": "Maria", "organ": "SGG"}
        existing_prompt = {
            "id": prompt_id,
            "author_id": current_user["id"],
            "source": "comunidade",
            "title": "Prompt de teste",
            "content": "Conteudo suficiente para submissao",
            "category_id": uuid4(),
            "publication_status": "privado",
        }
        updated_prompt = {
            "id": prompt_id,
            "title": "Prompt de teste",
            "description": "",
            "content": "Conteudo suficiente para submissao",
            "category_id": existing_prompt["category_id"],
            "model_id": None,
            "tags": [],
            "difficulty": "iniciante",
            "variables": [],
            "is_public": False,
            "usage_count": 0,
            "rating_avg": 0,
            "rating_count": 0,
            "author_id": current_user["id"],
            "is_active": True,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-02T00:00:00+00:00",
            "publication_status": "aguardando",
            "source": "comunidade",
            "version": 1,
            "report_count": 0,
            "submitted_at": "2026-01-02T00:00:00+00:00",
            "submission_notes": "Contexto importante para o curador",
            "reviewed_at": None,
            "review_notes": None,
            "original_author_name": current_user["name"],
        }

        with (
            patch(
                "app.routers.user_prompts.database.fetchrow",
                new=AsyncMock(side_effect=[existing_prompt, updated_prompt]),
            ) as fetchrow,
            patch("app.routers.user_prompts._notify", new=AsyncMock()) as notify,
        ):
            result = await submit_my_prompt(
                prompt_id,
                UserPromptSubmit(submission_notes="Contexto importante para o curador"),
                current_user,
            )

        update_query = fetchrow.await_args_list[1].args[0]
        update_value = fetchrow.await_args_list[1].args[2]
        self.assertIn("submission_notes", update_query)
        self.assertNotIn("review_notes       = $2", update_query)
        self.assertEqual(update_value, "Contexto importante para o curador")
        self.assertEqual(result.submission_notes, "Contexto importante para o curador")
        self.assertIsNone(result.review_notes)
        notify.assert_awaited_once()

    async def test_submit_my_prompt_requires_private_status(self):
        prompt_id = uuid4()
        current_user = {"id": str(uuid4()), "name": "Maria", "organ": "SGG"}
        existing_prompt = {
            "id": prompt_id,
            "author_id": current_user["id"],
            "source": "comunidade",
            "title": "Prompt de teste",
            "content": "Conteudo suficiente para submissao",
            "category_id": uuid4(),
            "publication_status": "rascunho",
        }

        with patch(
            "app.routers.user_prompts.database.fetchrow",
            new=AsyncMock(return_value=existing_prompt),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await submit_my_prompt(
                    prompt_id, UserPromptSubmit(submission_notes="x"), current_user
                )

        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
