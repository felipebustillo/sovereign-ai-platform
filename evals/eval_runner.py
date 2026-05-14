"""
RAG eval runner. Loads dataset.jsonl, runs each question through the live
retrieval+generation pipeline, scores with RAGAS, optionally posts per-row
scores to Langfuse.

Replace `run_pipeline()` with the real retriever + generator for your
application. Today it returns a stub so the container starts and the
scaffolding can be exercised end-to-end.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

DATASET = Path(__file__).with_name("dataset.jsonl")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_LLM = os.getenv("OLLAMA_LLM_MODEL", "qwen2.5:7b-instruct-q4_K_M")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://langfuse:3000")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")


def run_pipeline(question: str) -> tuple[str, list[str]]:
    """
    Returns (answer, contexts). Stub until you wire up retrieval+generation.

    A real implementation:
      1. Embed `question` with bge-m3 via Ollama
      2. Query Qdrant for top-50 matches
      3. Rerank with bge-reranker-v2-m3 via TEI -> keep top-5
      4. Build a prompt with those 5 contexts and call qwen2.5:7b
      5. Return the generated answer + the 5 context strings

    Returning ("", []) here makes RAGAS produce 0 scores -- a clear
    signal that the pipeline isn't wired up yet, not a silent failure.
    """
    return "", []


def main() -> int:
    rows = [json.loads(line) for line in DATASET.read_text().splitlines() if line.strip()]
    print(f"loaded {len(rows)} dataset rows from {DATASET.name}")

    # Run pipeline for each question
    for r in rows:
        answer, contexts = run_pipeline(r["question"])
        r["answer"] = answer
        r["contexts"] = contexts

    # Score with RAGAS. Imports are deferred so a missing ragas install
    # doesn't crash the smoke-test path that runs run_pipeline only.
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )
    except ImportError as e:
        print(f"ragas not installed ({e}); skipping scoring. Pipeline ran for {len(rows)} rows.")
        return 0

    if all(not r["answer"] for r in rows):
        print("All answers empty -- pipeline is still a stub. Wire run_pipeline() to score.")
        return 0

    ds = Dataset.from_list(rows)
    result = evaluate(
        ds,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
