"""LLM provider interface for the answer-generation step.

The concrete provider is chosen via settings.llm_provider. Everything downstream
depends only on the LLMProvider protocol, so adding a provider is a new class
plus one line in _build().

Providers:
  stub   - no model; returns the top retrieved passage (default, zero setup)
  ollama - local model via a running Ollama server
"""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol, Sequence

import httpx

from app.config import get_settings

_OLLAMA_DEFAULT_MODEL = "llama3.1:8b"

# Grounding instructions: answer only from the supplied passages, admit when the
# answer isn't there, don't fall back on the model's own knowledge.
_SYSTEM_PROMPT = (
    "You answer questions using only the numbered context passages given by the "
    "user. If the passages do not contain the answer, reply that you could not "
    "find it in the provided documents. Do not use outside knowledge or guess. "
    "Keep the answer concise and factual, and refer to passage numbers where "
    "helpful."
)


class LLMError(RuntimeError):
    """The configured provider failed (unreachable, bad response, empty output)."""


class LLMProvider(Protocol):
    """Generates a grounded answer from a question and retrieved context chunks."""

    def generate(self, question: str, context_chunks: Sequence[str]) -> str:
        ...


def _user_message(question: str, context_chunks: Sequence[str]) -> str:
    if not context_chunks:
        return f"No context passages were retrieved.\n\nQuestion: {question}"
    numbered = "\n\n".join(
        f"[{i}] {c.strip()}" for i, c in enumerate(context_chunks, start=1)
    )
    return f"Context passages:\n\n{numbered}\n\nQuestion: {question}"


class StubLLMProvider:
    """No real model. Returns the most relevant retrieved passage, framed as an
    answer, so the pipeline and UI are exercisable before a provider is wired in.
    """

    def generate(self, question: str, context_chunks: Sequence[str]) -> str:
        if not context_chunks:
            return (
                "No relevant passages were found in the uploaded documents, "
                "so there's nothing to ground an answer on."
            )
        top = context_chunks[0].strip()
        if len(top) > 600:
            top = top[:600].rsplit(" ", 1)[0] + "…"
        return (
            f"{top}\n\n"
            "— (stub answer: the most relevant retrieved passage, shown as-is. "
            "Set LLM_PROVIDER=ollama for a synthesized response.)"
        )


class OllamaLLMProvider:
    """Calls an Ollama /api/chat endpoint (non-streaming).

    Works with a local server (http://localhost:11434, no key) or Ollama Cloud
    (https://ollama.com, api_key required).
    """

    def __init__(self, host: str, model: str, api_key: str = "") -> None:
        self._url = host.rstrip("/") + "/api/chat"
        self._model = model
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def generate(self, question: str, context_chunks: Sequence[str]) -> str:
        payload = {
            "model": self._model,
            "stream": False,
            "options": {"temperature": 0.2},
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _user_message(question, context_chunks)},
            ],
        }
        try:
            resp = httpx.post(
                self._url, json=payload, headers=self._headers, timeout=120.0
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(
                f"Ollama request to {self._url} failed ({exc}). "
                f"Is the server running and '{self._model}' pulled?"
            ) from exc

        data = resp.json()
        content = (data.get("message") or {}).get("content", "").strip()
        if not content:
            raise LLMError(f"Ollama returned no content: {data!r}")
        return content


def _build(provider: str) -> LLMProvider:
    if provider == "stub":
        return StubLLMProvider()
    if provider == "ollama":
        settings = get_settings()
        return OllamaLLMProvider(
            host=settings.ollama_host,
            model=settings.llm_model or _OLLAMA_DEFAULT_MODEL,
            api_key=settings.ollama_api_key,
        )
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}")


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    return _build(get_settings().llm_provider)
