"""Database URL and engine helpers for the PostgreSQL/PostGIS backend."""

from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine


def database_url_from_env() -> str:
    """Return the configured URL using the installed psycopg 3 driver."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL must be set; keep credentials in backend/.env")
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def create_database_engine() -> Engine:
    return create_engine(database_url_from_env(), pool_pre_ping=True)