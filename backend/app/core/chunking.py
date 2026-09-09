"""Split parsed page text into overlapping chunks.

Word-packed character budget: fill a chunk with whole words until adding another
would pass ~chunk_size characters, emit it, then step back far enough to repeat
~chunk_overlap characters at the start of the next chunk. Chunking is done
per page, so every chunk keeps an exact page number for citation.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.parsing import PageText


@dataclass
class Chunk:
    id: str
    document_id: str
    text: str
    page: int | None
    chunk_index: int


def _pack_page(words: list[str], size: int, overlap: int) -> list[str]:
    """Pack one page's words into overlapping ~size-char strings."""
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    n = len(words)

    while start < n:
        # Grow the window until one more word would exceed `size`.
        # `length == 0` guarantees we always take at least one word.
        end = start
        length = 0
        while end < n and (length == 0 or length + 1 + len(words[end]) <= size):
            length += (1 if length else 0) + len(words[end])
            end += 1

        chunks.append(" ".join(words[start:end]))

        if end >= n:
            break

        # Step back from `end` until ~`overlap` chars are re-covered,
        # but always land at least one word past `start` (forward progress).
        back = end
        covered = 0
        while back > start + 1 and covered < overlap:
            back -= 1
            covered += len(words[back]) + 1
        start = back

    return chunks


def chunk_pages(
    pages: list[PageText],
    document_id: str,
    size: int,
    overlap: int,
) -> list[Chunk]:
    if overlap >= size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[Chunk] = []
    index = 0
    for page in pages:
        for text in _pack_page(page.text.split(), size, overlap):
            chunks.append(
                Chunk(
                    id=f"{document_id}:{index}",
                    document_id=document_id,
                    text=text,
                    page=page.page,
                    chunk_index=index,
                )
            )
            index += 1
    return chunks
