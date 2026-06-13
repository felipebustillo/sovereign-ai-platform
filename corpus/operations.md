# Operations

## Resource sizing

The default resource limits assume a host with 16 GB of RAM. Ollama is capped at
9 GB, the TEI reranker at 4 GB, Docling and Open WebUI at 2 GB each, and Qdrant
at 1 GB. To run larger models, raise the Ollama memory limit in
`docker-compose.yml`.

## First start

On first start, Ollama pulls every model listed in `OLLAMA_LLM_MODELS` and
`OLLAMA_EMBED_MODELS`. On a typical connection this takes five to fifteen
minutes. The TEI reranker downloads its roughly 1.2 GB model on first start as
well.

## Secrets

Every value marked `change-me` in `.env.example` must be rotated before the stack
is exposed to anything. The n8n encryption key is especially important: losing
`N8N_ENCRYPTION_KEY` means losing access to all credentials stored inside n8n.

## GPU

The stack is CPU-only by design. To enable GPU acceleration, add a device
reservation to the Ollama service. The reranker and Docling also have GPU images
available upstream.

## Running the platform

Copy `.env.example` to `.env`, rotate the `change-me` values, then start the
stack with `docker compose up -d`. Ingest a corpus with
`python -m rag ingest <corpus_dir>` and ask questions with
`python -m rag query "<question>"`.
