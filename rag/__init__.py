"""Sovereign AI Platform — RAG application code.

Retrieval + generation over the self-hosted stack: bge-m3 embeddings and
qwen2.5 generation via Ollama, Qdrant for vector search, and Hugging Face TEI
for reranking. No external API calls — every hop stays inside the trust
boundary described in the project README.
"""

from .pipeline import run_pipeline

__all__ = ["run_pipeline"]
