from __future__ import annotations

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
