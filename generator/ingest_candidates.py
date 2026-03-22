"""Milestone 2 (part 2) — Parse Listado de Candidatos and populate the candidates table.

For each party folder:
  1. OCR the Listado.pdf (or reuse cached ``Listado.md`` sidecar).
  2. Parse the ONPE list layout with :func:`generator.listado_parser.parse_listado_text`
     (no LLM).
  3. Insert each candidate into the ``candidates`` table linked to the party.

Parsed candidate fields:
  - name        : full candidate name
  - position    : Presidente, Vicepresidente, Senador, Congresista, Parlamento Andino
  - scope       : ``nacional`` or canonical department name (e.g. ``Lima Metropolitana``)
  - list_order  : order on the list when present

Usage:
    python -m generator.ingest_candidates
    python -m generator.ingest_candidates --once PARTY "Candidate Full Name"
    python -m generator.ingest_candidates --watch 3600
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any

from db.connection import get_connection
from generator.listado_parser import parse_listado_text
from generator.ocr_client import extract

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


def _ocr_listado(folder: Path) -> str | None:
    listado = folder / "Listado.pdf"
    if not listado.exists():
        log.warning("  No Listado.pdf found in %s", folder.name)
        return None
    log.debug("  OCR-extracting Listado.pdf")
    return extract(listado)


def _insert_candidates(conn, party_id: int, candidates: list[dict[str, Any]]) -> int:
    inserted = 0
    with conn.cursor() as cur:
        for c in candidates:
            name = (c.get("name") or "").strip()
            if not name:
                continue
            position = (c.get("position") or "").strip()
            scope = c.get("scope")
            list_order = c.get("list_order")

            # Coerce list_order to int if possible
            if list_order is not None:
                try:
                    list_order = int(list_order)
                except (ValueError, TypeError):
                    list_order = None

            cur.execute(
                """
                INSERT INTO candidates (party_id, name, position, scope, list_order)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (party_id, name, position, scope, list_order),
            )
            inserted += 1
            conn.commit()
    return inserted


def _normalize_name(s: str) -> str:
    return " ".join(s.split()).casefold()


def _pick_single_candidate(
        candidates: list[dict[str, Any]], candidate_name: str
) -> list[dict[str, Any]]:
    needle = _normalize_name(candidate_name)
    for c in candidates:
        name = (c.get("name") or "").strip()
        if name and _normalize_name(name) == needle:
            return [c]
    raise ValueError(
        f"No candidate matching {candidate_name!r} in parsed list "
        f"({len(candidates)} entries)"
    )


def _get_party_id(conn, party_name: str) -> int | None:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM parties WHERE name = %s", (party_name,))
        row = cur.fetchone()
        return row["id"] if row else None


def ingest_candidates(
        data_dir: Path = DATA_DIR,
        *,
        party_name: str | None = None,
        candidate_name: str | None = None,
) -> None:
    if candidate_name is not None and party_name is None:
        raise ValueError("candidate_name requires party_name (--once PARTY NAME)")

    if party_name is not None:
        folder = data_dir / party_name
        if not folder.is_dir():
            raise FileNotFoundError(
                f"No party folder {party_name!r} under {data_dir}"
            )
        party_folders = [folder]
        log.info("Single-candidate mode: party=%s name=%s", party_name, candidate_name)
    else:
        party_folders = sorted(p for p in data_dir.iterdir() if p.is_dir())
        log.info("Found %d party folders", len(party_folders))

    with get_connection() as conn:
        for folder in party_folders:
            pname = folder.name
            log.info("Processing candidates for: %s", pname)

            party_id = _get_party_id(conn, pname)
            if party_id is None:
                log.warning("  Party not found in DB — skipping (run ingest_parties first)")
                continue

            raw_text = _ocr_listado(folder)
            if not raw_text:
                continue

            candidates = parse_listado_text(raw_text)
            if not candidates:
                log.warning("  No candidates parsed for %s", pname)
                continue

            if candidate_name is not None:
                candidates = _pick_single_candidate(candidates, candidate_name)

            count = _insert_candidates(conn, party_id, candidates)
            log.info("  → inserted %d candidates", count)

    log.info("Candidate ingestion complete.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest candidates from Listado.pdf into the database.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--once",
        nargs=2,
        metavar=("PARTY", "CANDIDATE"),
        help='Ingest one candidate: party folder name under data/ and full name as on the list (e.g. --once "My Party" "JUAN PÉREZ").',
    )
    mode.add_argument(
        "--watch",
        type=float,
        metavar="SECONDS",
        help="Re-run after each full pass, sleeping SECONDS between passes.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    try:
        if args.watch is not None:
            while True:
                ingest_candidates()
                log.info("Sleeping %.1f s before next pass…", args.watch)
                time.sleep(args.watch)
        elif args.once is not None:
            p, c = args.once
            ingest_candidates(party_name=p, candidate_name=c)
        else:
            ingest_candidates()
    except (FileNotFoundError, ValueError) as exc:
        log.error("%s", exc)
        sys.exit(1)
    except Exception as exc:
        log.error("Candidate ingestion failed: %s", exc)
        sys.exit(1)
