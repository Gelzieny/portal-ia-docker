import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("goia.requests")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        duration_ms = (time.perf_counter() - start) * 1000

        # user_id via header injetado pelo token (opcional, best-effort)
        user_id = request.state.__dict__.get("user_id", "-")

        logger.info(
            "%s %s %d %.1fms user=%s request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            user_id,
            request_id,
        )
        return response
