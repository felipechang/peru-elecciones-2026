"""OpenRouter client (OpenAI-compatible chat completions API)."""
from __future__ import annotations

import json

import httpx

from generator.config import get_config


def chat_completion(
        prompt: str,
        *,
        model: str,
        base_url: str,
        api_key: str,
        timeout: float,
        http_referer: str | None = None,
        app_title: str | None = None,
) -> str:
    """POST to OpenRouter `/chat/completions` and return assistant message text."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if http_referer:
        headers["HTTP-Referer"] = http_referer
    if app_title:
        headers["X-Title"] = app_title
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = httpx.post(url, json=payload, headers=headers, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise ValueError("OpenRouter response had no choices")
    content = choices[0].get("message", {}).get("content")
    if content is None:
        raise ValueError("OpenRouter response missing message content")
    return str(content).strip()


def generate(prompt: str, model: str | None = None) -> str:
    """Send a prompt to OpenRouter and return the response text."""
    cfg = get_config()
    return chat_completion(
        prompt,
        model=model or cfg.generation_model,
        base_url=cfg.openrouter_base_url,
        api_key=cfg.openrouter_api_key,
        timeout=cfg.openrouter_timeout,
        http_referer=cfg.openrouter_http_referer,
        app_title=cfg.openrouter_app_title,
    )


def generate_json(prompt: str, model: str | None = None) -> object:
    """Send a prompt expecting a JSON response; parse and return the object."""
    raw = generate(prompt, model=model)
    # Strip markdown code fences if the model wraps the JSON
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        # drop first and last fence lines
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        cleaned = "\n".join(inner).strip()
    return json.loads(cleaned)
