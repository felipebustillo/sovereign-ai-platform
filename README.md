# Sovereign AI Platform

Self-hosted RAG and LLM inference stack on Docker Compose, designed to run on a single CPU-only host with explicit trust boundaries. No external API calls — every component (inference, embeddings, reranking, vector DB, observability, document parsing, workflow automation) runs locally.

Built around a simple principle: **agent reasoning is separated from agent action**. The inference host holds no privileged credentials to other systems, so prompts and outputs cannot turn into infrastructure changes by accident.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         AI Host (single Docker host)                         │
├────────────┬───────────────────────────────┬─────────────────────────────────┤
│ INFERENCE  │ ollama (11434)                │ LLMs + embeddings (CPU)         │
│            │ tei-reranker (8082)           │ bge-reranker-v2-m3 (CPU)        │
│            │ docling (5001)                │ PDF / doc parsing               │
├────────────┼───────────────────────────────┼─────────────────────────────────┤
│ STORAGE    │ qdrant (6333 / 6334)          │ Vector DB                       │
├────────────┼───────────────────────────────┼─────────────────────────────────┤
│ FRONTEND   │ open-webui (3000)             │ ChatGPT-like UI for Ollama      │
├────────────┼───────────────────────────────┼─────────────────────────────────┤
│ WORKFLOWS  │ n8n (5678)                    │ Workflow automation             │
│            │ n8n-db                        │ Postgres for n8n                │
├────────────┼───────────────────────────────┼─────────────────────────────────┤
│ OBSERV.    │ langfuse (3001)               │ LLM / RAG traces (v2)           │
│            │ langfuse-db                   │ Postgres for langfuse           │
├────────────┼───────────────────────────────┼─────────────────────────────────┤
│ EVALS      │ rag-eval (on-demand)          │ RAGAS quality checks            │
└────────────┴───────────────────────────────┴─────────────────────────────────┘
```

All HTTP ports bind to the host's internal interface. Public exposure (if any) goes through a separate reverse-proxy host — never directly from the inference host.

## Components

| Service | Port | Auth | Notes |
|---------|------|------|-------|
| Ollama | 11434 | none (network-scoped) | Models pre-pulled by `ollama-init.sh` from `OLLAMA_LLM_MODELS` + `OLLAMA_EMBED_MODELS`. `OLLAMA_MAX_LOADED_MODELS=2`, `OLLAMA_NUM_PARALLEL=2`, `OLLAMA_KEEP_ALIVE=24h`. Hard memory limit 9 GB by default. |
| Qdrant | 6333 (REST), 6334 (gRPC) | API key (`QDRANT_API_KEY`) | 1 GB memory limit. |
| TEI Reranker | 8082 | none | Hugging Face `text-embeddings-inference` serving `BAAI/bge-reranker-v2-m3`. ~1.2 GB model on first start. 4 GB memory limit. |
| Docling | 5001 | none | UI disabled. PDF / doc-to-markdown parsing. 2 GB memory limit. |
| Open WebUI | 3000 | UI signup (first user → admin) | ChatGPT-style frontend for Ollama. 2 GB memory limit. State on `./open-webui` (users, chats, RAG). |
| n8n | 5678 | Basic Auth via UI | Encryption key in `N8N_ENCRYPTION_KEY` — losing it means losing all stored credentials inside n8n. |
| Langfuse | 3001 | UI signup | Self-hosted v2 (single app + Postgres). |

## Quick start

```bash
git clone https://github.com/felipebustillo/sovereign-ai-platform
cd sovereign-ai-platform
cp .env.example .env
# Edit .env: rotate all "change-me" values
docker compose up -d
```

First start pulls the Ollama models declared in `OLLAMA_LLM_MODELS` + `OLLAMA_EMBED_MODELS` (defaults: `qwen2.5:7b-instruct-q4_K_M`, `qwen2.5:3b-instruct-q4_K_M`, `bge-m3`). Expect 5-15 minutes on a typical connection.

Once up:

```bash
# Smoke tests
curl -s http://localhost:11434/api/tags | jq            # Ollama
curl -s -H "api-key: $QDRANT_API_KEY" http://localhost:6333/collections | jq
curl -s http://localhost:8082/health                    # Reranker
curl -s http://localhost:5001/health                    # Docling
```

Web UIs:
- Open WebUI → `http://localhost:3000`
- n8n → `http://localhost:5678`
- Langfuse → `http://localhost:3001`

## RAG pipeline

The retrieval + generation pipeline lives in the `rag/` package: embed the
question with `bge-m3`, retrieve the top `RAG_RETRIEVE_K` chunks from Qdrant,
rerank with TEI down to `RAG_RERANK_K`, then generate a grounded answer with the
Ollama LLM. The same `run_pipeline()` powers both the CLI and the eval harness.

```bash
pip install -r requirements.txt

# point at the stack (in-cluster service names are the defaults)
export QDRANT_API_KEY=...                  # from your .env
export OLLAMA_URL=http://localhost:11434
export QDRANT_URL=http://localhost:6333
export TEI_RERANKER_URL=http://localhost:8082

python -m rag ingest corpus                # chunk + embed + upsert
python -m rag query "What reranker does the platform use?"
```

Answers are grounded: when the corpus does not contain the answer, the pipeline
replies *"I don't know based on the provided context"* instead of guessing. The
reranker is an enhancement, not a hard dependency — if TEI is unreachable the
pipeline degrades to vector-search order rather than failing the query.

## Usage from clients

### Ollama (OpenAI-compatible)

```bash
export OPENAI_BASE_URL="http://localhost:11434/v1"
export OPENAI_API_KEY="ollama"   # ignored, but the SDK requires a value
```

Default LLM is the first entry in `OLLAMA_LLM_MODELS`. Embeddings via `bge-m3`.

### Qdrant

```python
import os
from qdrant_client import QdrantClient

client = QdrantClient(
    url="http://localhost:6333",
    api_key=os.environ["QDRANT_API_KEY"],
)
```

### Reranker

```bash
curl http://localhost:8082/rerank \
    -H 'Content-Type: application/json' \
    -d '{"query": "...", "texts": ["...", "..."]}'
```

### Langfuse

Create a project in the UI, copy the public + secret keys, then:

```python
from langfuse import Langfuse
lf = Langfuse(host="http://localhost:3001", public_key="...", secret_key="...")
```

## Trust boundary

This host is intentionally credential-light. It must not be given:

- SSH keys to other hosts in your infrastructure.
- Source-control tokens with write scope.
- Cloud API keys outside the inference scope (model downloads from Hugging Face are the one exception).

The reasoning is simple: any prompt or tool call that runs on this host should be confined to information operations (read, generate, transform), not infrastructure operations (deploy, rotate, delete). If a workflow needs privileged automation, move that workflow to a separate host on a different security boundary — not to n8n on this host.

## Evals

`evals/` contains a [RAGAS](https://github.com/explodinggradients/ragas)-based harness that runs each golden question through `rag.pipeline.run_pipeline` and scores it on four metrics (faithfulness, answer relevancy, context precision, context recall), driven entirely by the local Ollama instance — no external API calls. Scores can optionally be pushed to Langfuse so the trend sits alongside production traces. See [`evals/README.md`](evals/README.md) for the full workflow.

### Results

Initial run on a 5-question subset of the golden set, every component on a
CPU-only host (`qwen2.5:3b-instruct-q4_K_M` as both generator and RAGAS judge,
`bge-m3` embeddings, `bge-reranker-v2-m3` reranking), 2026-06-13:

| Metric | Score |
|---|---:|
| Faithfulness | 0.71 |
| Answer relevancy | 0.83 |
| Context precision | 0.95 |
| Context recall | 1.00 |

Retrieval is strong (precision 0.95, recall 1.00); faithfulness and answer
relevancy are bounded by the small CPU-resident generator. Reproduce with
`docker compose --profile eval run --rm rag-eval`. Scaling the generator and
judge to the 7B model lifts faithfulness and relevancy; the 9.6 GB host used here
runs the 3B model to stay within memory.

## Customisation

- **Resource limits**: edit `deploy.resources.limits.memory` in `docker-compose.yml`. Defaults assume 16 GB RAM total. Scale up the Ollama limit (currently 9 GB) for larger models.
- **Models**: edit `OLLAMA_LLM_MODELS` and `OLLAMA_EMBED_MODELS` in `.env`. The init script pulls them all; `OLLAMA_MAX_LOADED_MODELS` caps how many stay in RAM concurrently (LRU eviction beyond that).
- **GPU**: this stack is CPU-only by design. To enable GPU, add `deploy.resources.reservations.devices` to the Ollama service. The reranker and Docling also have GPU images upstream.
- **Public exposure**: do not publish ports directly. Front the stack with a reverse proxy on a separate host (Caddy, Traefik, Nginx) with TLS termination there.

## File layout

```
.
├── docker-compose.yml      Service definitions
├── .env.example            Environment template (rotate every "change-me")
├── ollama-init.sh          Entrypoint that pulls models declared in env
├── Makefile                install / test / ingest / query / eval shortcuts
├── requirements.txt        Runtime deps for the rag package
├── rag/                    RAG pipeline
│   ├── ingest.py             Read corpus -> chunk -> embed -> upsert to Qdrant
│   ├── pipeline.py           run_pipeline(): embed -> retrieve -> rerank -> generate
│   ├── chunk.py              Pure, unit-tested text chunking
│   ├── vector_store.py       Qdrant wrapper
│   ├── rerank.py             TEI reranker (with graceful fallback)
│   └── ollama_client.py      Ollama embeddings + chat
├── corpus/                 Sample documents (the platform's own docs)
├── tests/                  Unit tests (chunking, pipeline orchestration, rerank)
├── evals/
│   ├── README.md
│   ├── compose-snippet.yml   Drop-in snippet for the eval service
│   ├── Dockerfile
│   ├── eval_runner.py        Scores run_pipeline() output with RAGAS
│   └── dataset.jsonl         Golden Q&A (one JSON per line)
└── LICENSE
```

Runtime state (not in git) appears on the host after first start:

```
./ollama/                 Model blobs
./qdrant/data/
./tei-reranker/data/
./docling/cache/
./n8n/                    n8n config + workflows
./postgresql/n8n/         n8n Postgres datadir
./postgresql/langfuse/    Langfuse Postgres datadir
./open-webui/             Open WebUI state
```

## License

MIT. See [`LICENSE`](LICENSE).
