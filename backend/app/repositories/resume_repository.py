from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.resume import Resume


class ResumePersistenceError(RuntimeError):
    """Raised when a resume cannot be safely persisted."""


class ResumeRepository:
    """Persistence operations for extracted resumes."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        user_id: int,
        extracted_text: str,
        page_count: int,
    ) -> Resume:
        resume = Resume(
            user_id=user_id,
            extracted_text=extracted_text,
            page_count=page_count,
            character_count=len(extracted_text),
        )
        self.session.add(resume)
        try:
            self.session.flush()
            self.session.refresh(resume)
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise ResumePersistenceError("Unable to save resume.") from exc
        return resume

    def list_for_user(
        self, user_id: int, offset: int, limit: int
    ) -> tuple[list[Resume], int]:
        ownership_filter = Resume.user_id == user_id
        total = self.session.scalar(
            select(func.count()).select_from(Resume).where(ownership_filter)
        )
        statement = (
            select(Resume)
            .where(ownership_filter)
            .order_by(Resume.created_at.desc(), Resume.id.desc())
            .offset(offset)
            .limit(limit)
        )
        resumes = list(self.session.execute(statement).scalars().all())
        return resumes, total or 0

    def get_for_user(self, resume_id: int, user_id: int) -> Resume | None:
        statement = select(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == user_id,
        )
        return self.session.execute(statement).scalar_one_or_none()

    def delete_for_user(self, resume_id: int, user_id: int) -> bool:
        statement = delete(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == user_id,
        )
        try:
            result = self.session.execute(statement)
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise
        return result.rowcount == 1
