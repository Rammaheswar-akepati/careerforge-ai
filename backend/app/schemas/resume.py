from pydantic import BaseModel


class ResumeTextRead(BaseModel):
    """Extracted text returned for a resume PDF without persisting it."""

    text: str
    page_count: int
