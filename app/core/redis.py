import redis.asyncio as aioredis
from app.core.config import settings

_client: aioredis.Redis | None = None


async def init_redis() -> None:
  global _client
  _client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def close_redis() -> None:
  global _client
  if _client:
    await _client.aclose()
    _client = None


def get_redis() -> aioredis.Redis:
  if _client is None:
    raise RuntimeError("Redis client not initialized")
  return _client
