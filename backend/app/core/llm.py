"""LLM provider interface for the answer-generation step.

The concrete provider is chosen later. Everything downstream depends only on the
``LLMProvider`` protocol below, so swapping in Anthropic / OpenAI / Ollama is a
one-file change plus a factory entry.
"""

from __future__ import annotations

from typing import Protocol, Sequence


class LLMProvider(Protocol):
    """Generates a grounded answer from a question and retrieved context chunks."""

    def generate(self, question: str, context_chunks: Sequence[str]) -> str:
        ...


class StubLLMProvider:
    """Placeholder provider. Returns the assembled context so the pipeline is
    runnable end to end before a real LLM is wired in.
    """

    def generate(self, question: str, context_chunks: Sequence[str]) -> str:
        joined = "\n\n---\n\n".join(context_chunks)
        return (
            "[stub answer — no LLM configured]\n\n"
            f"Question: {question}\n\nRetrieved context:\n{joined}"
        )


def get_llm_provider() -> LLMProvider:
    """Factory: pick a provider based on config (LLM_PROVIDER)."""
    # TODO: read config and branch on provider name.
    return StubLLMProvider()
