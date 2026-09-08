"""SQLite storage for document metadata and ingestion status.

One table: documents(id, filename, status, chunk_count, uploaded_at).
status is one of: processing | ready | failed.
"""

# TODO: init_db(), create_document(), set_status(), set_chunk_count(),
#       list_documents(), get_document(), delete_document()
