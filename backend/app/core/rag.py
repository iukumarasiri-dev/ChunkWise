"""The RAG pipeline: ingestion and query.

Ingestion:  parse -> chunk -> embed -> store, updating the document's status.
Query:      embed question -> hybrid (vector + BM25) search -> cross-encoder
            rerank -> LLM generate -> answer + sources.
"""

from __future__ import annotations

import logging

from app.config import get_settings
from app.core import reranking, retrieval
from app.core.chunking import chunk_pages
from app.core.embedding import embed_query, embed_texts
from app.core.llm import get_llm_provider
from app.core.parsing import parse_document
from app.db import documents as db
from app.models.schemas import QueryResponse, SourceChunk

logger = logging.getLogger(__name__)

_EXCERPT_CHARS = 300


def _excerpt(text: str, limit: int = _EXCERPT_CHARS) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


def ingest_document(document_id: str, path: str, filename: str) -> None:
    """Run the full ingestion pipeline for one uploaded file.

    Always resolves the document's status to "ready" or "failed"; never raises.
    Designed to run in a background task.
    """
    settings = get_settings()
    try:
        pages = parse_document(path)
        chunks = chunk_pages(
            pages, document_id, settings.chunk_size, settings.chunk_overlap
        )
        if not chunks:
            raise ValueError("Document produced no chunks")

        embeddings = embed_texts([c.text for c in chunks])

        # Replace any previous chunks for this id (safe to call when there are none).
        retrieval.delete_document_chunks(document_id)
        retrieval.add_chunks(chunks, embeddings, filename)

        db.set_chunk_count(document_id, len(chunks))
        db.set_status(document_id, "ready")
        logger.info("Ingested %s (%s): %d chunks", filename, document_id, len(chunks))
    except Exception as exc:  # noqa: BLE001 - record any failure, don't crash the task
        logger.exception("Ingestion failed for %s (%s)", filename, document_id)
        db.set_status(document_id, "failed", str(exc))


def answer_query(question: str, document_id: str | None = None) -> QueryResponse:
    settings = get_settings()

    candidates = retrieval.search(
        question, embed_query(question), settings.rerank_pool_size, document_id
    )
    hits = reranking.rerank(question, candidates, settings.top_k)

    answer = get_llm_provider().generate(question, [h.text for h in hits])

    sources = [
        SourceChunk(
            document_id=h.document_id,
            filename=h.filename,
            page=h.page,
            excerpt=_excerpt(h.text),
            score=round(h.score, 4),
        )
        for h in hits
    ]
    return QueryResponse(answer=answer, sources=sources)
