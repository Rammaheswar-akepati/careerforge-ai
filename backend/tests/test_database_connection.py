"""Integration test for the configured PostgreSQL connection."""

import os
import unittest

from sqlalchemy import text

from app.db.session import get_engine


@unittest.skipUnless(
    os.getenv("DATABASE_URL"),
    "DATABASE_URL is not set; skipping PostgreSQL connectivity test.",
)
class DatabaseConnectionTest(unittest.TestCase):
    """Verify a configured database accepts a harmless query."""

    def test_select_one(self) -> None:
        with get_engine().connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar_one()

        self.assertEqual(result, 1)
