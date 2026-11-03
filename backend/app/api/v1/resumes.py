from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.resume_repository import (
    ResumePersistenceError,
    ResumeRepository,
)
from app.schemas.resume import (
    ResumeListRead,
    ResumeRead,
    ResumeSummaryRead,
    ResumeTextRead,
)
from app.services.resume_service import (
    EmptyPdfError,
    EncryptedPdfError,
    ExtractedTextTooLargeError,
    InvalidPdfError,
    NoExtractableTextError,
    PdfProcessingLimitError,
    ResumeNotFoundError,
    ResumeTooLargeError,
    ResumeService,
    TooManyPdfPagesError,
    extract_resume_text,
)

router = APIRouter(
    prefix="/api/v1/resumes",
    tags=["resumes"],
    dependencies=[Depends(get_current_user)],
)


def get_resume_service(db: Session = Depends(get_db)) -> ResumeService:
    return ResumeService(ResumeRepository(db))


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


@router.post("", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeRead:
    """Extract and save resume text and metadata for the authenticated user."""
    try:
        resume = await service.create_resume(current_user.id, file)
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
    except ResumePersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save resume.",
        ) from exc
    finally:
        await file.close()

    return resume


@router.get("", response_model=ResumeListRead)
def list_resumes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeListRead:
    """List metadata for the authenticated user's resumes."""
    resume_page = service.list_resumes(current_user.id, page, page_size)
    return ResumeListRead(
        items=[
            ResumeSummaryRead.model_validate(resume)
            for resume in resume_page.items
        ],
        total=resume_page.total,
        page=resume_page.page,
        page_size=resume_page.page_size,
        total_pages=resume_page.total_pages,
    )


@router.get("/{resume_id}", response_model=ResumeRead)
def read_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeRead:
    """Return one resume only when it belongs to the authenticated user."""
    try:
        return service.get_resume(current_user.id, resume_id)
    except ResumeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        ) from exc


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> Response:
    """Permanently delete one resume belonging to the authenticated user."""
    try:
        service.delete_resume(current_user.id, resume_id)
    except ResumeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
