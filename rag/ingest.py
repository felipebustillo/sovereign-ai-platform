"""Corpus ingestion: read documents, chunk, embed, upsert to Qdrant.

Markdown and plain text are read directly. PDFs are parsed to text via the
Docling service when ``DOCLING_URL`` is configured, keeping document parsing
inside the trust boundary (no external API calls).
"""
from __future__ import annotations

import os
from pathlib import Path

import requests

from . import ollama_client
from .chunk import chunk_text
from .config import Config, load_config
from .vector_store import VectorStore

TEXT_SUFFIXES = {".md", ".txt", ".markdown"}


def _parse_pdf_via_docling(path: Path, docling_url: str, timeout: int = 300) -> str:
    with path.open("rb") as fh:
        resp = requests.post(
            f"{docling_url}/v1alpha/convert/file",
            files={"files": (path.name, fh, "application/pdf")},
            data={"to_formats": "md"},
            timeout=timeout,
        )
    resp.raise_for_status()
    payload = resp.json()
    return payload["document"]["md_content"]


def read_documents(corpus_dir: str, docling_url: str | None = None) -> list[tuple[str, str]]:
    root = Path(corpus_dir)
    docs: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        source = str(path.relative_to(root))
        if suffix in TEXT_SUFFIXES:
            docs.append((source, path.read_text(encoding="utf-8")))
        elif suffix == ".pdf" and docling_url:
            docs.append((source, _parse_pdf_via_docling(path, docling_url)))
    return docs


def ingest(corpus_dir: str, cfg: Config | None = None) -> int:
    """Ingest ``corpus_dir`` into Qdrant. Returns the number of chunks stored."""
    cfg = cfg or load_config()
    docling_url = os.getenv("DOCLING_URL")

    documents = read_documents(corpus_dir, docling_url)
    if not documents:
        raise SystemExit(f"no ingestible documents found under {corpus_dir!r}")

    chunks = [c for source, text in documents for c in chunk_text(text, source)]
    vectors = ollama_client.embed(
        [c.text for c in chunks], url=cfg.ollama_url, model=cfg.embed_model
    )

    store = VectorStore(cfg.qdrant_url, cfg.qdrant_api_key, cfg.collection)
    store.recreate(dim=len(vectors[0]))
    payloads = [
        {"text": c.text, "source": c.source, "chunk": c.index} for c in chunks
    ]
    store.upsert(vectors, payloads)
    return len(chunks)
