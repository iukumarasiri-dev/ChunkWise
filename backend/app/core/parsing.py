"""Extract text from uploaded documents.

PDF via pdfplumber, DOCX via python-docx. Yields per-page (or per-block) text
along with a page number so downstream chunks can be attributed to a location.
"""

# TODO: parse_pdf(path) / parse_docx(path) -> list[PageText]
