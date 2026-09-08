"""Vector store access (ChromaDB) — add chunks and run similarity search.

Persists to STORAGE_DIR/chroma. Supports scoping a query to a single document
via metadata filter.
"""

# TODO: add_chunks(chunks, embeddings) / search(query_embedding, top_k, document_id=None)
