from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.core import retrieval
from app.db import documents as db
from app.models.schemas import DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
def list_documents():
    return db.list_documents()


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str):
    doc = db.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{doc_id}", status_code=204)
def delete_document(doc_id: str):
    if db.get_document(doc_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")

    retrieval.delete_document_chunks(doc_id)

    uploads = get_settings().uploads_dir
    for path in uploads.glob(f"{doc_id}.*"):
        path.unlink(missing_ok=True)

    db.delete_document(doc_id)
    return None
