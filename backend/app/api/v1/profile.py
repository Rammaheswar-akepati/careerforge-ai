from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import (
    SkillCreate,
    SkillRead,
    StudentProfileCreate,
    StudentProfileRead,
    StudentProfileUpdate,
)
from app.services.profile_service import (
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
    ProfileService,
    SkillAlreadyExistsError,
    SkillNotFoundError,
)

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


def get_profile_service(db: Session = Depends(get_db)) -> ProfileService:
    return ProfileService(ProfileRepository(db))


@router.get("", response_model=StudentProfileRead)
def read_profile(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> StudentProfileRead:
    try:
        return service.get_profile(current_user.id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.") from exc


@router.post(
    "", response_model=StudentProfileRead, status_code=status.HTTP_201_CREATED
)
def create_profile(
    payload: StudentProfileCreate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> StudentProfileRead:
    try:
        return service.create_profile(
            current_user.id, payload.model_dump(exclude_unset=True)
        )
    except ProfileAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A profile already exists for this user.",
        ) from exc


@router.put("", response_model=StudentProfileRead)
def update_profile(
    payload: StudentProfileUpdate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> StudentProfileRead:
    try:
        return service.update_profile(
            current_user.id, payload.model_dump(exclude_unset=True)
        )
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.") from exc


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> Response:
    try:
        service.delete_profile(current_user.id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/skills", response_model=list[SkillRead])
def list_skills(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> list[SkillRead]:
    try:
        return service.list_skills(current_user.id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.") from exc


@router.post(
    "/skills", response_model=SkillRead, status_code=status.HTTP_201_CREATED
)
def add_skill(
    payload: SkillCreate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> SkillRead:
    try:
        return service.add_skill(current_user.id, payload.name)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.") from exc
    except SkillAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This skill is already associated with the profile.",
        ) from exc


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> Response:
    try:
        service.remove_skill(current_user.id, skill_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.") from exc
    except SkillNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)