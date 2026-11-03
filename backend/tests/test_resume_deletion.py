from __future__ import annotations

from collections.abc import Generator
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
    email = f"resume-delete-{uuid4().hex}@example.com"
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "full_name": "Resume Deletion User",
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


def create_resume(user_id: int) -> int:
    with get_session_factory()() as session:
        resume = Resume(
            user_id=user_id,
            extracted_text="Private resume content",
            page_count=1,
            character_count=len("Private resume content"),
        )
        session.add(resume)
        session.commit()
        return resume.id


def test_owner_can_delete_resume_and_it_is_no_longer_accessible(
    client: TestClient,
) -> None:
    headers, user_id = create_authenticated_user(client)
    resume_id = create_resume(user_id)

    response = client.delete(f"/api/v1/resumes/{resume_id}", headers=headers)

    assert response.status_code == 204
    assert response.content == b""

    detail_response = client.get(
        f"/api/v1/resumes/{resume_id}",
        headers=headers,
    )
    assert detail_response.status_code == 404
    assert detail_response.json() == {"detail": "Resume not found."}

    list_response = client.get("/api/v1/resumes", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json() == {
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 20,
        "total_pages": 0,
    }


def test_user_cannot_delete_another_users_resume(
    client: TestClient,
) -> None:
    requester_headers, _ = create_authenticated_user(client)
    owner_headers, owner_id = create_authenticated_user(client)
    resume_id = create_resume(owner_id)

    response = client.delete(
        f"/api/v1/resumes/{resume_id}",
        headers=requester_headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Resume not found."}
    owner_response = client.get(
        f"/api/v1/resumes/{resume_id}",
        headers=owner_headers,
    )
    assert owner_response.status_code == 200
    assert owner_response.json()["extracted_text"] == "Private resume content"


def test_foreign_owned_and_nonexistent_ids_return_identical_404(
    client: TestClient,
) -> None:
    requester_headers, requester_id = create_authenticated_user(client)
    _, owner_id = create_authenticated_user(client)
    foreign_resume_id = create_resume(owner_id)
    nonexistent_resume_id = max(requester_id, owner_id, foreign_resume_id) + 100

    foreign_response = client.delete(
        f"/api/v1/resumes/{foreign_resume_id}",
        headers=requester_headers,
    )
    nonexistent_response = client.delete(
        f"/api/v1/resumes/{nonexistent_resume_id}",
        headers=requester_headers,
    )

    assert foreign_response.status_code == 404
    assert nonexistent_response.status_code == 404
    assert foreign_response.json() == {"detail": "Resume not found."}
    assert nonexistent_response.json() == foreign_response.json()


def test_resume_deletion_requires_authentication(client: TestClient) -> None:
    response = client.delete("/api/v1/resumes/1")

    assert response.status_code == 401
