import asyncpg
from asyncpg import Pool, Connection
from app.core.config import settings

_pool: Pool | None = None

async def init_pool() -> None:
  global _pool
  _pool = await asyncpg.create_pool(
    dsn=settings.DATABASE_URL,
    min_size=2,
    max_size=10,
    command_timeout=60,
  )

async def close_pool() -> None:
  global _pool
  if _pool:
    await _pool.close()
    _pool = None


def get_pool() -> Pool:
  if _pool is None:
    raise RuntimeError("Database pool not initialized")
  return _pool


class get_connection:
  """Async context manager que retorna uma conexão do pool."""

  async def __aenter__(self) -> Connection:
    self._conn = await get_pool().acquire()
    return self._conn

  async def __aexit__(self, exc_type, exc, tb) -> None:
    await get_pool().release(self._conn)


async def execute(query: str, *args) -> str:
  async with get_connection() as conn:
    return await conn.execute(query, *args)


async def fetch(query: str, *args) -> list[asyncpg.Record]:
  async with get_connection() as conn:
    return await conn.fetch(query, *args)


async def fetchrow(query: str, *args) -> asyncpg.Record | None:
  async with get_connection() as conn:
    return await conn.fetchrow(query, *args)


async def fetchval(query: str, *args):
  async with get_connection() as conn:
    return await conn.fetchval(query, *args)
