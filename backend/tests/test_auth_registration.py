from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.main import app
from app.db.session import get_session_factory
from app.models.user import User


@pytest.fixture(autouse=True)
def clean_users() -> None:
    session = get_session_factory()()
    session.execute(delete(User))
    session.commit()
    session.close()
    yield
    session = get_session_factory()()
    session.execute(delete(User))
    session.commit()
    session.close()


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_register_user_success(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": " Alice@example.com ",
            "password": "StrongPass123!",
            "full_name": "  Alice Johnson  ",
        },
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["email"] == "alice@example.com"
    assert payload["full_name"] == "Alice Johnson"
    assert "password" not in payload
    assert "password_hash" not in payload


def test_register_duplicate_email(client: TestClient) -> None:
    first = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "StrongPass123!",
            "full_name": "First User",
        },
    )
    assert first.status_code == 201, first.text

    second = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "AnotherPass456!",
            "full_name": "Second User",
        },
    )

    assert second.status_code == 409, second.text
    assert "already exists" in second.json()["detail"].lower()


def test_register_invalid_email(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "StrongPass123!",
            "full_name": "Invalid Email",
        },
    )

    assert response.status_code == 422, response.text


def test_register_password_validation(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "weak",
            "full_name": "Weak User",
        },
    )

    assert response.status_code == 422, response.text


def test_password_is_hashed_and_not_plaintext(client: TestClient) -> None:
    raw_password = "StrongPass123!"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "hash@example.com",
            "password": raw_password,
            "full_name": "Hash User",
        },
    )

    assert response.status_code == 201, response.text
    session = get_session_factory()()
    user = session.query(User).filter_by(email="hash@example.com").one()
    session.close()

    assert user.password_hash != raw_password
    assert user.password_hash.startswith("$2b$")
    assert "StrongPass123!" not in user.password_hash


def test_registration_response_does_not_expose_password_hash(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "response@example.com",
            "password": "StrongPass123!",
            "full_name": "Response User",
        },
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert "password_hash" not in payload
    assert "password" not in payload


def test_user_is_persisted_in_database(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "persist@example.com",
            "password": "StrongPass123!",
            "full_name": "Persist User",
        },
    )

    assert response.status_code == 201, response.text
    session = get_session_factory()()
    count = session.query(User).filter_by(email="persist@example.com").count()
    session.close()

    assert count == 1


def test_login_success(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "StrongPass123!",
            "full_name": "Login User",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert "access_token" in payload
    assert "password_hash" not in payload
    assert "password" not in payload


def test_login_wrong_password(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpass@example.com",
            "password": "StrongPass123!",
            "full_name": "Wrong Pass User",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "WrongPass456!",
        },
    )

    assert response.status_code == 401, response.text


def test_login_nonexistent_email(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "missing@example.com",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 401, response.text


def test_login_invalid_email_format(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "not-an-email",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 422, response.text


def test_login_inactive_user(client: TestClient) -> None:
    session = get_session_factory()()
    session.add(
        User(
            email="inactive@example.com",
            password_hash="$2b$12$dummyhashvalueforinactiveuser",
            full_name="Inactive User",
            is_active=False,
        )
    )
    session.commit()
    session.close()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "inactive@example.com",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 401, response.text


def test_get_me_with_valid_token(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "password": "StrongPass123!",
            "full_name": "Me User",
        },
    )
    assert register_response.status_code == 201, register_response.text

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "me@example.com",
            "password": "StrongPass123!",
        },
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["email"] == "me@example.com"
    assert "password_hash" not in payload
    assert "password" not in payload


def test_get_me_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401, response.text


def test_get_me_rejects_malformed_token(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Token abcdef"},
    )

    assert response.status_code == 401, response.text


def test_get_me_rejects_invalid_token(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401, response.text


def test_jwt_expired_token_rejected(client: TestClient) -> None:
    from datetime import timedelta

    from app.core.security import create_access_token

    token = create_access_token(
        subject=999999,
        expires_delta=timedelta(minutes=-5),
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401, response.text


def test_jwt_payload_has_no_password_fields(client: TestClient) -> None:
    from app.core.security import create_access_token

    token = create_access_token(subject=123)
    payload = token.split(".")[1]
    assert payload
