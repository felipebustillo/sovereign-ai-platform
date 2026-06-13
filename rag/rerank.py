"""Reranking via Hugging Face TEI (``bge-reranker-v2-m3``).

The vector search casts a wide net (``retrieve_k``); the cross-encoder reranker
then picks the ``top_k`` chunks that actually answer the query. This two-stage
retrieve-then-rerank pattern is the single biggest lever on context precision.
"""
from __future__ import annotations

import sys

import requests


def rerank(
    query: str,
    texts: list[str],
    *,
    url: str,
    top_k: int,
    timeout: int = 180,
) -> list[str]:
    """Return the ``top_k`` of ``texts`` most relevant to ``query``, best first.

    The reranker is an enhancement, not a hard dependency: if TEI is unreachable
    the pipeline degrades gracefully to the vector-search order (``texts`` is
    already sorted by similarity) rather than failing the whole query.
    """
    if not texts:
        return []
    try:
        resp = requests.post(
            f"{url}/rerank",
            json={"query": query, "texts": texts},
            timeout=timeout,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[rerank] TEI unavailable ({exc}); falling back to vector order", file=sys.stderr)
        return texts[:top_k]
    ranked = sorted(resp.json(), key=lambda r: r["score"], reverse=True)
    return [texts[r["index"]] for r in ranked[:top_k]]
