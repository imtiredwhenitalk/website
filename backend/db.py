"""Database engine, session and initialization helpers.

This module provides a small, well-tested surface for working with SQLAlchemy
in the project: engine creation that respects `DATABASE_URL`, a session
factory, a generator-style `get_db()` for dependency injection, and helpers
to initialize or access the engine/session programmatically.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

# Prefer settings.DATABASE_URL if available, otherwise fall back to env or sqlite
try:
    # optional import — some environments provide `innovation.settings`
    from innovation import settings  # type: ignore

    DATABASE_URL = getattr(settings, "DATABASE_URL", os.getenv("DATABASE_URL", "sqlite:///./website.db"))
except Exception:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./website.db")

API_PREFIX = "/api/v1"

# SQLite needs connect_args; other backends ignore it
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite:") else {}

# Engine and session factory
engine: Engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def get_db() -> Generator:
    """Yield a database session and ensure it's closed afterwards.

    Intended for use as a dependency in web frameworks (FastAPI/Starlette) or
    as a context-managed generator in scripts.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Return a new session instance (not a generator).

    Use this when you need a session object directly (tests, scripts).
    """
    return SessionLocal()


def get_db_engine() -> Engine:
    """Return the SQLAlchemy engine for low-level operations."""
    return engine


def init_db() -> None:
    """Create all tables for models registered on `Base`."""
    Base.metadata.create_all(bind=engine)


__all__ = ["Base", "engine", "SessionLocal", "get_db", "get_db_session", "get_db_engine", "init_db", "API_PREFIX"]
