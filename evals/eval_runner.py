"""RAG eval runner.

Loads ``dataset.jsonl``, runs each question through the real RAG pipeline
(``rag.pipeline.run_pipeline``), scores the results with RAGAS, and prints a
summary. RAGAS is driven by the local Ollama instance (LLM judge + embeddings),
so scoring makes no external API calls. Per-question scores can optionally be
pushed to Langfuse.

Run a smaller, faster subset by setting ``EVAL_LIMIT`` (e.g. ``EVAL_LIMIT=5``)
and a lighter judge with ``RAGAS_JUDGE_MODEL`` (e.g. ``qwen2.5:3b-instruct-q4_K_M``).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from rag.config import load_config
from rag.pipeline import run_pipeline

DATASET = Path(__file__).with_name("dataset.jsonl")


def _load_rows() -> list[dict]:
    rows = [json.loads(line) for line in DATASET.read_text().splitlines() if line.strip()]
    limit = int(os.getenv("EVAL_LIMIT", "0"))
    return rows[:limit] if limit > 0 else rows


def _ragas_models(cfg):
    from langchain_ollama import ChatOllama, OllamaEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper

    judge = os.getenv("RAGAS_JUDGE_MODEL", cfg.llm_model)
    llm = ChatOllama(model=judge, base_url=cfg.ollama_url, temperature=0.0)
    embeddings = OllamaEmbeddings(model=cfg.embed_model, base_url=cfg.ollama_url)
    return LangchainLLMWrapper(llm), LangchainEmbeddingsWrapper(embeddings)


def main() -> int:
    cfg = load_config()
    rows = _load_rows()
    print(f"loaded {len(rows)} dataset rows from {DATASET.name}")

    samples: list[dict] = []
    for i, row in enumerate(rows, start=1):
        answer, contexts = run_pipeline(row["question"], cfg)
        samples.append(
            {
                "user_input": row["question"],
                "response": answer,
                "retrieved_contexts": contexts,
                "reference": row["ground_truth"],
            }
        )
        print(f"  [{i}/{len(rows)}] {row['question'][:55]}... -> {len(contexts)} contexts")

    try:
        from ragas import EvaluationDataset, evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )
    except ImportError as exc:
        print(f"ragas not installed ({exc}); ran pipeline for {len(rows)} rows, skipping scoring.")
        return 0

    if all(not s["response"] for s in samples):
        print("All answers empty -- is the corpus ingested and the stack reachable?")
        return 1

    from ragas.run_config import RunConfig

    # Keep concurrency at or below the host's parallel inference slots: a single
    # CPU host serving a quantized model drowns under RAGAS' default 16 workers,
    # which shows up as TimeoutError -> NaN. Tune via env on bigger hardware.
    run_config = RunConfig(
        timeout=int(os.getenv("EVAL_TIMEOUT", "600")),
        max_workers=int(os.getenv("EVAL_MAX_WORKERS", "2")),
    )

    llm, embeddings = _ragas_models(cfg)
    dataset = EvaluationDataset.from_list(samples)
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=llm,
        embeddings=embeddings,
        run_config=run_config,
    )
    print("\nRAGAS scores:")
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
