"""POST /query — answer a question grounded in uploaded documents.

Optionally scoped to a single document. Returns the generated answer plus the
retrieved chunks (source file, page number, excerpt) that support it.
"""

# TODO: APIRouter with the query endpoint; delegates to core.rag.
