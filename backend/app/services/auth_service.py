from __future__ import annotations

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


class EmailAlreadyExistsError(ValueError):
    """Raised when a user registers with an email already in use."""


class AuthService:
    """Service layer for the initial user registration flow."""

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def register_user(self, email: str, password: str, full_name: str) -> User:
        normalized_email = email.strip().lower()
        if self.user_repository.get_by_email(normalized_email):
            raise EmailAlreadyExistsError("A user with this email already exists.")

        cleaned_name = " ".join(full_name.strip().split())
        user = User(
            email=normalized_email,
            password_hash=hash_password(password),
            full_name=cleaned_name,
        )
        return self.user_repository.create(user)
