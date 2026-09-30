"""Declarative base class for future SQLAlchemy models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class that future persisted models will inherit from."""
