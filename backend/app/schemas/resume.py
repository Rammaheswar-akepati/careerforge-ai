from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeTextRead(BaseModel):
    """Extracted text returned for a resume PDF without persisting it."""

    text: str
    page_count: int


class ResumeRead(BaseModel):
    """Persisted resume fields returned after upload."""

    id: int
    extracted_text: str
    page_count: int
    character_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeSummaryRead(BaseModel):
    """Resume metadata returned in a paginated list."""

    id: int
    page_count: int
    character_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeListRead(BaseModel):
    """Paginated resumes belonging to the authenticated user."""

    items: list[ResumeSummaryRead]
    total: int
    page: int
    page_size: int
    total_pages: int
