from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.v1.auth import get_current_user
from app.schemas.resume import ResumeTextRead
from app.services.resume_service import (
    EmptyPdfError,
    EncryptedPdfError,
    ExtractedTextTooLargeError,
    InvalidPdfError,
    NoExtractableTextError,
    PdfProcessingLimitError,
    ResumeTooLargeError,
    TooManyPdfPagesError,
    extract_resume_text,
)

router = APIRouter(
    prefix="/api/v1/resumes",
    tags=["resumes"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/extract-text", response_model=ResumeTextRead)
async def extract_resume_pdf_text(
    file: UploadFile = File(...),
) -> ResumeTextRead:
    """Extract text from an authenticated PDF upload without saving it."""
    try:
        result = await extract_resume_text(file)
    except ResumeTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="PDF must not exceed 5 MB.",
        ) from exc
    except ExtractedTextTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Extracted PDF text exceeds the supported size.",
        ) from exc
    except TooManyPdfPagesError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="PDF must not contain more than 100 pages.",
        ) from exc
    except PdfProcessingLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="PDF exceeds supported processing limits.",
        ) from exc
    except EmptyPdfError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="PDF upload is empty.",
        ) from exc
    except EncryptedPdfError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Encrypted PDFs are not supported.",
        ) from exc
    except NoExtractableTextError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="PDF contains no extractable text.",
        ) from exc
    except InvalidPdfError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Upload is not a valid, readable PDF.",
        ) from exc
    finally:
        await file.close()

    return ResumeTextRead(text=result.text, page_count=result.page_count)
