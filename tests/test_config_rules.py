import os
import unittest
from unittest.mock import patch

os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_DB", "goia_test")
os.environ.setdefault("POSTGRES_USER", "goia")
os.environ.setdefault("POSTGRES_PASSWORD", "goia")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("FIRST_ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("FIRST_ADMIN_PASSWORD", "secret123")

from pydantic import ValidationError

from app.core.config import DEV_MODEL_ACCESS_CREDENTIALS_SECRET_KEY, Settings


BASE_ENV = {
    "POSTGRES_HOST": "localhost",
    "POSTGRES_DB": "goia_test",
    "POSTGRES_USER": "goia",
    "POSTGRES_PASSWORD": "goia",
    "REDIS_URL": "redis://localhost:6379/0",
    "FIRST_ADMIN_EMAIL": "admin@example.com",
    "FIRST_ADMIN_PASSWORD": "secret123",
    "APP_CONTEXT_PATH": "/api",
    "APP_VERSION": "0.1.0",
}


class ConfigRulesTests(unittest.TestCase):
    def build_settings(self, **overrides):
        env = {**BASE_ENV, **overrides}
        with patch.dict(os.environ, env, clear=True):
            return Settings(_env_file=None)

    def test_development_allows_missing_model_access_secret_with_dev_fallback(self):
        settings = self.build_settings(APP_ENV="development")

        self.assertEqual(
            settings.MODEL_ACCESS_CREDENTIALS_SECRET_KEY,
            DEV_MODEL_ACCESS_CREDENTIALS_SECRET_KEY,
        )
        self.assertEqual(settings.cors_origins, ["*"])

    def test_production_requires_model_access_credentials_secret_key(self):
        with self.assertRaises(ValidationError) as ctx:
            self.build_settings(
                APP_ENV="production",
                APP_CORS_ORIGINS="https://goia.example.gov.br",
            )

        self.assertIn("MODEL_ACCESS_CREDENTIALS_SECRET_KEY", str(ctx.exception))

    def test_production_requires_explicit_cors_origins(self):
        with self.assertRaises(ValidationError) as ctx:
            self.build_settings(
                APP_ENV="production",
                MODEL_ACCESS_CREDENTIALS_SECRET_KEY="credential-secret",
                APP_CORS_ORIGINS="",
            )

        self.assertIn("APP_CORS_ORIGINS", str(ctx.exception))

    def test_production_accepts_explicit_secure_settings(self):
        settings = self.build_settings(
            APP_ENV="production",
            MODEL_ACCESS_CREDENTIALS_SECRET_KEY="credential-secret",
            APP_CORS_ORIGINS="https://goia.example.gov.br, https://admin.example.gov.br",
        )

        self.assertEqual(settings.MODEL_ACCESS_CREDENTIALS_SECRET_KEY, "credential-secret")
        self.assertEqual(
            settings.cors_origins,
            ["https://goia.example.gov.br", "https://admin.example.gov.br"],
        )


if __name__ == "__main__":
    unittest.main()
