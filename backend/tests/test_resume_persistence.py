from __future__ import annotations

from collections.abc import Generator
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db.session import get_session_factory
from app.main import app
from app.models.resume import Resume
from app.services.resume_service import MAX_UPLOAD_BYTES


EXPECTED_TEXT = "Python and FastAPI experience"


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def create_authenticated_user(client: TestClient) -> tuple[dict[str, str], int]:
    email = f"resume-persistence-{uuid4().hex}@example.com"
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "full_name": "Resume Persistence User",
        },
    )
    assert registration.status_code == 201, registration.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPass123!"},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    current_user = client.get("/api/v1/auth/me", headers=headers)
    assert current_user.status_code == 200, current_user.text
    return headers, current_user.json()["id"]


def create_text_pdf(text: str = EXPECTED_TEXT) -> bytes:
    escaped_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({escaped_text}) Tj ET".encode("ascii")
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


def create_encrypted_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.encrypt("private-password")
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def create_textless_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def post_resume(
    client: TestClient,
    headers: dict[str, str] | None,
    content: bytes,
) -> tuple[int, dict[str, object]]:
    response = client.post(
        "/api/v1/resumes",
        headers=headers,
        files={"file": ("unpersisted-original-name.pdf", content, "application/pdf")},
    )
    return response.status_code, response.json()


def resume_rows_for_user(user_id: int) -> list[Resume]:
    with get_session_factory()() as session:
        return list(
            session.execute(select(Resume).where(Resume.user_id == user_id))
            .scalars()
            .all()
        )


def test_authenticated_upload_persists_resume_for_current_user(
    client: TestClient,
) -> None:
    headers, user_id = create_authenticated_user(client)

    status_code, payload = post_resume(client, headers, create_text_pdf())

    assert status_code == 201
    assert set(payload) == {
        "id",
        "extracted_text",
        "page_count",
        "character_count",
        "created_at",
    }
    assert payload["extracted_text"] == EXPECTED_TEXT
    assert payload["page_count"] == 1
    assert payload["character_count"] == len(EXPECTED_TEXT)
    assert payload["created_at"]
    assert "unpersisted-original-name.pdf" not in payload

    rows = resume_rows_for_user(user_id)
    assert len(rows) == 1
    assert rows[0].id == payload["id"]
    assert rows[0].user_id == user_id
    assert rows[0].extracted_text == EXPECTED_TEXT
    assert rows[0].page_count == 1
    assert rows[0].character_count == len(EXPECTED_TEXT)


def test_upload_requires_authentication_and_does_not_persist(
    client: TestClient,
) -> None:
    status_code, payload = post_resume(client, None, create_text_pdf())

    assert status_code == 401
    assert payload == {"detail": "Not authenticated."}


@pytest.mark.parametrize(
    ("content", "expected_status", "expected_detail"),
    [
        (b"", 422, "PDF upload is empty."),
        (b"not a PDF", 422, "Upload is not a valid, readable PDF."),
        (
            b"%PDF-1.4\nnot-a-valid-xref",
            422,
            "Upload is not a valid, readable PDF.",
        ),
        (create_textless_pdf(), 422, "PDF contains no extractable text."),
        (create_encrypted_pdf(), 422, "Encrypted PDFs are not supported."),
        (
            create_text_pdf() + b"x" * (MAX_UPLOAD_BYTES + 1),
            413,
            "PDF must not exceed 5 MB.",
        ),
    ],
    ids=["empty", "not-pdf", "malformed-pdf", "textless", "encrypted", "oversized"],
)
def test_invalid_upload_is_rejected_without_persistence(
    client: TestClient,
    content: bytes,
    expected_status: int,
    expected_detail: str,
) -> None:
    headers, user_id = create_authenticated_user(client)

    status_code, payload = post_resume(client, headers, content)

    assert status_code == expected_status
    assert payload == {"detail": expected_detail}
    assert resume_rows_for_user(user_id) == []


def test_persistence_failure_rolls_back_and_returns_safe_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers, user_id = create_authenticated_user(client)
    original_rollback = Session.rollback
    rollback_called = False

    def fail_commit(_session: Session) -> None:
        raise OperationalError("insert resume", {}, RuntimeError("database failure"))

    def track_rollback(session: Session) -> None:
        nonlocal rollback_called
        rollback_called = True
        original_rollback(session)

    monkeypatch.setattr(Session, "commit", fail_commit)
    monkeypatch.setattr(Session, "rollback", track_rollback)

    status_code, payload = post_resume(client, headers, create_text_pdf())

    assert status_code == 500
    assert payload == {"detail": "Unable to save resume."}
    assert rollback_called
    assert resume_rows_for_user(user_id) == []


def test_extract_text_endpoint_remains_non_persistent(client: TestClient) -> None:
    headers, user_id = create_authenticated_user(client)
    response = client.post(
        "/api/v1/resumes/extract-text",
        headers=headers,
        files={"file": ("resume.pdf", create_text_pdf(), "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json() == {"text": EXPECTED_TEXT, "page_count": 1}
    assert resume_rows_for_user(user_id) == []
