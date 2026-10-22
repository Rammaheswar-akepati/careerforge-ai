from __future__ import annotations

import atexit
import os
import shutil
import tempfile
from pathlib import Path

import pytest


_BACKEND_DIR = Path(__file__).resolve().parents[1]
_TEST_DATABASE_DIRECTORY = Path(
    tempfile.mkdtemp(prefix=".careerforge-test-", dir=_BACKEND_DIR)
)
_TEST_DATABASE_PATH = _TEST_DATABASE_DIRECTORY / "test.sqlite3"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DATABASE_PATH.as_posix()}"


def _cleanup_test_database() -> None:
    from app.db.session import get_engine, get_session_factory

    if get_engine.cache_info().currsize:
        get_engine().dispose()
        get_session_factory.cache_clear()
        get_engine.cache_clear()
    shutil.rmtree(_TEST_DATABASE_DIRECTORY, ignore_errors=True)


atexit.register(_cleanup_test_database)


def pytest_report_header(config: pytest.Config) -> str:
    return "Database: isolated temporary SQLite, migrated by Alembic; DATABASE_URL overridden"


def pytest_sessionstart(session: pytest.Session) -> None:
    from alembic import command
    from alembic.config import Config

    from app.db.session import get_engine

    engine = get_engine()
    active_database_path = Path(engine.url.database or "").resolve()
    if (
        engine.url.drivername != "sqlite"
        or active_database_path != _TEST_DATABASE_PATH.resolve()
    ):
        raise pytest.UsageError(
            "Refusing to run tests without the isolated temporary SQLite database."
        )
    print(f"Using isolated test database: SQLite at {_TEST_DATABASE_PATH}")

    alembic_config = Config(str(_BACKEND_DIR / "alembic.ini"))
    alembic_config.set_main_option(
        "script_location", str(_BACKEND_DIR / "alembic")
    )
    command.upgrade(alembic_config, "head")


def pytest_sessionfinish(
    session: pytest.Session, exitstatus: int
) -> None:
    _cleanup_test_database()