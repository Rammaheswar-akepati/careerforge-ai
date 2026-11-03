from __future__ import annotations

from collections.abc import Generator
from sqlite3 import Connection as SQLiteConnection

import pytest
from sqlalchemy import create_engine, delete, event, inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import get_engine
from app.models.resume import Resume
from app.models.user import User


@pytest.fixture()
def sqlite_resume_engine() -> Generator[Engine, None, None]:
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(
        dbapi_connection: SQLiteConnection, _connection_record: object
    ) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


def test_alembic_upgrade_creates_resume_schema() -> None:
    inspector = inspect(get_engine())

    assert inspector.has_table("resumes")
    columns = {column["name"]: column for column in inspector.get_columns("resumes")}
    assert set(columns) == {
        "id",
        "user_id",
        "extracted_text",
        "page_count",
        "character_count",
        "created_at",
    }
    assert columns["id"]["nullable"] is False
    assert columns["user_id"]["nullable"] is False
    assert columns["extracted_text"]["nullable"] is False
    assert columns["page_count"]["nullable"] is False
    assert columns["character_count"]["nullable"] is False
    assert columns["created_at"]["nullable"] is False
    assert columns["created_at"]["default"] is not None
    assert inspector.get_pk_constraint("resumes")["constrained_columns"] == ["id"]
    assert inspector.get_foreign_keys("resumes") == [
        {
            "name": None,
            "constrained_columns": ["user_id"],
            "referred_schema": None,
            "referred_table": "users",
            "referred_columns": ["id"],
            "options": {"ondelete": "CASCADE"},
        }
    ]
    assert inspector.get_indexes("resumes") == [
        {
            "name": "ix_resumes_user_id",
            "column_names": ["user_id"],
            "unique": 0,
            "dialect_options": {},
        }
    ]


def test_user_can_own_multiple_resumes(sqlite_resume_engine: Engine) -> None:
    with Session(sqlite_resume_engine) as session:
        user = _create_user(session, "resume-owner@example.com")
        first_resume = Resume(
            extracted_text="First resume",
            page_count=1,
            character_count=12,
        )
        second_resume = Resume(
            extracted_text="Second resume",
            page_count=2,
            character_count=13,
        )
        user.resumes.extend([first_resume, second_resume])
        session.commit()

        assert first_resume.user_id == user.id
        assert second_resume.user_id == user.id
        assert first_resume.user is user
        assert second_resume.user is user
        assert {resume.id for resume in user.resumes} == {
            first_resume.id,
            second_resume.id,
        }


def test_sqlite_cascade_deletes_resumes_when_user_is_deleted(
    sqlite_resume_engine: Engine,
) -> None:
    with sqlite_resume_engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1

    with Session(sqlite_resume_engine) as session:
        user = _create_user(session, "cascade-owner@example.com")
        resume = Resume(
            user=user,
            extracted_text="Resume content",
            page_count=1,
            character_count=15,
        )
        session.add(resume)
        session.commit()
        user_id = user.id
        resume_id = resume.id

    with sqlite_resume_engine.begin() as connection:
        connection.execute(delete(User).where(User.id == user_id))

    with Session(sqlite_resume_engine) as session:
        assert session.get(User, user_id) is None
        assert session.get(Resume, resume_id) is None
        assert session.execute(select(Resume)).scalars().all() == []


def _create_user(session: Session, email: str) -> User:
    user = User(
        email=email,
        password_hash="test-hash",
        full_name="Resume Test User",
    )
    session.add(user)
    session.flush()
    return user
