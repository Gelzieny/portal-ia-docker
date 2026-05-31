import logging
import os
import re
from app.core import database

logger = logging.getLogger("goia.migrations")

MIGRATIONS_DIR = "docs/migrations"


def _split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []
    i = 0
    length = len(sql)
    in_single_quote = False
    in_double_quote = False
    in_line_comment = False
    in_block_comment = False
    dollar_quote: str | None = None

    while i < length:
        char = sql[i]
        next_char = sql[i + 1] if i + 1 < length else ""

        if in_line_comment:
            buffer.append(char)
            if char == "\n":
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            buffer.append(char)
            if char == "*" and next_char == "/":
                buffer.append(next_char)
                i += 2
                in_block_comment = False
            else:
                i += 1
            continue

        if dollar_quote is not None:
            if sql.startswith(dollar_quote, i):
                buffer.append(dollar_quote)
                i += len(dollar_quote)
                dollar_quote = None
            else:
                buffer.append(char)
                i += 1
            continue

        if in_single_quote:
            buffer.append(char)
            if char == "'":
                if next_char == "'":
                    buffer.append(next_char)
                    i += 2
                else:
                    in_single_quote = False
                    i += 1
            else:
                i += 1
            continue

        if in_double_quote:
            buffer.append(char)
            if char == '"':
                if next_char == '"':
                    buffer.append(next_char)
                    i += 2
                else:
                    in_double_quote = False
                    i += 1
            else:
                i += 1
            continue

        if sql.startswith("--", i):
            buffer.append("--")
            i += 2
            in_line_comment = True
            continue

        if sql.startswith("/*", i):
            buffer.append("/*")
            i += 2
            in_block_comment = True
            continue

        if char == "'":
            buffer.append(char)
            in_single_quote = True
            i += 1
            continue

        if char == '"':
            buffer.append(char)
            in_double_quote = True
            i += 1
            continue

        if char == "$":
            match = re.match(r"\$[A-Za-z_][A-Za-z0-9_]*\$|\$\$", sql[i:])
            if match:
                dollar_quote = match.group(0)
                buffer.append(dollar_quote)
                i += len(dollar_quote)
                continue

        if char == ";":
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
            i += 1
            continue

        buffer.append(char)
        i += 1

    statement = "".join(buffer).strip()
    if statement:
        statements.append(statement)

    return statements


def _has_no_transaction_marker(sql: str) -> bool:
    return re.search(r"(?m)^\s*--\s*NO_TRANSACTION\s*$", sql) is not None


def _strip_no_transaction_marker(sql: str) -> str:
    return re.sub(r"(?m)^\s*--\s*NO_TRANSACTION\s*\n?", "", sql, count=1)


class MigrationService:
    @staticmethod
    async def init_migrations_table():
        """Cria a tabela de controle de migrações se não existir."""
        await database.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                executed_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

    @staticmethod
    async def get_executed_migrations():
        """Retorna uma lista de nomes de migrações já executadas."""
        rows = await database.fetch("SELECT name FROM _migrations ORDER BY id")
        return [row["name"] for row in rows]

    @staticmethod
    async def run_migrations():
        """Lê os arquivos SQL de migração e executa os pendentes."""
        await MigrationService.init_migrations_table()
        
        executed = await MigrationService.get_executed_migrations()
        
        if not os.path.exists(MIGRATIONS_DIR):
            logger.warning(f"Diretório de migrações não encontrado: {MIGRATIONS_DIR}")
            return {"message": "Diretório de migrações não encontrado", "executed": []}

        files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql")])
        pending = [f for f in files if f not in executed]

        if not pending:
            return {"message": "Sistema já está atualizado", "executed": []}

        results = []
        for filename in pending:
            filepath = os.path.join(MIGRATIONS_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Verifica se a migração deve rodar sem transação
                no_transaction = _has_no_transaction_marker(content)
                
                logger.info(f"Executando migração: {filename} (no_transaction={no_transaction})")
                
                if no_transaction:
                    content = _strip_no_transaction_marker(content)
                    for statement in _split_sql_statements(content):
                        await database.execute(statement)
                else:
                    # Executa em transação
                    async with database.get_connection() as conn:
                        async with conn.transaction():
                            await conn.execute(content)
                
                await database.execute("INSERT INTO _migrations (name) VALUES ($1)", filename)
                results.append(filename)
                logger.info(f"Migração {filename} concluída com sucesso.")
            
            except Exception as e:
                logger.exception(f"Erro ao executar migração {filename}")
                return {
                    "error": str(e),
                    "filename": filename,
                    "executed_until": results
                }

        return {
            "message": f"{len(results)} migrações executadas com sucesso",
            "executed": results
        }
