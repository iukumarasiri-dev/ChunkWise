"""Vector store access (ChromaDB) — persist chunks and run similarity search.

Persists under settings.chroma_dir. One collection ("chunks") holds every
document's chunks; each chunk's metadata carries document_id (for scoped
queries and deletion), filename, page, and chunk_index.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings
from app.core.chunking import Chunk

_NO_PAGE = -1  # Chroma metadata can't store None; sentinel for DOCX chunks


@dataclass
class Retrieved:
    document_id: str
    filename: str
    page: int | None
    text: str
    score: float


@lru_cache(maxsize=1)
def _collection():
    settings = get_settings()
    client = chromadb.PersistentClient(
        path=str(settings.chroma_dir),
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(
        name="chunks",
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(
    chunks: list[Chunk],
    embeddings: list[list[float]],
    filename: str,
) -> None:
    if not chunks:
        return
    _collection().upsert(
        ids=[c.id for c in chunks],
        embeddings=embeddings,
        documents=[c.text for c in chunks],
        metadatas=[
            {
                "document_id": c.document_id,
                "filename": filename,
                "page": c.page if c.page is not None else _NO_PAGE,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ],
    )


def search(
    query_embedding: list[float],
    top_k: int,
    document_id: str | None = None,
) -> list[Retrieved]:
    where = {"document_id": document_id} if document_id else None
    res = _collection().query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
    )

    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]

    out: list[Retrieved] = []
    for text, meta, dist in zip(docs, metas, dists):
        page = meta.get("page", _NO_PAGE)
        out.append(
            Retrieved(
                document_id=meta["document_id"],
                filename=meta["filename"],
                page=None if page == _NO_PAGE else int(page),
                text=text,
                score=max(0.0, 1.0 - float(dist)),
            )
        )
    return out


def delete_document_chunks(document_id: str) -> None:
    _collection().delete(where={"document_id": document_id})


def count() -> int:
    return _collection().count()
