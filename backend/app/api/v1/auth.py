from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_jwt_secret,
    get_token_from_authorization,
    rfc_bearer_scheme,
)
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, Token, UserCreate
from app.schemas.user import UserRead
from app.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(rfc_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a valid bearer token."""
    token = get_token_from_authorization(credentials)
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = UserRepository(db).get_by_id(int(user_id))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    """Create a new application user with a hashed password."""
    service = AuthService(UserRepository(db))
    try:
        user = service.register_user(payload.email, payload.password, payload.full_name)
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        ) from exc
    return user


@router.post("/login", response_model=Token)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    """Authenticate a user and return an access token."""
    service = AuthService(UserRepository(db))
    try:
        user = service.authenticate_user(payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(
            minutes=get_settings().jwt_access_token_expire_minutes
        ),
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserRead:
    """Return the authenticated user without exposing sensitive fields."""
    return current_user
