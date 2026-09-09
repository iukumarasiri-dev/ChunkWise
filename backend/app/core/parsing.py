"""Extract text from uploaded documents.

PDF via pdfplumber (real 1-based page numbers), DOCX via python-docx (no page
concept, so page is None). Both return a list of PageText holding only the
pages/sections that actually contained text.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pdfplumber
from docx import Document


@dataclass
class PageText:
    page: int | None   # 1-based for PDF, None for DOCX
    text: str


def parse_pdf(path: str | Path) -> list[PageText]:
    pages: list[PageText] = []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append(PageText(page=i, text=text))
    return pages


def parse_docx(path: str | Path) -> list[PageText]:
    doc = Document(str(path))
    parts = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    text = "\n".join(parts).strip()
    return [PageText(page=None, text=text)] if text else []


def parse_document(path: str | Path) -> list[PageText]:
    """Dispatch on file extension. Raises ValueError for unsupported types or
    when no text could be extracted (scanned PDF, empty file)."""
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        pages = parse_pdf(path)
    elif suffix == ".docx":
        pages = parse_docx(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix or '(none)'}")

    if not pages:
        raise ValueError("No extractable text found in document")
    return pages
