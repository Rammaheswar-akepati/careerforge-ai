from __future__ import annotations

import string

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
