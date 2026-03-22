"""Apply the database schema and seed migrations to the configured PostgreSQL instance.

Runs, in order: ``schema.sql``, ``migrations/seed_parties.sql``,
``migrations/seed_topics.sql``, ``migrations/seed_candidates.sql``,
``migrations/seed_party_sections.sql``.

Usage:
    python -m db.init_db
    # or directly:
    python db/init_db.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import sqlparse

from db.connection import get_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

DB_DIR = Path(__file__).parent
SQL_FILES = [
    DB_DIR / "schema.sql",
    DB_DIR / "migrations" / "seed_parties.sql",
    DB_DIR / "migrations" / "seed_topics.sql",
    DB_DIR / "migrations" / "seed_candidates.sql",
    DB_DIR / "migrations" / "seed_party_sections.sql",
]


_SETVAL_MARKER = "\nSELECT setval(pg_get_serial_sequence("


def _iter_sql_statements(sql: str):
    """Yield executable statements from a script.

    psycopg2 runs only one statement per ``execute()`` call; multi-statement
    scripts would otherwise stop after the first command (e.g. only ``parties``
    created / seeded).

    Large seed scripts are split on the trailing ``SELECT setval(...)`` line so
    we never run ``sqlparse.format`` on huge ``INSERT`` bodies (token limit).
    """
    text = sql.strip()
    if not text:
        return
    idx = text.rfind(_SETVAL_MARKER)
    if idx != -1:
        head, tail = text[:idx].strip(), text[idx + 1 :].strip()
        if head:
            yield head
        if tail:
            yield tail
        return
    for stmt in sqlparse.split(text):
        stripped = stmt.strip()
        if not stripped:
            continue
        if not sqlparse.format(stripped, strip_comments=True).strip():
            continue
        yield stripped


def init_db() -> None:
    log.info("Connecting to database…")
    with get_connection() as conn:
        with conn.cursor() as cur:
            for path in SQL_FILES:
                log.info("Applying %s…", path.name)
                script = path.read_text(encoding="utf-8")
                for stmt in _iter_sql_statements(script):
                    cur.execute(stmt)
    log.info("Schema and migrations applied successfully.")


if __name__ == "__main__":
    try:
        init_db()
    except Exception as exc:
        log.error("Failed to initialise database: %s", exc)
        sys.exit(1)
