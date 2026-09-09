"""POST /documents — accept a PDF/DOCX upload and start ingestion.

Validates type and size, saves the bytes under a UUID filename, creates the
metadata row (status "processing"), and hands ingestion to a background task.
The response returns immediately; the frontend polls GET /documents for status.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from app.config import get_settings
from app.core.rag import ingest_document
from app.db import documents as db
from app.models.schemas import DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])

_ALLOWED_EXT = {".pdf", ".docx"}
_MAX_BYTES = 20 * 1024 * 1024  # 20 MB, matches the frontend's client-side cap


@router.post("", response_model=DocumentOut, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> dict:
    filename = (file.filename or "").strip()
    ext = Path(filename).suffix.lower()
    if ext not in _ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(content) > _MAX_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds the 20MB limit")

    # Filenames must be unique — they identify the document in the UI and in
    # citations. To re-upload, delete the existing one first.
    if db.get_document_by_filename(filename) is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A document named '{filename}' already exists. "
                "Delete it before uploading a new version."
            ),
        )

    doc = db.create_document(filename, len(content))

    dest = get_settings().uploads_dir / f"{doc['id']}{ext}"
    try:
        dest.write_bytes(content)
    except OSError as exc:
        db.set_status(doc["id"], "failed", f"Could not save file: {exc}")
        raise HTTPException(status_code=500, detail="Could not save uploaded file")

    background_tasks.add_task(ingest_document, doc["id"], str(dest), filename)
    return doc
