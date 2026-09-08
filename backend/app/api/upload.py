"""POST /documents — accept a PDF/DOCX upload and kick off ingestion.

Saves the file to storage, creates a metadata row with status "processing",
then runs the ingestion pipeline (parse -> chunk -> embed -> store) and
updates status to "ready" or "failed".
"""

# TODO: APIRouter with the upload endpoint.
