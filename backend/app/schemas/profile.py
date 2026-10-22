from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, TypeAdapter, field_validator


_http_url_adapter = TypeAdapter(HttpUrl)


class StudentProfileFields(BaseModel):
    phone: str | None = Field(default=None, max_length=32)
    college: str | None = Field(default=None, max_length=255)
    degree: str | None = Field(default=None, max_length=128)
    branch: str | None = Field(default=None, max_length=128)
    graduation_year: int | None = Field(default=None, ge=1000, le=9999)
    cgpa: Decimal | None = Field(default=None, ge=0, le=10, max_digits=4, decimal_places=2)
    tenth_percentage: Decimal | None = Field(
        default=None, ge=0, le=100, max_digits=5, decimal_places=2
    )
    diploma_percentage: Decimal | None = Field(
        default=None, ge=0, le=100, max_digits=5, decimal_places=2
    )
    bio: str | None = Field(default=None, max_length=5000)
    portfolio_url: str | None = Field(default=None, max_length=2048)
    github_url: str | None = Field(default=None, max_length=2048)
    linkedin_url: str | None = Field(default=None, max_length=2048)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned_value = value.strip()
        digits = sum(character.isdigit() for character in cleaned_value)
        if not cleaned_value or digits < 7 or digits > 20:
            raise ValueError("Phone must contain between 7 and 20 digits.")
        if any(character not in "+0123456789(). -" for character in cleaned_value):
            raise ValueError("Phone contains unsupported characters.")
        return cleaned_value

    @field_validator("college", "degree", "branch", "bio")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned_value = value.strip()
        return cleaned_value or None

    @field_validator("graduation_year")
    @classmethod
    def validate_graduation_year(cls, value: int | None) -> int | None:
        if value is not None and not 1950 <= value <= datetime.now().year + 10:
            raise ValueError("Graduation year is outside the supported range.")
        return value

    @field_validator("portfolio_url", "github_url", "linkedin_url", mode="before")
    @classmethod
    def validate_http_url(cls, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
        return str(_http_url_adapter.validate_python(value))

    model_config = ConfigDict(extra="forbid")


class StudentProfileCreate(StudentProfileFields):
    """Optional profile details supplied when creating a profile."""


class StudentProfileUpdate(StudentProfileFields):
    """Profile fields that may be changed by the authenticated owner."""


class StudentProfileRead(StudentProfileFields):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized_name = " ".join(value.split()).casefold()
        if not normalized_name:
            raise ValueError("Skill name is required.")
        return normalized_name

    model_config = ConfigDict(extra="forbid")


class SkillRead(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)