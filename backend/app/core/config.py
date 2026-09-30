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


def get_settings() -> Settings:
    """Return settings without loading or persisting secret values."""
    return Settings(database_url=getenv("DATABASE_URL"))
