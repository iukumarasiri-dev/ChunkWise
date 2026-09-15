"""Vector store access (ChromaDB) — persist chunks and run hybrid search.

Persists under settings.chroma_dir. One collection ("chunks") holds every
document's chunks; each chunk's metadata carries document_id (for scoped
queries and deletion), filename, page, and chunk_index.

Retrieval is hybrid: a dense vector search (Chroma/cosine) catches semantic
matches, a sparse BM25 keyword search (in-memory, rebuilt from the collection)
catches exact terms embeddings tend to blur (IDs, names, acronyms). The two
rankings are merged with Reciprocal Rank Fusion (RRF) rather than averaging
their raw scores, since cosine similarity and BM25 scores live on unrelated
scales and RRF only needs each list's rank order.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

import chromadb
from chromadb.config import Settings as ChromaSettings
from rank_bm25 import BM25Okapi

from app.config import get_settings
from app.core.chunking import Chunk

_NO_PAGE = -1  # Chroma metadata can't store None; sentinel for DOCX chunks

_RRF_K = 60  # standard RRF damping constant; de-weights lower ranks smoothly
_CANDIDATE_POOL = 20  # hits pulled from each retriever before fusing


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


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


@dataclass
class _Bm25Index:
    bm25: BM25Okapi
    ids: list[str]
    texts: list[str]
    metas: list[dict]


_bm25_index: _Bm25Index | None = None


def _invalidate_bm25() -> None:
    global _bm25_index
    _bm25_index = None


def _get_bm25_index() -> _Bm25Index | None:
    """Lazily (re)builds the BM25 index from whatever is currently in Chroma.

    Rebuilt on first use after any add/delete (see _invalidate_bm25 callers)
    rather than kept incrementally in sync — simple, and fine at this corpus
    scale; a large collection would want a persisted/incremental index instead.
    """
    global _bm25_index
    if _bm25_index is None:
        data = _collection().get(include=["documents", "metadatas"])
        ids, texts, metas = data["ids"], data["documents"], data["metadatas"]
        if not texts:
            return None
        _bm25_index = _Bm25Index(
            bm25=BM25Okapi([_tokenize(t) for t in texts]),
            ids=ids,
            texts=texts,
            metas=metas,
        )
    return _bm25_index


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
    _invalidate_bm25()


def _vector_candidates(
    query_embedding: list[float],
    top_k: int,
    document_id: str | None,
) -> list[tuple[str, str, dict]]:
    """Ranked (id, text, metadata) triples, best first."""
    where = {"document_id": document_id} if document_id else None
    res = _collection().query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
    )
    if not res["ids"][0]:
        return []
    return list(zip(res["ids"][0], res["documents"][0], res["metadatas"][0]))


def _keyword_candidates(
    query: str,
    top_k: int,
    document_id: str | None,
) -> list[tuple[str, str, dict]]:
    """Ranked (id, text, metadata) triples, best first."""
    index = _get_bm25_index()
    if index is None:
        return []
    scores = index.bm25.get_scores(_tokenize(query))
    candidates = list(zip(index.ids, index.texts, index.metas, scores))
    if document_id:
        candidates = [c for c in candidates if c[2]["document_id"] == document_id]
    candidates.sort(key=lambda c: c[3], reverse=True)
    return [(cid, text, meta) for cid, text, meta, _score in candidates[:top_k] if _score > 0]


def search(
    query_text: str,
    query_embedding: list[float],
    top_k: int,
    document_id: str | None = None,
) -> list[Retrieved]:
    pool = max(top_k * 4, _CANDIDATE_POOL)
    vector_hits = _vector_candidates(query_embedding, pool, document_id)
    keyword_hits = _keyword_candidates(query_text, pool, document_id)

    rrf_scores: dict[str, float] = {}
    chunk_info: dict[str, tuple[str, dict]] = {}

    for hits in (vector_hits, keyword_hits):
        for rank, (cid, text, meta) in enumerate(hits):
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (_RRF_K + rank + 1)
            chunk_info.setdefault(cid, (text, meta))

    ranked = sorted(rrf_scores.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    if not ranked:
        return []

    # RRF scores aren't a 0-1 similarity, just a fused rank; min-max normalize
    # within this result set so the UI's "% match" stays a meaningful relative
    # signal (best of these results ~100%, worst ~0%).
    raw = [score for _, score in ranked]
    lo, hi = min(raw), max(raw)
    spread = hi - lo

    out: list[Retrieved] = []
    for cid, score in ranked:
        text, meta = chunk_info[cid]
        page = meta.get("page", _NO_PAGE)
        out.append(
            Retrieved(
                document_id=meta["document_id"],
                filename=meta["filename"],
                page=None if page == _NO_PAGE else int(page),
                text=text,
                score=1.0 if spread == 0 else (score - lo) / spread,
            )
        )
    return out


def delete_document_chunks(document_id: str) -> None:
    _collection().delete(where={"document_id": document_id})
    _invalidate_bm25()


def count() -> int:
    return _collection().count()
