"""LLM-based summarization of search results into news-ticker event records."""
from __future__ import annotations

import json
import logging

import httpx

from generator.llm_client import chat_completion
from researcher.config import get_config
from researcher.search_client import SearchResult

log = logging.getLogger(__name__)

_SUMMARIZE_PROMPT = """\
Eres un asistente neutral de noticias electorales peruanas. A continuación se presentan fragmentos de noticias recientes sobre el candidato "{candidate_name}".

Tu tarea es producir un resumen estilo ticker de noticias: una lista de eventos notables, cada uno con un título corto y un resumen de una oración.

Responde ÚNICAMENTE con un objeto JSON con la siguiente estructura (sin texto adicional, sin bloques de código):
{{
  "events": [
    {{
      "title": "Título corto del evento (máx. 80 caracteres)",
      "summary": "Resumen neutral de una oración (máx. 160 caracteres)",
      "source": "URL de la fuente o cadena vacía"
    }}
  ]
}}

Si no hay información relevante o los fragmentos no contienen noticias concretas, devuelve {{"events": []}}.

--- FRAGMENTOS ---
{snippets}
"""


def _build_snippets(results: list[SearchResult]) -> str:
    parts: list[str] = []
    for i, r in enumerate(results, 1):
        lines = [f"[{i}] {r.title}"]
        if r.content:
            lines.append(r.content)
        if r.url:
            lines.append(f"Fuente: {r.url}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


def _call_llm(prompt: str) -> str:
    cfg = get_config()
    return chat_completion(
        prompt,
        model=cfg.summarization_model,
        base_url=cfg.openrouter_base_url,
        api_key=cfg.openrouter_api_key,
        timeout=cfg.openrouter_timeout,
        http_referer=cfg.openrouter_http_referer,
        app_title=cfg.openrouter_app_title,
    )


def _parse_response(raw: str) -> list[dict]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        cleaned = "\n".join(inner).strip()
    data = json.loads(cleaned)
    return data.get("events", [])


def summarize_results(
        candidate_name: str,
        results: list[SearchResult],
) -> list[dict]:
    """
    Summarize *results* for *candidate_name* using the configured LLM.

    Returns a list of dicts, each with keys: ``title``, ``summary``, ``source``.
    Returns an empty list if there are no results or the LLM returns nothing useful.
    """
    if not results:
        return []

    snippets = _build_snippets(results)
    prompt = _SUMMARIZE_PROMPT.format(
        candidate_name=candidate_name,
        snippets=snippets,
    )

    try:
        raw = _call_llm(prompt)
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("OpenRouter request failed for %r: %s", candidate_name, exc)
        return []

    try:
        events = _parse_response(raw)
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        log.warning(
            "Could not parse LLM response for %r: %s\nRaw: %s",
            candidate_name,
            exc,
            raw[:500],
        )
        return []

    return events
