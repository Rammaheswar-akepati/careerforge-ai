from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import validate_password


class UserCreate(BaseModel):
    """Fields required to register a new user."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return value.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        try:
            return validate_password(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        cleaned_name = " ".join(value.strip().split())
        if not cleaned_name:
            raise ValueError("Full name is required.")
        return cleaned_name

    model_config = ConfigDict(from_attributes=True)
