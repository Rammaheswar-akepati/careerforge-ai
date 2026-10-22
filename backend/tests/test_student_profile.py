from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_session_factory
from app.main import app
from app.models.profile import Skill, StudentProfile, StudentSkill
from app.models.user import User


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def create_authenticated_user(client: TestClient, email: str) -> dict[str, str]:
    email_local_part = email.partition("@")[0]
    unique_email = f"{email_local_part}-{uuid4().hex}@example.com"
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "StrongPass123!",
            "full_name": "Profile Test User",
        },
    )
    assert registration.status_code == 201, registration.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "StrongPass123!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_authenticated_user_can_create_profile(client: TestClient) -> None:
    headers = create_authenticated_user(client, "create-profile@example.com")

    response = client.post(
        "/api/v1/profile",
        headers=headers,
        json={
            "college": "Example University",
            "cgpa": 8.75,
            "phone": "+1 (415) 555-2671",
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["college"] == "Example University"
    assert response.json()["cgpa"] == "8.75"
    assert response.json()["phone"] == "+1 (415) 555-2671"
    assert "password_hash" not in response.json()


def test_unauthenticated_user_cannot_create_profile(client: TestClient) -> None:
    response = client.post("/api/v1/profile", json={"college": "Example"})

    assert response.status_code == 401


def test_authenticated_user_can_retrieve_own_profile(client: TestClient) -> None:
    headers = create_authenticated_user(client, "read-profile@example.com")
    client.post("/api/v1/profile", headers=headers, json={"college": "Example"})

    response = client.get("/api/v1/profile", headers=headers)

    assert response.status_code == 200, response.text
    assert response.json()["college"] == "Example"
    assert "password_hash" not in response.json()


def test_authenticated_user_can_update_own_profile(client: TestClient) -> None:
    headers = create_authenticated_user(client, "update-profile@example.com")
    client.post("/api/v1/profile", headers=headers, json={"college": "Old College"})

    response = client.put(
        "/api/v1/profile", headers=headers, json={"college": "New College"}
    )

    assert response.status_code == 200, response.text
    assert response.json()["college"] == "New College"


def test_authenticated_user_can_delete_own_profile(client: TestClient) -> None:
    headers = create_authenticated_user(client, "delete-profile@example.com")
    client.post("/api/v1/profile", headers=headers, json={})

    response = client.delete("/api/v1/profile", headers=headers)

    assert response.status_code == 204
    assert client.get("/api/v1/profile", headers=headers).status_code == 404


def test_missing_profile_returns_404(client: TestClient) -> None:
    headers = create_authenticated_user(client, "missing-profile@example.com")

    response = client.get("/api/v1/profile", headers=headers)

    assert response.status_code == 404


def test_profile_mutations_and_skills_return_404_without_profile(
    client: TestClient,
) -> None:
    headers = create_authenticated_user(client, "missing-profile-operations@example.com")

    update = client.put("/api/v1/profile", headers=headers, json={"college": "New"})
    delete_profile = client.delete("/api/v1/profile", headers=headers)
    list_skills = client.get("/api/v1/profile/skills", headers=headers)
    add_skill = client.post(
        "/api/v1/profile/skills", headers=headers, json={"name": "Python"}
    )

    assert update.status_code == 404
    assert delete_profile.status_code == 404
    assert list_skills.status_code == 404
    assert add_skill.status_code == 404


def test_duplicate_profile_creation_is_rejected(client: TestClient) -> None:
    headers = create_authenticated_user(client, "duplicate-profile@example.com")
    client.post("/api/v1/profile", headers=headers, json={})

    response = client.post("/api/v1/profile", headers=headers, json={})

    assert response.status_code == 409


@pytest.mark.parametrize(
    "field,value",
    [
        ("cgpa", 10.01),
        ("tenth_percentage", 100.01),
        ("diploma_percentage", -0.01),
        ("graduation_year", 2101),
        ("graduation_year", 1949),
        ("portfolio_url", "javascript:alert(1)"),
        ("phone", "123"),
        ("phone", "call me at 12345678"),
    ],
)
def test_invalid_profile_fields_are_rejected(
    client: TestClient, field: str, value: object
) -> None:
    headers = create_authenticated_user(client, "invalid-profile@example.com")

    response = client.post("/api/v1/profile", headers=headers, json={field: value})

    assert response.status_code == 422, response.text


def test_profile_data_is_persisted(client: TestClient) -> None:
    headers = create_authenticated_user(client, "persist-profile@example.com")
    created = client.post(
        "/api/v1/profile",
        headers=headers,
        json={"college": "Persisted University", "graduation_year": 2027},
    )
    profile_id = created.json()["id"]

    session = get_session_factory()()
    persisted = session.get(StudentProfile, profile_id)
    session.close()

    assert created.status_code == 201, created.text
    assert persisted is not None
    assert persisted.college == "Persisted University"


def test_users_cannot_read_or_modify_another_users_profile(
    client: TestClient,
) -> None:
    first_user_headers = create_authenticated_user(client, "first-owner@example.com")
    second_user_headers = create_authenticated_user(client, "second-owner@example.com")
    client.post(
        "/api/v1/profile", headers=first_user_headers, json={"college": "First"}
    )
    client.post(
        "/api/v1/profile", headers=second_user_headers, json={"college": "Second"}
    )

    first_user_response = client.get("/api/v1/profile", headers=first_user_headers)
    second_user_response = client.get("/api/v1/profile", headers=second_user_headers)
    attempted_update = client.put(
        "/api/v1/profile",
        headers=first_user_headers,
        json={"user_id": second_user_response.json()["user_id"], "college": "Hijacked"},
    )

    assert first_user_response.json()["college"] == "First"
    assert second_user_response.json()["college"] == "Second"
    assert attempted_update.status_code == 422
    assert client.get("/api/v1/profile", headers=second_user_headers).json()[
        "college"
    ] == "Second"


def test_authenticated_user_can_add_and_list_skill(client: TestClient) -> None:
    headers = create_authenticated_user(client, "add-skill@example.com")
    client.post("/api/v1/profile", headers=headers, json={})

    added = client.post(
        "/api/v1/profile/skills", headers=headers, json={"name": "Python"}
    )
    listed = client.get("/api/v1/profile/skills", headers=headers)

    assert added.status_code == 201, added.text
    assert added.json()["name"] == "python"
    assert [skill["id"] for skill in listed.json()] == [added.json()["id"]]


def test_existing_normalized_skill_is_reused(client: TestClient) -> None:
    first_headers = create_authenticated_user(client, "reuse-first@example.com")
    second_headers = create_authenticated_user(client, "reuse-second@example.com")
    client.post("/api/v1/profile", headers=first_headers, json={})
    client.post("/api/v1/profile", headers=second_headers, json={})

    first = client.post(
        "/api/v1/profile/skills", headers=first_headers, json={"name": "Python"}
    )
    second = client.post(
        "/api/v1/profile/skills", headers=second_headers, json={"name": " PYTHON "}
    )

    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    session = get_session_factory()()
    count = session.execute(select(Skill)).scalars().all()
    session.close()
    assert len(count) == 1


def test_duplicate_user_skill_association_is_rejected(client: TestClient) -> None:
    headers = create_authenticated_user(client, "duplicate-skill@example.com")
    client.post("/api/v1/profile", headers=headers, json={})
    client.post("/api/v1/profile/skills", headers=headers, json={"name": "Python"})

    duplicate = client.post(
        "/api/v1/profile/skills", headers=headers, json={"name": "PYTHON"}
    )

    assert duplicate.status_code == 409


def test_user_cannot_remove_another_users_skill(client: TestClient) -> None:
    requester_headers = create_authenticated_user(client, "skill-requester@example.com")
    owner_headers = create_authenticated_user(client, "skill-owner@example.com")
    client.post("/api/v1/profile", headers=requester_headers, json={})
    client.post("/api/v1/profile", headers=owner_headers, json={})
    owned_skill = client.post(
        "/api/v1/profile/skills", headers=owner_headers, json={"name": "Python"}
    ).json()

    response = client.delete(
        f"/api/v1/profile/skills/{owned_skill['id']}", headers=requester_headers
    )

    assert response.status_code == 404
    assert client.get("/api/v1/profile/skills", headers=owner_headers).json() == [
        owned_skill
    ]


def test_removing_nonexistent_skill_returns_404(client: TestClient) -> None:
    headers = create_authenticated_user(client, "nonexistent-skill@example.com")
    client.post("/api/v1/profile", headers=headers, json={})

    response = client.delete("/api/v1/profile/skills/999999", headers=headers)

    assert response.status_code == 404


def test_removing_skill_keeps_global_skill_for_other_users(
    client: TestClient,
) -> None:
    first_headers = create_authenticated_user(client, "remove-first@example.com")
    second_headers = create_authenticated_user(client, "remove-second@example.com")
    client.post("/api/v1/profile", headers=first_headers, json={})
    client.post("/api/v1/profile", headers=second_headers, json={})
    first_skill = client.post(
        "/api/v1/profile/skills", headers=first_headers, json={"name": "Python"}
    ).json()
    client.post(
        "/api/v1/profile/skills", headers=second_headers, json={"name": "python"}
    )

    removed = client.delete(
        f"/api/v1/profile/skills/{first_skill['id']}", headers=first_headers
    )

    assert removed.status_code == 204
    assert client.get("/api/v1/profile/skills", headers=first_headers).json() == []
    assert client.get("/api/v1/profile/skills", headers=second_headers).json()[
        0
    ]["id"] == first_skill["id"]
    session = get_session_factory()()
    assert session.get(Skill, first_skill["id"]) is not None
    session.close()


def test_profile_endpoints_require_authentication(client: TestClient) -> None:
    responses = [
        client.get("/api/v1/profile"),
        client.put("/api/v1/profile", json={}),
        client.delete("/api/v1/profile"),
        client.get("/api/v1/profile/skills"),
        client.post("/api/v1/profile/skills", json={"name": "Python"}),
        client.delete("/api/v1/profile/skills/1"),
    ]

    assert all(response.status_code == 401 for response in responses)


def test_health_and_docs_routes_remain_available(client: TestClient) -> None:
    assert client.get("/").status_code == 200
    assert client.get("/docs").status_code == 200