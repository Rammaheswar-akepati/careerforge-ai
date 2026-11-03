from __future__ import annotations

import zlib
from collections.abc import Generator
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from sqlalchemy import inspect, select

from app.db.session import get_engine, get_session_factory
from app.main import app
from app.models.resume import Resume
from app.services.resume_service import (
    MAX_UPLOAD_BYTES,
    MAX_DECODED_STREAM_BYTES,
    UPLOAD_READ_CHUNK_BYTES,
    ResumeTooLargeError,
    read_bounded_upload,
)


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def create_authenticated_user(client: TestClient) -> dict[str, str]:
    email = f"resume-{uuid4().hex}@example.com"
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "full_name": "Resume Test User",
        },
    )
    assert registration.status_code == 201, registration.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPass123!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_pdf_with_stream(stream: bytes, compressed: bool = False) -> bytes:
    filter_entry = b" /Filter /FlateDecode" if compressed else b""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + filter_entry
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_number, object_body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_number} 0 obj\n".encode("ascii"))
        pdf.extend(object_body)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)


def create_text_pdf(text: str = "Python and FastAPI experience") -> bytes:
    escaped_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({escaped_text}) Tj ET".encode("ascii")
    return create_pdf_with_stream(stream)


def create_highly_compressed_pdf() -> bytes:
    compressed_stream = zlib.compress(b" " * (MAX_DECODED_STREAM_BYTES + 1))
    return create_pdf_with_stream(compressed_stream, compressed=True)


def create_encrypted_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.encrypt("private-password")
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def create_textless_pdf(page_count: int = 1) -> bytes:
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=612, height=792)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def upload_pdf(
    client: TestClient,
    headers: dict[str, str],
    content: bytes,
    filename: str = "resume.pdf",
) -> tuple[int, dict[str, object]]:
    response = client.post(
        "/api/v1/resumes/extract-text",
        headers=headers,
        files={"file": (filename, content, "application/pdf")},
    )
    return response.status_code, response.json()


def test_extract_text_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/resumes/extract-text",
        files={"file": ("resume.pdf", create_text_pdf(), "application/pdf")},
    )

    assert response.status_code == 401


def test_extract_text_from_pdf_without_persisting_it(client: TestClient) -> None:
    headers = create_authenticated_user(client)

    status_code, payload = upload_pdf(client, headers, create_text_pdf())

    assert status_code == 200
    assert payload == {
        "text": "Python and FastAPI experience",
        "page_count": 1,
    }
    assert inspect(get_engine()).has_table("resumes")
    current_user_response = client.get("/api/v1/auth/me", headers=headers)
    assert current_user_response.status_code == 200
    user_id = current_user_response.json()["id"]
    with get_session_factory()() as session:
        assert (
            session.execute(select(Resume).where(Resume.user_id == user_id))
            .scalars()
            .all()
            == []
        )


@pytest.mark.parametrize(
    ("content", "expected_detail"),
    [
        (b"", "PDF upload is empty."),
        (b"not a PDF", "Upload is not a valid, readable PDF."),
        (b"%PDF-1.4\nnot-a-valid-xref", "Upload is not a valid, readable PDF."),
        (create_textless_pdf(), "PDF contains no extractable text."),
        (create_encrypted_pdf(), "Encrypted PDFs are not supported."),
    ],
    ids=["empty", "not-pdf", "malformed-pdf", "textless", "encrypted"],
)
def test_invalid_or_non_text_pdfs_are_rejected_safely(
    client: TestClient, content: bytes, expected_detail: str
) -> None:
    headers = create_authenticated_user(client)

    status_code, payload = upload_pdf(client, headers, content)

    assert status_code == 422
    assert payload == {"detail": expected_detail}
    assert "private-password" not in str(payload)


def test_oversized_pdf_is_rejected(client: TestClient) -> None:
    headers = create_authenticated_user(client)
    content = create_text_pdf() + b"x" * (MAX_UPLOAD_BYTES + 1)

    status_code, payload = upload_pdf(client, headers, content)

    assert status_code == 413
    assert payload == {"detail": "PDF must not exceed 5 MB."}


def test_pdf_page_limit_is_enforced(client: TestClient) -> None:
    headers = create_authenticated_user(client)

    status_code, payload = upload_pdf(client, headers, create_textless_pdf(page_count=101))

    assert status_code == 422
    assert payload == {"detail": "PDF must not contain more than 100 pages."}


def test_extracted_text_limit_is_enforced(client: TestClient) -> None:
    headers = create_authenticated_user(client)
    oversized_text = "A" * 200_001

    status_code, payload = upload_pdf(client, headers, create_text_pdf(oversized_text))

    assert status_code == 413
    assert payload == {
        "detail": "Extracted PDF text exceeds the supported size."
    }


def test_pdf_decompression_limit_is_enforced(client: TestClient) -> None:
    headers = create_authenticated_user(client)

    status_code, payload = upload_pdf(client, headers, create_highly_compressed_pdf())

    assert status_code == 422
    assert payload == {"detail": "PDF exceeds supported processing limits."}


class TrackingUpload:
    def __init__(self, content: bytes) -> None:
        self.content = content
        self.position = 0
        self.requested_sizes: list[int] = []

    async def read(self, size: int = -1) -> bytes:
        self.requested_sizes.append(size)
        chunk = self.content[self.position : self.position + size]
        self.position += len(chunk)
        return chunk


@pytest.mark.anyio
async def test_upload_size_is_checked_during_bounded_reads() -> None:
    upload = TrackingUpload(b"x" * (MAX_UPLOAD_BYTES + 1))

    with pytest.raises(ResumeTooLargeError):
        await read_bounded_upload(upload)  # type: ignore[arg-type]

    assert upload.position == MAX_UPLOAD_BYTES + 1
    assert all(0 < size <= UPLOAD_READ_CHUNK_BYTES for size in upload.requested_sizes)
    assert len(upload.requested_sizes) > 1


@pytest.mark.anyio
async def test_upload_at_limit_is_accepted_by_bounded_reader() -> None:
    upload = TrackingUpload(b"x" * MAX_UPLOAD_BYTES)

    content = await read_bounded_upload(upload)  # type: ignore[arg-type]

    assert len(content) == MAX_UPLOAD_BYTES
    assert upload.position == MAX_UPLOAD_BYTES
    assert upload.requested_sizes[-1] == 1
