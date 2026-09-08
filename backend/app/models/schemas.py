"""Pydantic request/response schemas for the API.

Planned models:
  - DocumentOut      : id, filename, status, chunk_count, uploaded_at
  - UploadResponse   : the created DocumentOut
  - QueryRequest     : question, optional document_id
  - SourceChunk      : document_id, filename, page, excerpt, score
  - QueryResponse    : answer, list[SourceChunk]
"""

# TODO: define the models above.
