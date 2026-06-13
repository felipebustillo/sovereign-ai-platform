# Architecture

The Sovereign AI Platform is a self-hosted retrieval-augmented generation (RAG)
and LLM inference stack that runs on a single CPU-only Docker host. Every
component runs locally and there are no external API calls.

## Inference layer

Inference is served by Ollama on port 11434. The default large language model is
`qwen2.5:7b-instruct-q4_K_M`, with `qwen2.5:3b-instruct-q4_K_M` available as a
lighter alternative. Text embeddings are produced by the `bge-m3` model, also
served through Ollama. Ollama keeps at most two models loaded in memory at once
(`OLLAMA_MAX_LOADED_MODELS=2`) and evicts least-recently-used models beyond that.

## Reranking

A Hugging Face Text Embeddings Inference (TEI) container serves the
`BAAI/bge-reranker-v2-m3` cross-encoder on port 8082. The reranker reorders the
candidate chunks returned by vector search so that the most relevant passages
are passed to the language model.

## Storage

Qdrant is the vector database, exposed on port 6333 for REST and 6334 for gRPC.
Access requires an API key supplied through the `QDRANT_API_KEY` environment
variable. Embeddings are stored with cosine distance.

## Document parsing

Docling runs on port 5001 and converts PDFs and other documents to Markdown so
they can be chunked and embedded. Its web UI is disabled by default.

## Retrieval pipeline

A query flows through five stages: the question is embedded with `bge-m3`; Qdrant
returns the top 50 candidate chunks by vector similarity; the TEI reranker keeps
the best 5; those 5 chunks are inserted into a grounded prompt; and `qwen2.5:7b`
generates the final answer. The number of candidates retrieved and the number
kept after reranking are configurable through `RAG_RETRIEVE_K` and `RAG_RERANK_K`.

## Supporting services

Open WebUI provides a ChatGPT-style frontend for Ollama on port 3000. n8n offers
workflow automation on port 5678, backed by its own PostgreSQL database. Langfuse
provides LLM and RAG observability on port 3001, also backed by PostgreSQL.
