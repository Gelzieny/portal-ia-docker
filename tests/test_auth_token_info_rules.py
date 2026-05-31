import os
import unittest

import jwt
from fastapi import HTTPException


os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_DB", "goia_test")
os.environ.setdefault("POSTGRES_USER", "goia")
os.environ.setdefault("POSTGRES_PASSWORD", "goia")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("FIRST_ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("FIRST_ADMIN_PASSWORD", "secret123")

from app.models.auth import TokenInfoRequest
from app.routers.auth import get_token_info
from app.services.auth_service import AuthService


TEST_SECRET = "test-secret-with-at-least-32-bytes"


class AuthTokenInfoRulesTests(unittest.IsolatedAsyncioTestCase):
    async def test_token_info_returns_decoded_claims(self):
        token = jwt.encode(
            {"sub": "123", "name": "Ana", "email": "ana@example.com"},
            TEST_SECRET,
            algorithm="HS256",
        )

        response = await get_token_info(TokenInfoRequest(token=token))

        self.assertEqual(response.claims["sub"], "123")
        self.assertEqual(response.claims["name"], "Ana")
        self.assertEqual(response.claims["email"], "ana@example.com")

    def test_decode_access_token_accepts_bearer_prefix(self):
        token = jwt.encode({"sub": "456"}, TEST_SECRET, algorithm="HS256")

        claims = AuthService.decode_access_token(f"Bearer {token}")

        self.assertEqual(claims["sub"], "456")

    def test_decode_access_token_rejects_token_without_subject(self):
        token = jwt.encode({"name": "Ana"}, TEST_SECRET, algorithm="HS256")

        with self.assertRaises(HTTPException) as context:
            AuthService.decode_access_token(token)

        self.assertEqual(context.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
