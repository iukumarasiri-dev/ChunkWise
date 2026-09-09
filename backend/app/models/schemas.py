"""Pydantic request/response schemas for the API.

Field names here must match what the frontend's client.js sends and reads.
"""

from __future__ import annotations

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    filename: str
    status: str                      # processing | ready | failed
    size_bytes: int | None = None
    chunk_count: int | None = None
    error: str | None = None
    uploaded_at: str                 # ISO 8601 string


class QueryRequest(BaseModel):
    question: str
    document_id: str | None = None   # None = search across all documents


class SourceChunk(BaseModel):
    document_id: str
    filename: str
    page: int | None = None          # None for DOCX (no page concept)
    excerpt: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk] = []