"""End-to-end RAG pipeline: embed -> retrieve -> rerank -> generate.

``run_pipeline(question)`` is the single entry point consumed by the CLI and by
the RAGAS eval harness in ``evals/``. It returns ``(answer, contexts)`` so the
evaluator can score both generation (faithfulness, answer relevancy) and
retrieval (context precision, context recall).
"""
from __future__ import annotations

from . import ollama_client, rerank
from .config import Config, load_config
from .vector_store import VectorStore

PROMPT_TEMPLATE = """You are a precise assistant for the Sovereign AI Platform.
Answer the question using ONLY the context below. If the answer is not contained
in the context, reply exactly: "I don't know based on the provided context."
Do not use outside knowledge.

Context:
{context}

Question: {question}
Answer:"""

NO_ANSWER = "I don't know based on the provided context."


def build_prompt(question: str, contexts: list[str]) -> str:
    """Assemble the grounded prompt. Pure function — unit-tested."""
    joined = "\n\n---\n\n".join(contexts)
    return PROMPT_TEMPLATE.format(context=joined, question=question)


def run_pipeline(question: str, cfg: Config | None = None) -> tuple[str, list[str]]:
    cfg = cfg or load_config()

    query_vector = ollama_client.embed(
        [question], url=cfg.ollama_url, model=cfg.embed_model
    )[0]

    store = VectorStore(cfg.qdrant_url, cfg.qdrant_api_key, cfg.collection)
    candidates = [text for text, _score in store.search(query_vector, limit=cfg.retrieve_k)]
    if not candidates:
        return NO_ANSWER, []

    contexts = rerank.rerank(
        question, candidates, url=cfg.tei_url, top_k=cfg.rerank_k
    )

    answer = ollama_client.chat(
        [{"role": "user", "content": build_prompt(question, contexts)}],
        url=cfg.ollama_url,
        model=cfg.llm_model,
    )
    return answer.strip(), contexts
