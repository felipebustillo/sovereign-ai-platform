.PHONY: install test ingest query eval

# Local dev venv for the rag package (ingestion + query).
VENV ?= .venv
PY := $(VENV)/bin/python

install:
	python -m venv $(VENV)
	$(PY) -m pip install -r requirements.txt pytest

test:
	PYTHONPATH=. $(PY) -m pytest -q

# Ingest the sample corpus into Qdrant. Override with: make ingest CORPUS=path
CORPUS ?= corpus
ingest:
	PYTHONPATH=. $(PY) -m rag ingest $(CORPUS)

# Ask a question: make query Q="What reranker does the platform use?"
query:
	PYTHONPATH=. $(PY) -m rag query "$(Q)"

# Run the RAGAS eval harness in its container (needs the stack up).
eval:
	docker compose --profile eval run --rm rag-eval
