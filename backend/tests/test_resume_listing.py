from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_session_factory
from app.main import app
from app.models.resume import Resume


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def create_authenticated_user(client: TestClient) -> tuple[dict[str, str], int]:
    email = f"resume-list-{uuid4().hex}@example.com"
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "full_name": "Resume Listing User",
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


def add_resumes(
    user_id: int,
    count: int,
    created_at: datetime | None = None,
) -> list[int]:
    timestamp = created_at or datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)
    with get_session_factory()() as session:
        resumes = [
            Resume(
                user_id=user_id,
                extracted_text=f"Private resume text {index}",
                page_count=index + 1,
                character_count=len(f"Private resume text {index}"),
                created_at=timestamp,
            )
            for index in range(count)
        ]
        session.add_all(resumes)
        session.commit()
        return [resume.id for resume in resumes]


def test_list_returns_only_owned_resume_metadata_and_orders_newest_first(
    client: TestClient,
) -> None:
    headers, user_id = create_authenticated_user(client)
    other_headers, other_user_id = create_authenticated_user(client)
    older = datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc)
    newer = datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)
    older_id = add_resumes(user_id, 1, older)[0]
    same_time_ids = add_resumes(user_id, 2, newer)
    add_resumes(other_user_id, 1, datetime(2026, 11, 4, 10, 0, tzinfo=timezone.utc))

    response = client.get("/api/v1/resumes", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == [
        same_time_ids[1],
        same_time_ids[0],
        older_id,
    ]
    assert payload["total"] == 3
    assert payload["page"] == 1
    assert payload["page_size"] == 20
    assert payload["total_pages"] == 1
    assert all(
        set(item) == {"id", "page_count", "character_count", "created_at"}
        for item in payload["items"]
    )
    assert all("extracted_text" not in item for item in payload["items"])


def test_default_pagination_limits_page_to_twenty(client: TestClient) -> None:
    headers, user_id = create_authenticated_user(client)
    inserted_ids = add_resumes(user_id, 23)

    response = client.get("/api/v1/resumes", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 20
    assert [item["id"] for item in payload["items"]] == sorted(
        inserted_ids, reverse=True
    )[:20]
    assert payload["total"] == 23
    assert payload["page"] == 1
    assert payload["page_size"] == 20
    assert payload["total_pages"] == 2


def test_custom_pagination_returns_requested_page(client: TestClient) -> None:
    headers, user_id = create_authenticated_user(client)
    inserted_ids = add_resumes(user_id, 5)

    response = client.get(
        "/api/v1/resumes?page=2&page_size=2",
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == sorted(
        inserted_ids, reverse=True
    )[2:4]
    assert payload["total"] == 5
    assert payload["page"] == 2
    assert payload["page_size"] == 2
    assert payload["total_pages"] == 3


@pytest.mark.parametrize(
    "query",
    ["page=0", "page=-1", "page_size=0", "page_size=101"],
)
def test_invalid_pagination_parameters_are_rejected(
    client: TestClient,
    query: str,
) -> None:
    headers, _ = create_authenticated_user(client)

    response = client.get(f"/api/v1/resumes?{query}", headers=headers)

    assert response.status_code == 422


def test_empty_list_returns_zero_total_pages(client: TestClient) -> None:
    headers, _ = create_authenticated_user(client)

    response = client.get("/api/v1/resumes", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 20,
        "total_pages": 0,
    }


def test_page_beyond_last_returns_empty_items(client: TestClient) -> None:
    headers, user_id = create_authenticated_user(client)
    add_resumes(user_id, 1)

    response = client.get(
        "/api/v1/resumes?page=2",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "total": 1,
        "page": 2,
        "page_size": 20,
        "total_pages": 1,
    }


def test_user_can_retrieve_owned_resume(client: TestClient) -> None:
    headers, user_id = create_authenticated_user(client)
    resume_id = add_resumes(user_id, 1)[0]

    response = client.get(f"/api/v1/resumes/{resume_id}", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == resume_id
    assert payload["extracted_text"] == "Private resume text 0"
    assert payload["page_count"] == 1
    assert payload["character_count"] == len("Private resume text 0")
    assert payload["created_at"]


def test_foreign_and_nonexistent_resume_ids_return_same_404(
    client: TestClient,
) -> None:
    headers, user_id = create_authenticated_user(client)
    _, other_user_id = create_authenticated_user(client)
    foreign_resume_id = add_resumes(other_user_id, 1)[0]
    nonexistent_resume_id = max(user_id, other_user_id, foreign_resume_id) + 100

    foreign_response = client.get(
        f"/api/v1/resumes/{foreign_resume_id}",
        headers=headers,
    )
    nonexistent_response = client.get(
        f"/api/v1/resumes/{nonexistent_resume_id}",
        headers=headers,
    )

    assert foreign_response.status_code == 404
    assert nonexistent_response.status_code == 404
    assert foreign_response.json() == {"detail": "Resume not found."}
    assert nonexistent_response.json() == foreign_response.json()


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/api/v1/resumes", "get"),
        ("/api/v1/resumes/1", "get"),
    ],
)
def test_list_and_detail_require_authentication(
    client: TestClient,
    path: str,
    method: str,
) -> None:
    response = getattr(client, method)(path)

    assert response.status_code == 401


def test_existing_upload_and_extract_endpoints_remain_unchanged(
    client: TestClient,
) -> None:
    headers, user_id = create_authenticated_user(client)
    pdf_content = create_text_pdf("Phase 5B.3 regression test")

    extraction_response = client.post(
        "/api/v1/resumes/extract-text",
        headers=headers,
        files={"file": ("resume.pdf", pdf_content, "application/pdf")},
    )
    assert extraction_response.status_code == 200
    assert extraction_response.json() == {
        "text": "Phase 5B.3 regression test",
        "page_count": 1,
    }

    upload_response = client.post(
        "/api/v1/resumes",
        headers=headers,
        files={"file": ("resume.pdf", pdf_content, "application/pdf")},
    )
    assert upload_response.status_code == 201
    resume_id = upload_response.json()["id"]

    list_response = client.get("/api/v1/resumes", headers=headers)
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["items"]] == [resume_id]
    assert list_response.json()["items"][0].get("extracted_text") is None

    with get_session_factory()() as session:
        persisted = session.get(Resume, resume_id)
        assert persisted is not None
        assert persisted.user_id == user_id


def create_text_pdf(text: str) -> bytes:
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
