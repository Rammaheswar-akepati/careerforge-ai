from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.models.profile import Skill, StudentProfile
from app.repositories.profile_repository import (
    DuplicateSkillAssociationError,
    ProfileRepository,
)


class ProfileNotFoundError(LookupError):
    """Raised when the authenticated user has no student profile."""


class ProfileAlreadyExistsError(ValueError):
    """Raised when the authenticated user already has a student profile."""


class SkillAlreadyExistsError(ValueError):
    """Raised when the profile already has the requested skill."""


class SkillNotFoundError(LookupError):
    """Raised when the profile does not have the requested skill."""


class ProfileService:
    """Business operations for a user's profile and profile-owned skills."""

    def __init__(self, repository: ProfileRepository) -> None:
        self.repository = repository

    def get_profile(self, user_id: int) -> StudentProfile:
        profile = self.repository.get_profile(user_id)
        if profile is None:
            raise ProfileNotFoundError
        return profile

    def create_profile(
        self, user_id: int, fields: dict[str, object]
    ) -> StudentProfile:
        if self.repository.get_profile(user_id) is not None:
            raise ProfileAlreadyExistsError
        try:
            return self.repository.create_profile(user_id, fields)
        except IntegrityError as exc:
            raise ProfileAlreadyExistsError from exc

    def update_profile(
        self, user_id: int, fields: dict[str, object]
    ) -> StudentProfile:
        profile = self.get_profile(user_id)
        return self.repository.update_profile(profile, fields)

    def delete_profile(self, user_id: int) -> None:
        profile = self.get_profile(user_id)
        self.repository.delete_profile(profile)

    def list_skills(self, user_id: int) -> list[Skill]:
        profile = self.get_profile(user_id)
        return self.repository.list_skills(profile.id)

    def add_skill(self, user_id: int, name: str) -> Skill:
        profile = self.get_profile(user_id)
        try:
            return self.repository.add_skill(profile.id, name)
        except DuplicateSkillAssociationError as exc:
            raise SkillAlreadyExistsError from exc
        except IntegrityError as exc:
            raise SkillAlreadyExistsError from exc

    def remove_skill(self, user_id: int, skill_id: int) -> None:
        profile = self.get_profile(user_id)
        if not self.repository.remove_skill(profile.id, skill_id):
            raise SkillNotFoundError