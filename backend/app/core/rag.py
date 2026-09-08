"""The RAG pipeline: ingestion and query.

Ingestion:  parse -> chunk -> embed -> store (retrieval.add_chunks)
Query:      embed question -> retrieval.search -> llm.generate -> return
            answer + supporting chunks
"""

# TODO: ingest_document(path, document_id) and answer_query(question, document_id=None)
