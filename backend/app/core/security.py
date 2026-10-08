from __future__ import annotations

import string
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
rfc_bearer_scheme = HTTPBearer(auto_error=False)


def validate_password(password: str) -> str:
    """Validate a password against a reasonable baseline for the app."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if len(password) > 128:
        raise ValueError("Password must be at most 128 characters long.")
    if not any(character.isupper() for character in password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not any(character.islower() for character in password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not any(character.isdigit() for character in password):
        raise ValueError("Password must contain at least one digit.")
    if not any(character in string.punctuation for character in password):
        raise ValueError("Password must contain at least one special character.")
    return password


def hash_password(password: str) -> str:
    """Hash a password with a modern password hashing algorithm."""
    validated_password = validate_password(password)
    return pwd_context.hash(validated_password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plain password against the stored hash."""
    return pwd_context.verify(password, password_hash)


def get_jwt_secret() -> str:
    """Return the configured JWT secret or raise a clear configuration error."""
    secret = get_settings().jwt_secret
    if not secret:
        raise ValueError("JWT_SECRET must be configured in the environment.")
    return secret


def get_jwt_algorithm() -> str:
    """Return the configured JWT algorithm."""
    return get_settings().jwt_algorithm


def create_access_token(subject: int, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token for the supplied user identifier."""
    now = datetime.now(timezone.utc)
    expire_delta = expires_delta or timedelta(
        minutes=get_settings().jwt_access_token_expire_minutes
    )
    expires_at = now + expire_delta
    payload: dict[str, Any] = {"sub": str(subject), "iat": now, "exp": expires_at}
    return jwt.encode(payload, get_jwt_secret(), algorithm=get_jwt_algorithm())


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        return jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[get_jwt_algorithm()],
        )
    except jwt.PyJWTError as exc:
        raise ValueError("Invalid or expired token.") from exc


def get_token_from_authorization(credentials: HTTPAuthorizationCredentials | None) -> str:
    """Validate bearer-token credentials and return the token payload."""
    if not credentials or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
