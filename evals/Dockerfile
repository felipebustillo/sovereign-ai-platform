FROM python:3.12-slim

WORKDIR /eval

# Pinned versions. Bump deliberately when upgrading RAGAS — the metric
# names and API have shifted across majors.
RUN pip install --no-cache-dir \
    ragas==0.2.10 \
    datasets==3.2.0 \
    langfuse==2.59.5 \
    ollama==0.4.7 \
    qdrant-client==1.13.2 \
    requests==2.32.3

COPY eval_runner.py dataset.jsonl ./

CMD ["python", "eval_runner.py"]
