"""Runtime configuration, read from the environment.

Defaults match the in-cluster service names in ``docker-compose.yml`` so the
pipeline runs unmodified inside the compose network. When running from outside
the network (e.g. against the host-published ports, or a remote host), override
the ``*_URL`` variables and ``QDRANT_API_KEY``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    ollama_url: str
    llm_model: str
    embed_model: str
    qdrant_url: str
    qdrant_api_key: str
    tei_url: str
    collection: str
    retrieve_k: int
    rerank_k: int


def load_config() -> Config:
    return Config(
        ollama_url=os.getenv("OLLAMA_URL", "http://ollama:11434"),
        llm_model=os.getenv("OLLAMA_LLM_MODEL", "qwen2.5:7b-instruct-q4_K_M"),
        embed_model=os.getenv("OLLAMA_EMBED_MODEL", "bge-m3"),
        qdrant_url=os.getenv("QDRANT_URL", "http://qdrant:6333"),
        qdrant_api_key=os.getenv("QDRANT_API_KEY", ""),
        tei_url=os.getenv("TEI_RERANKER_URL", "http://tei-reranker:80"),
        collection=os.getenv("RAG_COLLECTION", "sovereign_docs"),
        retrieve_k=int(os.getenv("RAG_RETRIEVE_K", "50")),
        rerank_k=int(os.getenv("RAG_RERANK_K", "5")),
    )
