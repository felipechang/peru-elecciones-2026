"""Environment-backed configuration for the generator package."""
from __future__ import annotations

import math
import os
from dataclasses import dataclass
from urllib.parse import urlparse


class ConfigError(ValueError):
    """Raised when a required environment variable is missing or invalid."""


def _env_str(name: str, default: str) -> str:
    raw = os.environ.get(name)
    if raw is None:
        return default
    stripped = raw.strip()
    return default if stripped == "" else stripped


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw.strip())
    except ValueError as exc:
        raise ConfigError(
            f"{name} must be a number, got {raw!r}"
        ) from exc
    if not math.isfinite(value) or value <= 0:
        raise ConfigError(
            f"{name} must be a positive finite number, got {value!r}"
        )
    return value


def _validate_http_url(name: str, url: str) -> str:
    if not url:
        raise ConfigError(f"{name} must be a non-empty URL")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ConfigError(
            f"{name} must use http or https scheme, got {url!r}"
        )
    if not parsed.netloc:
        raise ConfigError(f"{name} must include a host, got {url!r}")
    return url.rstrip("/")


def _optional_env_str(name: str) -> str | None:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return None
    return raw.strip()


@dataclass(frozen=True)
class GeneratorConfig:
    openrouter_base_url: str
    openrouter_api_key: str
    openrouter_http_referer: str | None
    openrouter_app_title: str | None
    generation_model: str
    openrouter_timeout: float
    ocr_url: str
    ocr_timeout: float


def load_generator_config() -> GeneratorConfig:
    """Read and validate configuration from the process environment."""
    api_key = _env_str("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ConfigError("OPENROUTER_API_KEY is required")
    or_base = _env_str("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    ocr_raw = _env_str("OCR_URL", "http://ocr:9000")
    model = _env_str("GENERATION_MODEL", "")
    if not model:
        raise ConfigError("GENERATION_MODEL must be set to a non-empty model id")

    return GeneratorConfig(
        openrouter_base_url=_validate_http_url("OPENROUTER_BASE_URL", or_base),
        openrouter_api_key=api_key,
        openrouter_http_referer=_optional_env_str("OPENROUTER_HTTP_REFERER"),
        openrouter_app_title=_optional_env_str("OPENROUTER_APP_TITLE"),
        generation_model=model,
        openrouter_timeout=_env_float("OPENROUTER_TIMEOUT", 300.0),
        ocr_url=_validate_http_url("OCR_URL", ocr_raw),
        # Large party PDFs at zoom=2 can exceed two minutes of Tesseract work.
        ocr_timeout=_env_float("OCR_TIMEOUT", 600.0),
    )


_config: GeneratorConfig | None = None


def get_config() -> GeneratorConfig:
    """Return the validated singleton config (loaded on first call)."""
    global _config
    if _config is None:
        _config = load_generator_config()
    return _config
