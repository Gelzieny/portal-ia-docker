import argparse
import asyncio
import sys
from pathlib import Path

import asyncpg

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings


MIGRATIONS_DIR = Path("docs/migrations")


def migration_names() -> list[str]:
    return sorted(path.name for path in MIGRATIONS_DIR.glob("*.sql"))


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Registra migrações já aplicadas em _migrations sem reexecutar SQL."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Insere as migrações ausentes em _migrations.",
    )
    args = parser.parse_args()

    names = migration_names()
    if not names:
        raise SystemExit(f"Nenhuma migração encontrada em {MIGRATIONS_DIR}")

    conn = await asyncpg.connect(dsn=settings.DATABASE_URL)
    try:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS _migrations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                executed_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )
        existing_rows = await conn.fetch("SELECT name FROM _migrations")
        existing = {row["name"] for row in existing_rows}
        missing = [name for name in names if name not in existing]

        if not missing:
            print("Todas as migrações já estão registradas.")
            return

        print("Migrações ausentes em _migrations:")
        for name in missing:
            print(f" - {name}")

        if not args.apply:
            print("\nDry-run apenas. Rode novamente com --apply para registrar.")
            return

        async with conn.transaction():
            await conn.executemany(
                """
                INSERT INTO _migrations (name)
                VALUES ($1)
                ON CONFLICT (name) DO NOTHING
                """,
                [(name,) for name in missing],
            )

        print(f"\nRegistradas {len(missing)} migrações em _migrations.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
