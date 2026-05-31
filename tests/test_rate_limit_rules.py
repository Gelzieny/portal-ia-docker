import json
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

from starlette.requests import Request

from app.core.config import settings
from app.middleware.rate_limit_middleware import _select_policy


def make_request(
    path: str,
    *,
    method: str = "POST",
    body: dict | None = None,
    authorization: str | None = None,
) -> Request:
    headers = []
    if authorization:
        headers.append((b"authorization", authorization.encode()))
    raw_body = json.dumps(body or {}).encode()
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": headers,
        "query_string": b"",
        "client": ("10.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
    }

    async def receive():
        return {"type": "http.request", "body": raw_body, "more_body": False}

    return Request(scope, receive)


class RateLimitRulesTests(unittest.IsolatedAsyncioTestCase):
    async def test_unauthenticated_api_request_uses_default_ip_policy(self):
        request = make_request(
            "/unauthenticated-request",
            body={"email": "  ANA@EXAMPLE.COM  ", "password": "secret"},
        )

        key, limit, window = await _select_policy(request)

        self.assertEqual(key, "rate:ip:10.0.0.1")
        self.assertEqual(limit, settings.RATE_LIMIT_DEFAULT_LIMIT)
        self.assertEqual(window, settings.RATE_LIMIT_DEFAULT_WINDOW_SECONDS)

    async def test_reveal_secret_uses_specific_user_policy(self):
        request = make_request(
            "/model-access/my-requests/request-1/credentials/reveal-secret",
            authorization="Bearer access-token",
        )

        with patch("app.middleware.rate_limit_middleware.jwt.decode", return_value={"sub": "user-1", "role": "servidor"}):
            key, limit, window = await _select_policy(request)

        self.assertEqual(key, "rate:reveal-secret:user-1")
        self.assertEqual(limit, settings.RATE_LIMIT_REVEAL_SECRET_LIMIT)
        self.assertEqual(window, settings.RATE_LIMIT_REVEAL_SECRET_WINDOW_SECONDS)

    async def test_admin_mutation_uses_admin_policy(self):
        request = make_request(
            "/users/user-1",
            method="PUT",
            authorization="Bearer access-token",
        )

        with patch("app.middleware.rate_limit_middleware.jwt.decode", return_value={"sub": "admin-1", "role": "admin"}):
            key, limit, window = await _select_policy(request)

        self.assertEqual(key, "rate:admin-mutation:admin-1")
        self.assertEqual(limit, settings.RATE_LIMIT_ADMIN_MUTATION_LIMIT)
        self.assertEqual(window, settings.RATE_LIMIT_ADMIN_MUTATION_WINDOW_SECONDS)


if __name__ == "__main__":
    unittest.main()
