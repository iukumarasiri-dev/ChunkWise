"""Embed text with a local sentence-transformers model.

The model (config.embedding_model) loads lazily on first use. That first call
downloads it (~80 MB for all-MiniLM-L6-v2) and takes a few seconds; every call
after reuses the in-memory model.
"""

from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import get_settings


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(get_settings().embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed many strings. Returns one vector (list of floats) per input."""
    if not texts:
        return []
    vectors = _model().encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    return embed_texts([text])[0]


def embedding_dim() -> int:
    return _model().get_sentence_embedding_dimension()
