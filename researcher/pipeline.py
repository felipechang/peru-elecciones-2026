"""Core researcher pipeline.

Steps:
  1. Fetch all candidates from the database.
  2. For each candidate, search SearXNG for recent news.
  3. Summarize the results with the LLM.
  4. Insert new event records into the `events` table.

Duplicate suppression: an event is skipped if an identical (candidate_id, title)
pair already exists in the database, so re-running the pipeline is idempotent.
"""
from __future__ import annotations

import logging
import time

from db.connection import get_connection
from researcher.config import get_config
from researcher.search_client import search_candidate
from researcher.summarize import summarize_results

log = logging.getLogger(__name__)


def _fetch_candidates(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.name, c.position, p.name AS party_name
            FROM candidates c
                     JOIN parties p ON p.id = c.party_id
            ORDER BY p.name, c.list_order NULLS LAST, c.name
            """
        )
        return list(cur.fetchall())


def _event_exists(conn, candidate_id: int, title: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM events WHERE candidate_id = %s AND title = %s LIMIT 1",
            (candidate_id, title),
        )
        return cur.fetchone() is not None


def _insert_event(
        conn,
        candidate_id: int,
        title: str,
        summary: str,
        source: str,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO events (candidate_id, title, summary, source)
            VALUES (%s, %s, %s, %s)
            """,
            (candidate_id, title, summary or None, source or None),
        )


def run_pipeline() -> None:
    """Execute one full research cycle over all candidates."""
    cfg = get_config()

    with get_connection() as conn:
        candidates = _fetch_candidates(conn)

    log.info("Researcher pipeline started — %d candidates to process", len(candidates))

    new_events_total = 0

    for candidate in candidates:
        candidate_id: int = candidate["id"]
        candidate_name: str = candidate["name"]
        party_name: str = candidate["party_name"]

        log.info("Searching news for: %s (%s)", candidate_name, party_name)

        results = search_candidate(candidate_name)
        if not results:
            log.debug("  No results found — skipping")
            time.sleep(cfg.request_delay)
            continue

        events = summarize_results(candidate_name, results)
        if not events:
            log.debug("  LLM produced no events — skipping")
            time.sleep(cfg.request_delay)
            continue

        new_events = 0
        with get_connection() as conn:
            for event in events:
                title = (event.get("title") or "").strip()
                summary = (event.get("summary") or "").strip()
                source = (event.get("source") or "").strip()

                if not title:
                    continue

                if _event_exists(conn, candidate_id, title):
                    log.debug("  Duplicate event skipped: %r", title)
                    continue

                _insert_event(conn, candidate_id, title, summary, source)
                new_events += 1

        log.info(
            "  → %d new event(s) stored for %s", new_events, candidate_name
        )
        new_events_total += new_events

        time.sleep(cfg.request_delay)

    log.info(
        "Researcher pipeline complete — %d new event(s) stored across %d candidates",
        new_events_total,
        len(candidates),
    )
