"""Database connection helpers."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

_DSN_TEMPLATE = (
    "postgresql://{user}:{password}@{host}:{port}/{dbname}"
)


def _dsn() -> str:
    return _DSN_TEMPLATE.format(
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ.get("POSTGRES_DB", "peru_elecciones"),
    )


@contextmanager
def get_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """Yield a psycopg2 connection, committing on success and rolling back on error."""
    conn = psycopg2.connect(_dsn(), cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_engine() -> Engine:
    """Return a SQLAlchemy engine (useful for pandas / bulk operations)."""
    return create_engine(_dsn())
