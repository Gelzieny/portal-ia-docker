import os
import unittest
from uuid import UUID, uuid4


os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_DB", "goia_test")
os.environ.setdefault("POSTGRES_USER", "goia")
os.environ.setdefault("POSTGRES_PASSWORD", "goia")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("FIRST_ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("FIRST_ADMIN_PASSWORD", "secret123")

from fastapi import HTTPException

from app.models.idea import IdeaCommentCreate, IdeaRoadmapUpdate, IdeaStatus
from app.services import idea_service


IDEA_ID = UUID("11111111-1111-1111-1111-111111111111")
USER_ID = UUID("22222222-2222-2222-2222-222222222222")
MODERATOR_ID = UUID("33333333-3333-3333-3333-333333333333")
COMMENT_ID = UUID("44444444-4444-4444-4444-444444444444")
REPLY_ID = UUID("55555555-5555-5555-5555-555555555555")


class VoteDatabase:
    def __init__(self):
        self.votes: set[tuple[UUID, UUID]] = set()

    async def fetchrow(self, query, *args):
        return {"id": args[0]}

    async def execute(self, query, *args):
        self.votes.add((args[0], args[1]))


class ReplyDatabase:
    async def fetchrow(self, query, *args):
        if "SELECT id, parent_id" in query:
            return {"id": args[0], "parent_id": REPLY_ID}
        raise AssertionError(f"Unexpected query: {query}")


class CommentModerationDatabase:
    async def fetchrow(self, query, *args):
        if query.startswith("SELECT * FROM idea_comments"):
            return {
                "id": COMMENT_ID,
                "idea_id": IDEA_ID,
                "parent_id": None,
                "author_id": USER_ID,
                "content": "Comentário original",
                "moderation_status": "publicado",
                "moderation_reason": None,
                "moderated_by": None,
                "moderated_at": None,
                "created_at": None,
                "updated_at": None,
            }
        if "UPDATE idea_comments" in query:
            return {
                "id": COMMENT_ID,
                "idea_id": IDEA_ID,
                "parent_id": None,
                "author_id": USER_ID,
                "content": "Comentário original",
                "moderation_status": "oculto",
                "moderation_reason": args[2],
                "moderated_by": args[3],
                "moderated_at": None,
                "created_at": None,
                "updated_at": None,
            }
        raise AssertionError(f"Unexpected query: {query}")


class IdeasBehaviorRulesTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.original_database = idea_service.database
        self.original_get_idea_detail = idea_service.get_idea_detail
        self.original_ensure_public_idea = idea_service._ensure_public_idea
        self.original_get_admin_idea_row = idea_service._get_admin_idea_row
        self.original_log_audit = idea_service.log_audit
        self.original_create_notification = idea_service.create_notification

    async def asyncTearDown(self):
        idea_service.database = self.original_database
        idea_service.get_idea_detail = self.original_get_idea_detail
        idea_service._ensure_public_idea = self.original_ensure_public_idea
        idea_service._get_admin_idea_row = self.original_get_admin_idea_row
        idea_service.log_audit = self.original_log_audit
        idea_service.create_notification = self.original_create_notification

    async def test_vote_is_unique_per_user_and_idea(self):
        db = VoteDatabase()
        idea_service.database = db

        async def fake_get_idea_detail(idea_id, user_id):
            return {
                "id": idea_id,
                "vote_count": len(db.votes),
                "user_has_voted": (idea_id, user_id) in db.votes,
            }

        idea_service.get_idea_detail = fake_get_idea_detail

        first = await idea_service.add_vote(idea_id=IDEA_ID, user_id=USER_ID)
        second = await idea_service.add_vote(idea_id=IDEA_ID, user_id=USER_ID)

        self.assertEqual(first["vote_count"], 1)
        self.assertEqual(second["vote_count"], 1)
        self.assertTrue(second["user_has_voted"])

    async def test_reply_cannot_target_another_reply(self):
        idea_service.database = ReplyDatabase()

        async def fake_ensure_public_idea(idea_id):
            return None

        idea_service._ensure_public_idea = fake_ensure_public_idea

        with self.assertRaises(HTTPException) as ctx:
            await idea_service.create_reply(
                idea_id=IDEA_ID,
                parent_id=COMMENT_ID,
                body=IdeaCommentCreate(content="Resposta invalida"),
                user_id=USER_ID,
            )

        self.assertEqual(ctx.exception.status_code, 409)

    async def test_roadmap_status_requires_version(self):
        async def fake_get_admin_idea_row(idea_id):
            return {
                "id": idea_id,
                "moderation_status": "publicada",
                "idea_status": None,
                "version_id": None,
            }

        idea_service._get_admin_idea_row = fake_get_admin_idea_row

        with self.assertRaises(HTTPException) as ctx:
            await idea_service.update_idea_roadmap(
                idea_id=IDEA_ID,
                body=IdeaRoadmapUpdate(idea_status=IdeaStatus.planejada, version_id=None),
                reviewer_id=MODERATOR_ID,
            )

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Versão obrigatória", ctx.exception.detail)

    async def test_hiding_comment_notifies_author(self):
        notifications = []
        audits = []
        idea_service.database = CommentModerationDatabase()

        async def fake_log_audit(**kwargs):
            audits.append(kwargs)

        async def fake_create_notification(**kwargs):
            notifications.append(kwargs)

        idea_service.log_audit = fake_log_audit
        idea_service.create_notification = fake_create_notification

        result = await idea_service.moderate_comment(
            comment_id=COMMENT_ID,
            moderator_id=MODERATOR_ID,
            hide=True,
            reason="Violacao de politica",
        )

        self.assertEqual(result["moderation_status"], "oculto")
        self.assertEqual(audits[0]["action"], "IDEA_COMMENT_HIDE")
        self.assertEqual(notifications[0]["title"], "Comentário ocultado")
        self.assertEqual(notifications[0]["target_user_ids"], [USER_ID])
        self.assertEqual(notifications[0]["link"], f"/ideias/{IDEA_ID}")

    async def test_moderator_does_not_notify_self_when_hiding_own_comment(self):
        notifications = []
        idea_service.database = CommentModerationDatabase()

        async def fake_log_audit(**kwargs):
            return None

        async def fake_create_notification(**kwargs):
            notifications.append(kwargs)

        idea_service.log_audit = fake_log_audit
        idea_service.create_notification = fake_create_notification

        await idea_service.moderate_comment(
            comment_id=COMMENT_ID,
            moderator_id=USER_ID,
            hide=True,
            reason="Violacao de politica",
        )

        self.assertEqual(notifications, [])


if __name__ == "__main__":
    unittest.main()
