"""Milestone 2 (part 1) — Ingest parties and generate summaries.

For each party folder:
  1. Read the party name from the folder name.
  2. Extract text from Estatuto and Ideario documents (PDF or image).
     - If a <doc>.md file exists, read it directly (pre-extracted plain text).
     - Otherwise OCR the file via the Tesseract service.
  3. Feed the combined text to the LLM to produce a neutral party summary.
  4. Upsert the party record into the `parties` table.
     Rows that already have a non-empty summary are skipped (no OCR/LLM).

Usage:
    python -m generator.ingest_parties
    python -m generator.ingest_parties --once "Folder Name Under data/"
    python -m generator.ingest_parties --watch 3600
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from db.connection import get_connection
from generator.llm_client import generate
from generator.ocr_client import extract

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"

_SUMMARY_PROMPT = """\
Eres un asistente neutral de análisis político. A continuación se presenta el Estatuto y/o el Ideario de un partido político peruano.

Redacta un resumen descriptivo, objetivo y conciso que explique:
- Los principios y valores del partido.
- Su posición ideológica general.
- Sus principales objetivos programáticos.

No incluyas opiniones ni juicios de valor. Responde únicamente con el resumen, sin encabezados ni listas.

--- DOCUMENTOS ---
{text}
"""


def _extract_text(folder: Path, stem: str) -> str | None:
    """
    Try to obtain text for a document with the given stem inside *folder*.

    Priority:
      1. <stem>.md — pre-extracted plain text
      2. <stem>.pdf / .png / .jpg — OCR via Tesseract service
    """
    md_path = folder / f"{stem}.md"
    if md_path.exists():
        log.debug("  Reading %s from .md file", stem)
        return md_path.read_text(encoding="utf-8").strip()

    for ext in (".pdf", ".png", ".jpg", ".jpeg"):
        doc_path = folder / f"{stem}{ext}"
        if doc_path.exists():
            log.debug("  OCR-extracting %s (%s)", stem, doc_path.name)
            return extract(doc_path)

    return None


def _build_source_text(folder: Path) -> str:
    """Combine Estatuto and Ideario text for a party folder."""
    parts: list[str] = []

    for stem_pattern in ("Estatuto", "Ideario"):
        # Some parties have multiple files: e.g. "Estatuto - Partido X.pdf"
        doc_files = sorted(
            p for p in folder.glob(f"{stem_pattern}*")
            if p.suffix.lower() not in {".md"}
        )

        if not doc_files:
            text = _extract_text(folder, stem_pattern)
            if text:
                parts.append(text)
            continue

        for doc_path in doc_files:
            md_path = doc_path.with_suffix(".md")
            if md_path.exists():
                log.debug("  Reading %s from .md", doc_path.name)
                parts.append(md_path.read_text(encoding="utf-8").strip())
                continue
            log.debug("  OCR-extracting %s", doc_path.name)
            text = extract(doc_path)
            if text:
                parts.append(text)

    return "\n\n---\n\n".join(parts)


def _generate_summary(source_text: str) -> str:
    if not source_text.strip():
        return ""
    # Truncate to avoid overwhelming the LLM context window (~12 000 chars)
    truncated = source_text[:12_000]
    prompt = _SUMMARY_PROMPT.format(text=truncated)
    return generate(prompt)


def _party_has_nonempty_summary(conn, name: str) -> bool:
    """True if a row exists and summary is non-null and not blank after trim."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM parties
            WHERE name = %s
              AND NULLIF(TRIM(summary), '') IS NOT NULL
            LIMIT 1
            """,
            (name,),
        )
        return cur.fetchone() is not None


def _upsert_party(conn, name: str, summary: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO parties (name, summary)
            VALUES (%s, %s)
            ON CONFLICT (name) DO UPDATE
                SET summary = EXCLUDED.summary
            RETURNING id
            """,
            (name, summary),
        )
        row = cur.fetchone()
        return row["id"]


def ingest_parties(data_dir: Path = DATA_DIR, *, party_name: str | None = None) -> None:
    if party_name is not None:
        folder = data_dir / party_name
        if not folder.is_dir():
            raise FileNotFoundError(
                f"No party folder {party_name!r} under {data_dir}"
            )
        party_folders = [folder]
        log.info("Single-party mode: %s", party_name)
    else:
        party_folders = sorted(p for p in data_dir.iterdir() if p.is_dir())
        log.info("Found %d party folders", len(party_folders))

    with get_connection() as conn:
        for folder in party_folders:
            party_name = folder.name
            log.info("Processing party: %s", party_name)

            if _party_has_nonempty_summary(conn, party_name):
                log.info("  Skipping — already has summary in database")
                continue

            source_text = _build_source_text(folder)
            if not source_text:
                log.warning("  No Estatuto/Ideario text found — inserting without summary")

            summary = _generate_summary(source_text)
            party_id = _upsert_party(conn, party_name, summary)
            log.info("  → party_id=%d  summary_len=%d", party_id, len(summary))

            conn.commit()

    log.info("Party ingestion complete.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest parties and summaries into the database.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--once",
        metavar="PARTY",
        help="Ingest only this party (exact name of the folder under data/).",
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
                ingest_parties()
                log.info("Sleeping %.1f s before next pass…", args.watch)
                time.sleep(args.watch)
        else:
            ingest_parties(party_name=args.once)
    except FileNotFoundError as exc:
        log.error("%s", exc)
        sys.exit(1)
    except Exception as exc:
        log.error("Party ingestion failed: %s", exc)
        sys.exit(1)
