import importlib
import os
import unittest
from unittest.mock import patch


BASE_ENV = {
    "POSTGRES_HOST": "localhost",
    "POSTGRES_DB": "goia_test",
    "POSTGRES_USER": "goia",
    "POSTGRES_PASSWORD": "goia",
    "REDIS_URL": "redis://localhost:6379/0",
    "FIRST_ADMIN_EMAIL": "admin@example.com",
    "FIRST_ADMIN_PASSWORD": "secret123",
    "MODEL_ACCESS_CREDENTIALS_SECRET_KEY": "credential-secret",
    "APP_CORS_ORIGINS": "https://goia.example.gov.br",
    "APP_CONTEXT_PATH": "/api",
    "APP_VERSION": "0.1.0",
}


class AppDocsRulesTests(unittest.TestCase):
    def load_main_with_env(self, **overrides):
        env = {**BASE_ENV, **overrides}
        with patch.dict(os.environ, env, clear=True):
            import app.core.config as config_module
            import app.main as main_module

            importlib.reload(config_module)
            return importlib.reload(main_module)

    def test_development_exposes_interactive_api_docs(self):
        main = self.load_main_with_env(APP_ENV="development", APP_CORS_ORIGINS="")
        route_paths = {route.path for route in main.app.routes}

        self.assertEqual(main.app.docs_url, "/docs")
        self.assertEqual(main.app.redoc_url, "/redoc")
        self.assertEqual(main.app.openapi_url, "/openapi.json")
        self.assertIn("/docs", route_paths)
        self.assertIn("/redoc", route_paths)
        self.assertIn("/openapi.json", route_paths)

    def test_production_disables_interactive_api_docs(self):
        main = self.load_main_with_env(APP_ENV="production")
        route_paths = {route.path for route in main.app.routes}

        self.assertIsNone(main.app.docs_url)
        self.assertIsNone(main.app.redoc_url)
        self.assertIsNone(main.app.openapi_url)
        self.assertNotIn("/docs", route_paths)
        self.assertNotIn("/redoc", route_paths)
        self.assertNotIn("/openapi.json", route_paths)


if __name__ == "__main__":
    unittest.main()
