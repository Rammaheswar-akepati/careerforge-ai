from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.profile import Skill, StudentProfile, StudentSkill


class DuplicateSkillAssociationError(ValueError):
    """Raised when a profile already has the requested skill."""


class ProfileRepository:
    """Persistence operations for student profiles and their skills."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_profile(self, user_id: int) -> StudentProfile | None:
        statement = select(StudentProfile).where(StudentProfile.user_id == user_id)
        return self.session.execute(statement).scalar_one_or_none()

    def create_profile(
        self, user_id: int, fields: dict[str, object]
    ) -> StudentProfile:
        profile = StudentProfile(user_id=user_id, **fields)
        self.session.add(profile)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise
        self.session.refresh(profile)
        return profile

    def update_profile(
        self, profile: StudentProfile, fields: dict[str, object]
    ) -> StudentProfile:
        for field_name, value in fields.items():
            setattr(profile, field_name, value)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def delete_profile(self, profile: StudentProfile) -> None:
        self.session.delete(profile)
        self.session.commit()

    def list_skills(self, profile_id: int) -> list[Skill]:
        statement = (
            select(Skill)
            .join(StudentSkill, StudentSkill.skill_id == Skill.id)
            .where(StudentSkill.profile_id == profile_id)
            .order_by(Skill.name)
        )
        return list(self.session.execute(statement).scalars())

    def add_skill(self, profile_id: int, normalized_name: str) -> Skill:
        association = self.session.execute(
            select(StudentSkill).where(
                StudentSkill.profile_id == profile_id,
                StudentSkill.skill.has(name=normalized_name),
            )
        ).scalar_one_or_none()
        if association is not None:
            raise DuplicateSkillAssociationError

        skill = self.session.execute(
            select(Skill).where(Skill.name == normalized_name)
        ).scalar_one_or_none()
        if skill is None:
            skill = Skill(name=normalized_name)
            try:
                with self.session.begin_nested():
                    self.session.add(skill)
                    self.session.flush()
            except IntegrityError:
                skill = self.session.execute(
                    select(Skill).where(Skill.name == normalized_name)
                ).scalar_one()

        self.session.add(StudentSkill(profile_id=profile_id, skill_id=skill.id))
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise
        return skill

    def remove_skill(self, profile_id: int, skill_id: int) -> bool:
        association = self.session.execute(
            select(StudentSkill).where(
                StudentSkill.profile_id == profile_id,
                StudentSkill.skill_id == skill_id,
            )
        ).scalar_one_or_none()
        if association is None:
            return False
        self.session.delete(association)
        self.session.commit()
        return True