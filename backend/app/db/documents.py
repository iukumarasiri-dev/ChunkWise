"""SQLite storage for document metadata and ingestion status.

One table: documents(id, filename, status, size_bytes, chunk_count, error, uploaded_at).
status is one of: processing | ready | failed.

Every function opens its own short-lived connection. SQLite handles this fine at
our scale, and it sidesteps the "connection used across threads" problem you'd
hit otherwise (FastAPI runs sync endpoints in a threadpool).
"""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Iterator

from app.config import get_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id           TEXT PRIMARY KEY,
    filename     TEXT NOT NULL,
    status       TEXT NOT NULL,
    size_bytes   INTEGER,
    chunk_count  INTEGER,
    error        TEXT,
    uploaded_at  TEXT NOT NULL
);
"""


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    """Open a connection, commit on success, roll back on error, always close."""
    conn = sqlite3.connect(get_settings().db_path)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "filename": row["filename"],
        "status": row["status"],
        "size_bytes": row["size_bytes"],
        "chunk_count": row["chunk_count"],
        "error": row["error"],
        "uploaded_at": row["uploaded_at"],
    }


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(_SCHEMA)


def create_document(filename: str, size_bytes: int) -> dict:
    doc = {
        "id": uuid.uuid4().hex,
        "filename": filename,
        "status": "processing",
        "size_bytes": size_bytes,
        "chunk_count": None,
        "error": None,
        "uploaded_at": _now(),
    }
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO documents
                (id, filename, status, size_bytes, chunk_count, error, uploaded_at)
            VALUES
                (:id, :filename, :status, :size_bytes, :chunk_count, :error, :uploaded_at)
            """,
            doc,
        )
    return doc


def get_document(doc_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def get_document_by_filename(filename: str) -> dict | None:
    """Case-insensitive lookup by original filename.

    Used to reject duplicate uploads: filenames are how documents are identified
    in the UI (list, scope selector, citations), so we keep them unique.
    """
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE filename = ? COLLATE NOCASE",
            (filename.strip(),),
        ).fetchone()
    return _row_to_dict(row) if row else None


def list_documents() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM documents ORDER BY uploaded_at DESC"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def set_status(doc_id: str, status: str, error: str | None = None) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE documents SET status = ?, error = ? WHERE id = ?",
            (status, error, doc_id),
        )


def set_chunk_count(doc_id: str, count: int) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE documents SET chunk_count = ? WHERE id = ?",
            (count, doc_id),
        )


def delete_document(doc_id: str) -> bool:
    """Returns True if a row was actually removed."""
    with _connect() as conn:
        cur = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        return cur.rowcount > 0


def fail_stale_processing(older_than_seconds: int = 120) -> int:
    """Mark 'processing' rows older than the cutoff as 'failed'.

    A background ingestion task does not survive a server restart, so any row
    still 'processing' afterwards is stuck forever. Called once on startup.
    Returns the number of rows updated.

    uploaded_at is always written by datetime.now(timezone.utc).isoformat(), so
    every value shares one format and a string comparison is a valid time
    comparison.
    """
    cutoff = (
        datetime.now(timezone.utc) - timedelta(seconds=older_than_seconds)
    ).isoformat()
    with _connect() as conn:
        cur = conn.execute(
            """
            UPDATE documents
               SET status = 'failed',
                   error  = 'Ingestion interrupted (server restarted)'
             WHERE status = 'processing'
               AND uploaded_at < ?
            """,
            (cutoff,),
        )
        return cur.rowcount
