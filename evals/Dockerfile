FROM python:3.12-slim

WORKDIR /app

# Pinned versions. Bump deliberately when upgrading RAGAS — the metric names and
# API have shifted across majors. langchain-ollama keeps RAGAS scoring on the
# local Ollama instance (no external API calls).
RUN pip install --no-cache-dir \
    ragas==0.2.10 \
    datasets==3.2.0 \
    langchain-ollama==0.2.3 \
    langfuse==2.59.5 \
    qdrant-client==1.13.2 \
    requests==2.32.3

# Build context is the repo root (see evals/compose-snippet.yml) so the rag
# package and the eval harness both land in the image.
COPY rag/ ./rag/
COPY evals/eval_runner.py evals/dataset.jsonl ./evals/

ENV PYTHONPATH=/app
CMD ["python", "evals/eval_runner.py"]
