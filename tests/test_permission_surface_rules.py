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

from app.core.deps import get_current_user
from app.routers import docs, mcp, news, prompts, users


def _captured_permissions(endpoint, param_name):
    dependency = inspect.signature(endpoint).parameters[param_name].default.dependency
    values = []
    for cell in dependency.__closure__ or []:
        content = cell.cell_contents
        if isinstance(content, tuple):
            values.extend(content)
        elif isinstance(content, str):
            values.append(content)
    return set(values)


class PermissionSurfaceRulesTests(unittest.TestCase):
    def test_user_lookup_by_codg_usuario_requires_authentication_only(self):
        dependency = inspect.signature(users.get_user_by_codg_usuario).parameters["_"].default.dependency

        self.assertIs(dependency, get_current_user)

    def test_prompt_categories_support_user_and_admin_surfaces(self):
        self.assertEqual(
            _captured_permissions(prompts.list_categories, "_"),
            {
                "prompts.library.view",
                "prompts.my.view",
                "admin.prompts.manage",
                "admin.prompt_curation.manage",
            },
        )

    def test_prompt_review_moderation_supports_prompt_admin_and_curation_admin(self):
        expected = {"admin.prompts.manage", "admin.prompt_curation.manage"}

        self.assertEqual(_captured_permissions(prompts.admin_list_reviews, "_"), expected)
        self.assertEqual(_captured_permissions(prompts.admin_approve_review, "_"), expected)
        self.assertEqual(_captured_permissions(prompts.admin_delete_review, "_"), expected)

    def test_mcp_categories_support_catalog_and_admin_surfaces(self):
        self.assertEqual(
            _captured_permissions(mcp.list_categories, "_"),
            {"mcp.catalog.view", "admin.mcp.manage"},
        )

    def test_docs_portal_endpoints_support_portal_and_admin_surfaces(self):
        expected = {"docs.portal.view", "admin.docs.manage"}

        self.assertEqual(_captured_permissions(docs.get_sections, "current_user"), expected)
        self.assertEqual(_captured_permissions(docs.get_article, "current_user"), expected)
        self.assertEqual(_captured_permissions(docs.search_docs, "current_user"), expected)

    def test_news_portal_endpoints_support_portal_and_admin_surfaces(self):
        expected = {"news.portal.view", "admin.news.manage"}

        self.assertEqual(_captured_permissions(news.list_news, "_"), expected)
        self.assertEqual(_captured_permissions(news.get_news, "_"), expected)


if __name__ == "__main__":
    unittest.main()
