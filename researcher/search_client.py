"""SearXNG search client for the researcher pipeline."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from researcher.config import get_config

log = logging.getLogger(__name__)


@dataclass
class SearchResult:
    title: str
    url: str
    content: str


def search_candidate(candidate_name: str) -> list[SearchResult]:
    """
    Query SearXNG for recent news about *candidate_name*.

    Returns up to ``config.max_results`` results, each with a title, URL,
    and snippet/content extracted by SearXNG.
    """
    cfg = get_config()
    params = {
        "q": f"{candidate_name} Peru elecciones 2026",
        "format": "json",
        "categories": "news,general",
        "language": "es",
        "time_range": "month",
    }

    try:
        response = httpx.get(
            f"{cfg.searxng_url}/search",
            params=params,
            timeout=cfg.searxng_timeout,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        log.warning("SearXNG request failed for %r: %s", candidate_name, exc)
        return []

    data = response.json()
    raw_results: list[dict] = data.get("results", [])

    results: list[SearchResult] = []
    for item in raw_results[: cfg.max_results]:
        title = (item.get("title") or "").strip()
        url = (item.get("url") or "").strip()
        content = (item.get("content") or item.get("snippet") or "").strip()
        if title or content:
            results.append(SearchResult(title=title, url=url, content=content))

    log.debug(
        "SearXNG returned %d results for %r (kept %d)",
        len(raw_results),
        candidate_name,
        len(results),
    )
    return results
