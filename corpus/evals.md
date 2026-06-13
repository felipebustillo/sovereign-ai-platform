# Evaluation

Retrieval and generation quality are measured with RAGAS, the open-source eval
framework. The evaluation is driven by the local Ollama instance, so scoring
involves no external API calls.

## How it runs

The eval harness reads a golden dataset of questions and reference answers from
`evals/dataset.jsonl`, runs each question through the live RAG pipeline, and
scores the result. Output goes to stdout for CI and cron logs, and can
optionally be pushed to Langfuse so quality trends sit alongside production
traces.

## Metrics

Four RAGAS metrics are reported. Faithfulness checks whether the generated answer
follows from the retrieved context rather than inventing facts. Answer relevancy
checks whether the answer actually addresses the question. Context precision
measures whether the retrieved chunks are relevant, serving as a proxy for
retrieval quality. Context recall measures whether all the information needed to
answer was retrieved, which requires a reference answer.

## Keeping the dataset honest

Golden datasets rot over time. Two practices keep them useful: pull failed user
queries from Langfuse into the dataset with corrected reference answers, and
refresh reference answers when the document corpus changes. A regression on any
metric in CI is a strong signal that a change to chunking, the retriever, the
reranker, or the model broke the pipeline.
