from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from io import BytesIO
from math import ceil

from fastapi import UploadFile
from pypdf import PdfReader, apply_configuration
from pypdf.errors import LimitReachedError, PyPdfError

from app.models.resume import Resume
from app.repositories.resume_repository import ResumeRepository

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_PDF_PAGES = 100
MAX_EXTRACTED_TEXT_CHARACTERS = 200_000
MAX_DECODED_STREAM_BYTES = 5 * 1024 * 1024
MAX_STREAM_DECODING_WORK_BYTES = 20 * 1024 * 1024
UPLOAD_READ_CHUNK_BYTES = 64 * 1024


class ResumeExtractionError(ValueError):
    """Base error for a PDF upload that cannot be safely extracted."""


class ResumeTooLargeError(ResumeExtractionError):
    """Raised when an upload exceeds the configured byte limit."""


class EmptyPdfError(ResumeExtractionError):
    """Raised when an upload contains no PDF data."""


class InvalidPdfError(ResumeExtractionError):
    """Raised when an upload is not a readable PDF."""


class EncryptedPdfError(ResumeExtractionError):
    """Raised when a PDF requires a password."""


class TooManyPdfPagesError(ResumeExtractionError):
    """Raised when a PDF exceeds the configured page limit."""


class NoExtractableTextError(ResumeExtractionError):
    """Raised when a PDF contains no extractable text."""


class ExtractedTextTooLargeError(ResumeExtractionError):
    """Raised when extracted text exceeds the configured character limit."""


class PdfProcessingLimitError(ResumeExtractionError):
    """Raised when a PDF exceeds a parser resource limit."""


class ResumeNotFoundError(LookupError):
    """Raised when the requested resume does not belong to the user."""


@dataclass(frozen=True, slots=True)
class ExtractedResumeText:
    text: str
    page_count: int


@dataclass(frozen=True, slots=True)
class ResumePage:
    items: list[Resume]
    total: int
    page: int
    page_size: int
    total_pages: int


class ResumeService:
    """Extract and persist resumes for their authenticated owners."""

    def __init__(self, repository: ResumeRepository) -> None:
        self.repository = repository

    async def create_resume(self, user_id: int, upload: UploadFile) -> Resume:
        extracted = await extract_resume_text(upload)
        return self.repository.create(
            user_id=user_id,
            extracted_text=extracted.text,
            page_count=extracted.page_count,
        )

    def list_resumes(
        self, user_id: int, page: int, page_size: int
    ) -> ResumePage:
        resumes, total = self.repository.list_for_user(
            user_id=user_id,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        return ResumePage(
            items=resumes,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total else 0,
        )

    def get_resume(self, user_id: int, resume_id: int) -> Resume:
        resume = self.repository.get_for_user(resume_id, user_id)
        if resume is None:
            raise ResumeNotFoundError
        return resume


async def read_bounded_upload(upload: UploadFile) -> bytes:
    """Read at most the configured limit plus one byte from the upload."""
    content = bytearray()
    while True:
        remaining_with_overflow_byte = MAX_UPLOAD_BYTES + 1 - len(content)
        chunk = await upload.read(min(UPLOAD_READ_CHUNK_BYTES, remaining_with_overflow_byte))
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > MAX_UPLOAD_BYTES:
            raise ResumeTooLargeError

    if not content:
        raise EmptyPdfError
    return bytes(content)


async def extract_resume_text(upload: UploadFile) -> ExtractedResumeText:
    """Extract bounded text from a PDF upload entirely in memory."""
    pdf_bytes = await read_bounded_upload(upload)
    try:
        with apply_configuration(
            jbig2_maximum_output_length=MAX_DECODED_STREAM_BYTES,
            lzw_maximum_output_length=MAX_DECODED_STREAM_BYTES,
            run_length_maximum_output_length=MAX_DECODED_STREAM_BYTES,
            zlib_maximum_output_length=MAX_DECODED_STREAM_BYTES,
            brotli_maximum_output_length=MAX_DECODED_STREAM_BYTES,
            stream_decoding_work_maximum_length=MAX_STREAM_DECODING_WORK_BYTES,
        ):
            reader = PdfReader(
                BytesIO(pdf_bytes),
                strict=True,
                root_object_recovery_limit=10_000,
                xref_stream_maximum_entries=100_000,
            )
            if reader.is_encrypted:
                raise EncryptedPdfError

            pages = reader.pages
            page_count = len(pages)
            if page_count > MAX_PDF_PAGES:
                raise TooManyPdfPagesError

            text_parts: list[str] = []
            extracted_characters = 0
            for page in pages:
                page_text = page.extract_text() or ""
                extracted_characters += len(page_text)
                if extracted_characters > MAX_EXTRACTED_TEXT_CHARACTERS:
                    raise ExtractedTextTooLargeError
                if page_text.strip():
                    text_parts.append(page_text.strip())
    except ResumeExtractionError:
        raise
    except LimitReachedError as exc:
        raise PdfProcessingLimitError from exc
    except (PyPdfError, ValueError, EOFError, IndexError, KeyError, struct.error, zlib.error) as exc:
        raise InvalidPdfError from exc

    extracted_text = "\n".join(text_parts).strip()
    if not extracted_text:
        raise NoExtractableTextError
    return ExtractedResumeText(text=extracted_text, page_count=page_count)
