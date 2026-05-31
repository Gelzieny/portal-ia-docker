import inspect
import os
import unittest


os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_DB", "goia_test")
os.environ.setdefault("POSTGRES_USER", "goia")
os.environ.setdefault("POSTGRES_PASSWORD", "goia")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("FIRST_ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("FIRST_ADMIN_PASSWORD", "secret123")

from app.routers import ideas
from app.services.permission_service import DEFAULT_ROLE_PERMISSIONS, ROLES


def _captured_permission(endpoint, param_name):
    dependency = inspect.signature(endpoint).parameters[param_name].default.dependency
    for cell in dependency.__closure__ or []:
        content = cell.cell_contents
        if isinstance(content, str):
            return content
    return None


class IdeasFoundationRulesTests(unittest.TestCase):
    def test_gestor_produto_role_is_registered(self):
        self.assertIn("gestor_produto", ROLES)
        self.assertIn("gestor_produto", DEFAULT_ROLE_PERMISSIONS)

    def test_default_idea_permissions_match_spec(self):
        common = {
            "ideas.portal.view",
            "ideas.create",
            "ideas.vote",
            "ideas.comment",
            "ideas.comment.react",
            "ideas.own.manage",
            "roadmap.view",
        }
        elevated = {
            "ideas.curation.manage",
            "ideas.roadmap.manage",
            "admin.idea_versions.manage",
        }

        for role in {"gestor", "curador", "curador_modelos", "servidor"}:
            self.assertTrue(common.issubset(DEFAULT_ROLE_PERMISSIONS[role]))
            self.assertFalse(elevated.intersection(DEFAULT_ROLE_PERMISSIONS[role]))

        self.assertTrue(common.issubset(DEFAULT_ROLE_PERMISSIONS["gestor_produto"]))
        self.assertTrue(elevated.issubset(DEFAULT_ROLE_PERMISSIONS["gestor_produto"]))
        self.assertTrue(common.issubset(DEFAULT_ROLE_PERMISSIONS["admin"]))
        self.assertTrue(elevated.issubset(DEFAULT_ROLE_PERMISSIONS["admin"]))

    def test_ideas_foundation_endpoints_require_expected_permissions(self):
        self.assertEqual(_captured_permission(ideas.list_topics, "_"), "ideas.portal.view")
        self.assertEqual(_captured_permission(ideas.list_versions, "_"), "roadmap.view")
        self.assertEqual(_captured_permission(ideas.get_roadmap, "current_user"), "roadmap.view")

    def test_ideas_authoring_endpoints_require_expected_permissions(self):
        self.assertEqual(_captured_permission(ideas.list_public_ideas, "current_user"), "ideas.portal.view")
        self.assertEqual(_captured_permission(ideas.find_similar_ideas, "_"), "ideas.create")
        self.assertEqual(_captured_permission(ideas.list_my_ideas, "current_user"), "ideas.own.manage")
        self.assertEqual(_captured_permission(ideas.create_idea, "current_user"), "ideas.create")
        self.assertEqual(_captured_permission(ideas.get_idea, "current_user"), "ideas.portal.view")
        self.assertEqual(_captured_permission(ideas.update_idea, "current_user"), "ideas.own.manage")
        self.assertEqual(_captured_permission(ideas.delete_idea, "current_user"), "ideas.own.manage")
        self.assertEqual(_captured_permission(ideas.request_idea_deletion, "current_user"), "ideas.own.manage")
        self.assertEqual(_captured_permission(ideas.add_vote, "current_user"), "ideas.vote")
        self.assertEqual(_captured_permission(ideas.remove_vote, "current_user"), "ideas.vote")
        self.assertEqual(_captured_permission(ideas.list_comments, "current_user"), "ideas.portal.view")
        self.assertEqual(_captured_permission(ideas.create_comment, "current_user"), "ideas.comment")
        self.assertEqual(_captured_permission(ideas.create_reply, "current_user"), "ideas.comment")
        self.assertEqual(_captured_permission(ideas.set_comment_reaction, "current_user"), "ideas.comment.react")
        self.assertEqual(_captured_permission(ideas.remove_comment_reaction, "current_user"), "ideas.comment.react")

    def test_ideas_curation_endpoints_require_expected_permissions(self):
        self.assertEqual(_captured_permission(ideas.admin_list_ideas, "_"), "ideas.curation.manage")
        self.assertEqual(_captured_permission(ideas.admin_approve_idea, "current_user"), "ideas.curation.manage")
        self.assertEqual(_captured_permission(ideas.admin_reject_idea, "current_user"), "ideas.curation.manage")
        self.assertEqual(_captured_permission(ideas.admin_remove_policy_violation, "current_user"), "ideas.curation.manage")
        self.assertEqual(_captured_permission(ideas.admin_approve_deletion_request, "current_user"), "ideas.curation.manage")
        self.assertEqual(_captured_permission(ideas.admin_deny_deletion_request, "current_user"), "ideas.curation.manage")
        self.assertEqual(_captured_permission(ideas.admin_hide_comment, "current_user"), "ideas.curation.manage")
        self.assertEqual(_captured_permission(ideas.admin_list_comments, "current_user"), "ideas.curation.manage")
        self.assertEqual(_captured_permission(ideas.admin_restore_comment, "current_user"), "ideas.curation.manage")
        self.assertEqual(_captured_permission(ideas.admin_update_idea_roadmap, "current_user"), "ideas.roadmap.manage")
        self.assertEqual(_captured_permission(ideas.admin_list_versions, "_"), "admin.idea_versions.manage")
        self.assertEqual(_captured_permission(ideas.admin_create_version, "current_user"), "admin.idea_versions.manage")
        self.assertEqual(_captured_permission(ideas.admin_update_version, "current_user"), "admin.idea_versions.manage")
        self.assertEqual(_captured_permission(ideas.admin_delete_version, "current_user"), "admin.idea_versions.manage")


if __name__ == "__main__":
    unittest.main()
