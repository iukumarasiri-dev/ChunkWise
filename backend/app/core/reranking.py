"""Cross-encoder reranking — the final relevance judge over the candidate pool.

The embedding model and BM25 (see embedding.py, retrieval.py) each score the
query and a passage independently, then compare those two scores — fast
enough to run over the whole corpus, but coarse. A cross-encoder instead reads
the query and passage together in a single forward pass, so it can weigh how
they actually relate to each other. That's far more accurate, but too slow to
run on every chunk in the collection — so it only reranks the smaller
candidate pool hybrid search already narrowed things down to.
"""

from __future__ import annotations

import math
from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.config import get_settings
from app.core.retrieval import Retrieved


@lru_cache(maxsize=1)
def _model() -> CrossEncoder:
    return CrossEncoder(get_settings().reranker_model)


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def rerank(query: str, candidates: list[Retrieved], top_k: int) -> list[Retrieved]:
    """Rescore candidates with the cross-encoder and return the best top_k.

    Replaces each candidate's score with the cross-encoder's own relevance
    estimate (squashed to 0-1 via sigmoid) rather than whatever score hybrid
    search assigned it — that score reflected fused rank position, not
    relevance to this stronger model's judgment.
    """
    if not candidates:
        return []

    pairs = [(query, c.text) for c in candidates]
    raw_scores = _model().predict(pairs)

    ranked = sorted(zip(candidates, raw_scores), key=lambda pair: pair[1], reverse=True)

    return [
        Retrieved(
            document_id=c.document_id,
            filename=c.filename,
            page=c.page,
            text=c.text,
            score=_sigmoid(float(raw_score)),
        )
        for c, raw_score in ranked[:top_k]
    ]
