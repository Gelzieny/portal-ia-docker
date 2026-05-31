import logging

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger("goia.ratelimit")


def _extract_token_payload(request: Request) -> dict | None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        return jwt.decode(auth[7:], options={"verify_signature": False})
    except jwt.PyJWTError:
        return None


def _extract_user_id(request: Request) -> str | None:
    payload = _extract_token_payload(request)
    if payload:
        return payload.get("sub")
    return None


async def _select_policy(request: Request) -> tuple[str, int, int]:
    path = request.url.path
    method = request.method.upper()
    ip = request.client.host if request.client else "unknown"

    if path.endswith("/credentials/reveal-secret") and method == "POST":
        user_id = _extract_user_id(request)
        principal = user_id or ip
        return (
            f"rate:reveal-secret:{principal}",
            settings.RATE_LIMIT_REVEAL_SECRET_LIMIT,
            settings.RATE_LIMIT_REVEAL_SECRET_WINDOW_SECONDS,
        )

    payload = _extract_token_payload(request)
    role = payload.get("role") if payload else None
    if path.startswith("/") and method in {"POST", "PUT", "PATCH", "DELETE"} and role in {
        "admin",
        "gestor",
        "curador",
        "curador_modelos",
        "gestor_produto",
    }:
        user_id = payload.get("sub") if payload else None
        principal = user_id or ip
        return (
            f"rate:admin-mutation:{principal}",
            settings.RATE_LIMIT_ADMIN_MUTATION_LIMIT,
            settings.RATE_LIMIT_ADMIN_MUTATION_WINDOW_SECONDS,
        )

    user_id = payload.get("sub") if payload else None
    if user_id:
        key = f"rate:user:{user_id}"
    else:
        key = f"rate:ip:{ip}"
    return key, settings.RATE_LIMIT_DEFAULT_LIMIT, settings.RATE_LIMIT_DEFAULT_WINDOW_SECONDS


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        try:
            from app.core.redis import get_redis

            key, limit, window = await _select_policy(request)
            redis = get_redis()
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, window)
            if current > limit:
                logger.warning("Rate limit excedido: key=%s count=%d limit=%d", key, current, limit)
                return JSONResponse(
                    status_code=429,
                    headers={"Retry-After": str(window)},
                    content={"detail": "Muitas requisicoes. Tente novamente em instantes."},
                )
        except Exception:
            pass

        return await call_next(request)
