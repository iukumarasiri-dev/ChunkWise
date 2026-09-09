"""POST /query — answer a question grounded in uploaded documents.

Optionally scoped to a single document. Returns the generated answer plus the
retrieved chunks (filename, page, excerpt, score) that support it.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.llm import LLMError
from app.core.rag import answer_query
from app.db import documents as db
from app.models.schemas import QueryRequest, QueryResponse

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty")

    if req.document_id is not None and db.get_document(req.document_id) is None:
        raise HTTPException(status_code=404, detail="Scoped document not found")

    try:
        return answer_query(question, req.document_id)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
