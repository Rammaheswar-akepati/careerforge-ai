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
