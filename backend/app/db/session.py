"""SQLAlchemy engine and request-scoped session helpers."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


class DatabaseConfigurationError(RuntimeError):
    """Raised when a database operation is requested without a configured URL."""


def get_database_url() -> str:
    """Return the configured database URL or explain what is missing."""
    database_url = get_settings().database_url
    if not database_url:
        raise DatabaseConfigurationError(
            "DATABASE_URL must be set before using database functionality."
        )
    return database_url


@lru_cache
def get_engine() -> Engine:
    """Create one pooled engine for the configured PostgreSQL database."""
    return create_engine(get_database_url(), pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Create the reusable SQLAlchemy session factory."""
    return sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """Provide a request-scoped database session for FastAPI routes."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
