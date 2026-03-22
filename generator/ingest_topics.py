"""Milestone 3 — Topic extraction from Plan de Gobierno documents.

Pipeline:
  1. OCR all "Plan de Gobierno" files across every party folder.
  2. Ask the LLM to derive a shared, canonical list of policy topics that
     covers the main areas found across all plans.
  3. For each party × topic, ask the LLM to extract the relevant section
     from that party's plan (or note that it is absent).
  4. Persist topics → `topics` table and sections → `party_sections` table.

Usage:
    python -m generator.ingest_topics
    python -m generator.ingest_topics --once "Party Name"
    python -m generator.ingest_topics --watch 3600
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from db.connection import get_connection
from generator.llm_client import generate, generate_json
from generator.ocr_client import extract

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_TOPICS_PROMPT = """\
Eres un analista político especializado en programas de gobierno peruanos.

A continuación se presentan fragmentos de los Planes de Gobierno de múltiples partidos políticos que participan en las elecciones peruanas de 2026.

Tu tarea es identificar los TEMAS DE POLÍTICA PÚBLICA más relevantes y recurrentes que aparecen en estos planes. Produce una lista canónica de entre 10 y 20 temas, ordenados de mayor a menor importancia.

{existing_topics_context}

Cada tema debe ser:
- Conciso (2-5 palabras en español)
- Representativo de un área de política pública (e.g. "Salud pública", "Educación", "Seguridad ciudadana")
- Distinto de los demás (sin solapamientos)

Devuelve ÚNICAMENTE un array JSON de strings con los nombres de los temas, sin explicaciones.

--- FRAGMENTOS DE PLANES DE GOBIERNO ---
{text}
"""

_SECTION_PROMPT = """\
Eres un asistente de análisis de programas de gobierno peruanos.

Se te proporciona el texto completo del Plan de Gobierno de un partido político y el nombre de un tema de política pública.

Tu tarea es extraer y resumir lo que el partido propone específicamente sobre ese tema. Si el plan no menciona el tema, responde con la cadena vacía "".

Responde ÚNICAMENTE con el texto extraído/resumido (máximo 400 palabras), sin encabezados ni explicaciones adicionales.

Tema: {topic}

--- PLAN DE GOBIERNO ---
{text}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ocr_plan(folder: Path) -> str | None:
    """Extract text from a Plan de Gobierno file, respecting .override and .md."""
    # Check for .override → use OCR service
    # Check for .md → read directly
    # Otherwise OCR the PDF

    for stem_pattern in ("Plan de Gobierno",):
        md_path = folder / f"{stem_pattern}.md"
        if md_path.exists():
            return md_path.read_text(encoding="utf-8").strip()

        # Some parties may have a single PDF
        pdf_path = folder / f"{stem_pattern}.pdf"
        if pdf_path.exists():
            log.debug("  OCR-extracting Plan de Gobierno for %s", folder.name)
            return extract(pdf_path)

        # Fallback: look for any file starting with "Plan de Gobierno"
        candidates = sorted(folder.glob(f"{stem_pattern}*"))
        doc_files = [
            p for p in candidates
            if p.suffix.lower() not in {".override", ".md"}
        ]
        if doc_files:
            return extract(doc_files[0])

    return None


def _collect_plans(data_dir: Path, party_name: str | None = None) -> dict[str, str]:
    """Return {party_name: plan_text} for all parties that have a plan."""
    plans: dict[str, str] = {}
    if party_name is not None:
        folder = data_dir / party_name
        if not folder.is_dir():
            raise FileNotFoundError(
                f"No party folder {party_name!r} under {data_dir}"
            )
        folders = [folder]
        log.info("Single-party mode: %s", party_name)
    else:
        folders = sorted(p for p in data_dir.iterdir() if p.is_dir())
    for folder in folders:
        text = _ocr_plan(folder)
        if text:
            plans[folder.name] = text
        elif party_name is not None:
            raise FileNotFoundError(
                f"No Plan de Gobierno found for {party_name!r}"
            )
        else:
            log.warning("No Plan de Gobierno found for %s", folder.name)
    return plans


def _fetch_existing_topic_names(conn) -> list[str]:
    """Return topic names already in the database (stable order for prompts)."""
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM topics ORDER BY name")
        return [row["name"] for row in cur.fetchall()]


def _existing_topics_prompt_context(existing_topic_names: list[str]) -> str:
    """Paragraph + bullet list of DB topics for _TOPICS_PROMPT (empty if none)."""
    if not existing_topic_names:
        return ""
    lines = "\n".join(f"- {name}" for name in existing_topic_names)
    return (
        "Ya existen temas registrados en la base de datos. Cuando un ámbito "
        "coincida con uno de esos temas, DEBES usar el nombre exacto de la lista "
        "siguiente (misma ortografía y mayúsculas/minúsculas). No inventes "
        "sinónimos ni variantes para el mismo área (p. ej. no añadas "
        '"Sistema de salud" si ya existe "Salud pública"). Solo añade nombres '
        "nuevos para ámbitos que no estén cubiertos por ningún tema de la lista.\n\n"
        "TEMAS YA REGISTRADOS (reutiliza estos nombres tal cual cuando apliquen):\n"
        f"{lines}"
    )


def _derive_topics(
    plans: dict[str, str], *, existing_topic_names: list[str] | None = None
) -> list[str]:
    """Ask the LLM to produce a canonical topic list from all plans."""
    existing = existing_topic_names or []
    existing_topics_context = _existing_topics_prompt_context(existing)
    # Build a representative sample: first 1 500 chars from each plan
    sample_parts = [
        f"[{name}]\n{text[:1_500]}"
        for name, text in list(plans.items())[:20]  # cap at 20 parties for context
    ]
    combined = "\n\n---\n\n".join(sample_parts)
    prompt = _TOPICS_PROMPT.format(
        existing_topics_context=existing_topics_context,
        text=combined[:15_000],
    )
    result = generate_json(prompt)
    if not isinstance(result, list):
        raise ValueError(f"Expected a JSON array of topic strings, got: {type(result)}")
    return [str(t).strip() for t in result if str(t).strip()]


def _extract_section(plan_text: str, topic: str) -> str:
    """Ask the LLM to extract the section of a plan relevant to a topic."""
    truncated = plan_text[:12_000]
    prompt = _SECTION_PROMPT.format(topic=topic, text=truncated)
    return generate(prompt).strip()


def _upsert_topic(conn, name: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO topics (name)
            VALUES (%s)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            (name,),
        )
        return cur.fetchone()["id"]


def _upsert_party_section(conn, party_id: int, topic_id: int, content: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO party_sections (party_id, topic_id, content)
            VALUES (%s, %s, %s)
            ON CONFLICT (party_id, topic_id) DO UPDATE
                SET content = EXCLUDED.content
            """,
            (party_id, topic_id, content),
        )


def _get_party_id(conn, name: str) -> int | None:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM parties WHERE name = %s", (name,))
        row = cur.fetchone()
        return row["id"] if row else None


def _party_has_all_topic_sections(
    conn, party_id: int, topic_ids: list[int]
) -> bool:
    """True if this party already has a party_sections row for every topic_id."""
    if not topic_ids:
        return False
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(DISTINCT topic_id) AS c
            FROM party_sections
            WHERE party_id = %s AND topic_id IN %s
            """,
            (party_id, tuple(topic_ids)),
        )
        row = cur.fetchone()
        return row["c"] == len(topic_ids)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def ingest_topics(data_dir: Path = DATA_DIR, *, party_name: str | None = None) -> None:
    log.info("Collecting Plan de Gobierno texts…")
    plans = _collect_plans(data_dir, party_name=party_name)
    log.info("Collected plans for %d parties", len(plans))

    with get_connection() as conn:
        existing_topic_names = _fetch_existing_topic_names(conn)
    if existing_topic_names:
        log.info(
            "Found %d existing topic(s) in DB — will steer LLM to reuse names",
            len(existing_topic_names),
        )

    log.info("Deriving canonical topic list via LLM…")
    topics = _derive_topics(plans, existing_topic_names=existing_topic_names)
    log.info("Derived %d topics: %s", len(topics), topics)

    with get_connection() as conn:
        # Persist topics
        topic_ids: dict[str, int] = {}
        for topic_name in topics:
            tid = _upsert_topic(conn, topic_name)
            conn.commit()
            topic_ids[topic_name] = tid
            log.info("  topic '%s' → id=%d", topic_name, tid)

        current_topic_ids = list(topic_ids.values())

        # For each party × topic, extract and store the section
        for party_name, plan_text in plans.items():
            party_id = _get_party_id(conn, party_name)
            if party_id is None:
                log.warning("Party '%s' not in DB — skipping (run ingest_parties first)", party_name)
                continue

            if _party_has_all_topic_sections(conn, party_id, current_topic_ids):
                log.info("Skipping %s — party_sections already complete for current topics", party_name)
                continue

            log.info("Extracting sections for: %s", party_name)
            for topic_name, topic_id in topic_ids.items():
                log.debug("  topic: %s", topic_name)
                content = _extract_section(plan_text, topic_name)
                if content:
                    _upsert_party_section(conn, party_id, topic_id, content)
                    conn.commit()

            log.info("  → sections written for %s", party_name)

    log.info("Topic ingestion complete.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract topics and party plan sections into the database.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--once",
        metavar="PARTY",
        help="Ingest topics/sections only for this party (exact folder name under data/).",
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
                ingest_topics()
                log.info("Sleeping %.1f s before next pass…", args.watch)
                time.sleep(args.watch)
        else:
            ingest_topics(party_name=args.once)
    except FileNotFoundError as exc:
        log.error("%s", exc)
        sys.exit(1)
    except Exception as exc:
        log.error("Topic ingestion failed: %s", exc)
        sys.exit(1)
