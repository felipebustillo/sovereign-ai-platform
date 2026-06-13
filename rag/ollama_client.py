"""Thin Ollama HTTP client — embeddings (bge-m3) and chat (qwen2.5).

Uses ``requests`` directly rather than a vendored SDK: the surface is two
endpoints and keeping it explicit makes the trust boundary auditable.
"""
from __future__ import annotations

import requests


def embed(texts: list[str], *, url: str, model: str, timeout: int = 180) -> list[list[float]]:
    """Batch-embed ``texts``. Returns one vector per input, in order."""
    resp = requests.post(
        f"{url}/api/embed",
        json={"model": model, "input": texts},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"]


def chat(
    messages: list[dict],
    *,
    url: str,
    model: str,
    timeout: int = 600,
    temperature: float = 0.0,
) -> str:
    """Single non-streamed chat completion. Returns the assistant message text."""
    resp = requests.post(
        f"{url}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]
