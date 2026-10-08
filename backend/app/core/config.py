"""Environment-based application configuration."""

from dataclasses import dataclass
from os import getenv
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    """Runtime settings read from environment variables."""

    database_url: str | None
    jwt_secret: str | None
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int


def get_settings() -> Settings:
    """Return settings without loading or persisting secret values."""
    return Settings(
        database_url=getenv("DATABASE_URL"),
        jwt_secret=getenv("JWT_SECRET"),
        jwt_algorithm=getenv("JWT_ALGORITHM", "HS256"),
        jwt_access_token_expire_minutes=int(
            getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        ),
    )
