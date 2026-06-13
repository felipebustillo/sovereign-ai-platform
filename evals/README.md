# RAG evals

Periodic, automatable quality checks for the RAG pipeline. Uses [RAGAS](https://github.com/explodinggradients/ragas) — the standard open-source eval framework — driven by the local Ollama instance, no external API calls.

Designed to be lightweight: a single Python container reads a golden dataset (`dataset.jsonl`), runs each question through the live pipeline, and scores the result on four RAGAS metrics. Output goes to stdout (for CI / cron logs) and optionally to Langfuse (`POST /api/public/scores`) so the trend is visible alongside production traces.

## How it wires to the pipeline

`eval_runner.py` calls `rag.pipeline.run_pipeline(question)` — the same retrieval + generation path used by the CLI and any application code. There is no separate eval-only pipeline to drift out of sync: the eval scores exactly what production serves. RAGAS itself is driven by the local Ollama instance (judge LLM + embeddings via `langchain-ollama`), so scoring makes no external API calls.

On a single CPU host, keep `EVAL_MAX_WORKERS` at or below the model's parallel inference slots (`OLLAMA_NUM_PARALLEL`) — RAGAS' default 16 workers drown a quantized CPU model and surface as `TimeoutError`. Use `EVAL_LIMIT` to score a faster subset and `RAGAS_JUDGE_MODEL` to pick a lighter judge.

## Files

| File | Purpose |
|---|---|
| `dataset.jsonl` | Golden Q&A — one JSON object per line: `{question, ground_truth, contexts?}`. Start with 20-50 examples, grow over time. |
| `eval_runner.py` | Loads the dataset, runs the pipeline for each question, scores via RAGAS, prints a summary, optionally pushes per-question scores to Langfuse. |
| `Dockerfile` | Pins the Python deps (ragas, datasets, langchain-ollama, qdrant-client) and copies the `rag/` package into the image. |
| `compose-snippet.yml` | The service entry to drop into the root `docker-compose.yml` once the eval is live (kept here, not in main compose, so it doesn't run as a long-lived container — invoke on-demand with `docker compose run --rm rag-eval`). |

## Metrics (RAGAS defaults)

- **faithfulness** — does the generated answer follow from the retrieved context, or is it making things up?
- **answer_relevancy** — does the answer actually address the question?
- **context_precision** — are the retrieved chunks relevant? (proxy for retrieval quality)
- **context_recall** — did we retrieve all the relevant info needed to answer? (requires `ground_truth`)

A regression on any of these in CI is a strong signal that something (retriever weights, chunking, model swap, reranker config) broke the pipeline.

## How to run

```bash
# from the repo root, with the stack already up
docker compose --profile eval run --rm rag-eval
```

For a cron job (e.g. nightly, results to Langfuse):

```cron
0 3 * * * cd /path/to/sovereign-ai-platform && docker compose run --rm rag-eval >> /var/log/rag-eval.log 2>&1
```

## Tuning the dataset

Golden datasets rot. Two practices keep them honest:

1. **Pull failed user queries.** Any query that produced a wrong/poor answer in production (visible in Langfuse) → add to `dataset.jsonl` with the correct `ground_truth`. This naturally moves the test distribution toward where the pipeline is weakest.
2. **Refresh the contexts.** If your document corpus drifts (new contracts, updated policies), the `ground_truth` answers may go stale. Re-validate every few months.
