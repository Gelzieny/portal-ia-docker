import os
import unittest


os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_DB", "goia_test")
os.environ.setdefault("POSTGRES_USER", "goia")
os.environ.setdefault("POSTGRES_PASSWORD", "goia")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("FIRST_ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("FIRST_ADMIN_PASSWORD", "secret123")

from app.services.migration_service import (
    _has_no_transaction_marker,
    _split_sql_statements,
    _strip_no_transaction_marker,
)


class MigrationServiceRulesTests(unittest.TestCase):
    def test_no_transaction_marker_does_not_skip_first_statement(self):
        sql = """-- NO_TRANSACTION
ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'gestor_produto';
SELECT 'ok';
"""

        self.assertTrue(_has_no_transaction_marker(sql))

        statements = _split_sql_statements(_strip_no_transaction_marker(sql))

        self.assertEqual(
            statements[0],
            "ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'gestor_produto'",
        )
        self.assertEqual(statements[1], "SELECT 'ok'")


if __name__ == "__main__":
    unittest.main()
