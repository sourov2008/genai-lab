"""SQLAlchemy declarative base for ClauseDesk models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared mapper registry and metadata for all ORM models."""

    pass
