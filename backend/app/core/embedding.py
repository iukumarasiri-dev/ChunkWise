"""Embed text with a local sentence-transformers model.

The model name comes from config (EMBEDDING_MODEL). Loaded once and reused.
"""

# TODO: embed_texts(texts) -> list[list[float]]; lazy-load the SentenceTransformer.
