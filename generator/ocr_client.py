"""HTTP client for the Tesseract OCR service.

Caching: every successful extraction is written to a ``<original_name>.md``
sidecar file next to the source document.  Subsequent calls to :func:`extract`
return the cached text immediately, skipping the OCR service entirely.
"""
from __future__ import annotations

import logging
from pathlib import Path

import httpx

from generator.config import get_config

log = logging.getLogger(__name__)


def _base_url() -> str:
    return get_config().ocr_url


def _http_timeout() -> httpx.Timeout:
    """Long read/write for OCR; bounded connect so misconfigured URLs fail fast."""
    cfg = get_config()
    read = cfg.ocr_timeout
    connect = min(60.0, read)
    return httpx.Timeout(connect=connect, read=read, write=read, pool=read)


def _cache_path(path: Path) -> Path:
    """Return the sidecar .md path for *path*."""
    return path.with_suffix(".md")


def _read_cache(path: Path) -> str | None:
    cache = _cache_path(path)
    if cache.exists():
        log.debug("OCR cache hit: %s", cache)
        return cache.read_text(encoding="utf-8")
    return None


def _write_cache(path: Path, text: str) -> None:
    cache = _cache_path(path)
    cache.write_text(text, encoding="utf-8")
    log.debug("OCR result cached: %s", cache)


def extract_pdf(path: Path, language: str = "spa", zoom: float = 2.0) -> str:
    """Send a PDF file to the OCR service and return the full extracted text."""
    url = f"{_base_url()}/ocr/pdf"
    with path.open("rb") as fh:
        response = httpx.post(
            url,
            files={"file": (path.name, fh, "application/pdf")},
            data={"language": language, "zoom": str(zoom)},
            timeout=_http_timeout(),
        )
    response.raise_for_status()
    pages = response.json()["pages"]
    return "\n\n".join(p["text"] for p in pages).strip()


def extract_image(path: Path, language: str = "spa") -> str:
    """Send an image file to the OCR service and return the extracted text."""
    url = f"{_base_url()}/ocr/image"
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    with path.open("rb") as fh:
        response = httpx.post(
            url,
            files={"file": (path.name, fh, mime)},
            data={"language": language},
            timeout=_http_timeout(),
        )
    response.raise_for_status()
    pages = response.json()["pages"]
    return "\n\n".join(p["text"] for p in pages).strip()


def extract(path: Path, language: str = "spa") -> str:
    """Extract text from a PDF or image file, using a cached .md sidecar when available.

    On a cache miss the OCR service is called and the result is written to
    ``<path>.md`` (same directory, same stem, ``.md`` extension) for future
    calls.
    """
    cached = _read_cache(path)
    if cached is not None:
        return cached

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text = extract_pdf(path, language=language)
    elif suffix in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}:
        text = extract_image(path, language=language)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    _write_cache(path, text)
    return text
