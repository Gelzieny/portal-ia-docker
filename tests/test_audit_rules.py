import json
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_DB", "goia_test")
os.environ.setdefault("POSTGRES_USER", "goia")
os.environ.setdefault("POSTGRES_PASSWORD", "goia")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("FIRST_ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("FIRST_ADMIN_PASSWORD", "secret123")

from starlette.requests import Request
from starlette.responses import Response

from app.middleware.logging_middleware import LoggingMiddleware
from app.routers.audit import list_audit_logs
from app.services.audit_service import log_audit


def make_request(
    *,
    path: str = "/audit",
    headers: list[tuple[bytes, bytes]] | None = None,
    client: tuple[str, int] = ("10.0.0.10", 12345),
) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": headers or [],
        "query_string": b"",
        "client": client,
        "server": ("testserver", 80),
        "scheme": "http",
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    return Request(scope, receive)


class AuditRulesTests(unittest.IsolatedAsyncioTestCase):
    async def test_log_audit_redacts_sensitive_metadata_and_captures_client_context(self):
        request = make_request(
            headers=[
                (b"x-forwarded-for", b"203.0.113.10, 10.0.0.2"),
                (b"user-agent", b"GOIA Test Client"),
            ],
        )
        user_id = uuid4()
        entity_id = uuid4()

        with patch("app.services.audit_service.database.execute", new=AsyncMock()) as execute:
            await log_audit(
                user_id=user_id,
                action="TOKEN_TEST",
                entity="auth",
                entity_id=entity_id,
                metadata={"refresh_token": "secret", "safe": "ok"},
                request=request,
            )

        execute.assert_awaited_once()
        args = execute.await_args.args
        metadata = json.loads(args[5])
        self.assertEqual(metadata["refresh_token"], "[redacted]")
        self.assertEqual(metadata["safe"], "ok")
        self.assertEqual(args[6], "203.0.113.10")
        self.assertEqual(args[7], "GOIA Test Client")

    async def test_list_audit_logs_returns_details_and_uses_filters(self):
        audit_id = uuid4()
        user_id = uuid4()
        entity_id = uuid4()
        row = {
            "id": audit_id,
            "user_id": user_id,
            "user_name": "Ana",
            "user_email": "ana@example.com",
            "action": "MODEL_ACCESS_SECRET_REVEAL",
            "entity": "model_access_request",
            "entity_id": entity_id,
            "metadata": {"model_id": "model-1", "request_id": "req-1"},
            "ip_address": "203.0.113.10",
            "user_agent": "GOIA Test Client",
            "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        }

        with patch("app.routers.audit.database.fetchval", new=AsyncMock(return_value=1)) as fetchval, \
             patch("app.routers.audit.database.fetch", new=AsyncMock(return_value=[row])) as fetch:
            result = await list_audit_logs(
                page=1,
                page_size=10,
                search="ana",
                action="MODEL_ACCESS_SECRET_REVEAL",
                entity="model_access_request",
                user_id=user_id,
                date_from="2026-01-01",
                date_to="2026-01-31",
                _={"role": "admin"},
            )

        self.assertEqual(result.total, 1)
        self.assertEqual(result.items[0].details, "model_id=model-1 | request_id=req-1")
        self.assertEqual(result.items[0].user_agent, "GOIA Test Client")
        self.assertIn("%ana%", fetchval.await_args.args)
        self.assertIn("%ana%", fetch.await_args.args)

    async def test_logging_middleware_adds_and_reuses_request_id(self):
        request = make_request(headers=[(b"x-request-id", b"req-123")])
        middleware = LoggingMiddleware(app=lambda scope, receive, send: None)

        async def call_next(received_request):
            self.assertEqual(received_request.state.request_id, "req-123")
            return Response("ok")

        response = await middleware.dispatch(request, call_next)

        self.assertEqual(response.headers["X-Request-ID"], "req-123")


if __name__ == "__main__":
    unittest.main()
