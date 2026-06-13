"""Pure, deterministic text chunking — no I/O, fully unit-testable.

Paragraph-aware greedy packing: paragraphs (split on blank lines) are packed
into windows of at most ``max_chars``. A paragraph longer than the window is
hard-split with ``overlap`` characters carried between pieces so a fact that
straddles a boundary is not lost.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str
    index: int


def _split_long(s: str, max_chars: int, overlap: int) -> list[str]:
    step = max_chars - overlap
    pieces: list[str] = []
    start = 0
    while start < len(s):
        pieces.append(s[start : start + max_chars])
        start += step
    return pieces


def chunk_text(
    text: str,
    source: str,
    *,
    max_chars: int = 1000,
    overlap: int | None = None,
) -> list[Chunk]:
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap is None:
        overlap = min(150, max_chars // 5)
    if not 0 <= overlap < max_chars:
        raise ValueError("overlap must be in [0, max_chars)")

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    units: list[str] = []
    for para in paragraphs:
        if len(para) > max_chars:
            units.extend(_split_long(para, max_chars, overlap))
        else:
            units.append(para)

    packed: list[str] = []
    buf = ""
    for unit in units:
        candidate = f"{buf}\n\n{unit}" if buf else unit
        if buf and len(candidate) > max_chars:
            packed.append(buf)
            buf = unit
        else:
            buf = candidate
    if buf:
        packed.append(buf)

    return [Chunk(text=t, source=source, index=i) for i, t in enumerate(packed)]
