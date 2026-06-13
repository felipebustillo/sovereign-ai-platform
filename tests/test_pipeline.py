from rag import pipeline
from rag.config import Config
from rag.pipeline import NO_ANSWER, build_prompt, run_pipeline

CFG = Config(
    ollama_url="http://x",
    llm_model="llm",
    embed_model="emb",
    qdrant_url="http://q",
    qdrant_api_key="k",
    tei_url="http://t",
    collection="c",
    retrieve_k=50,
    rerank_k=5,
)


def test_build_prompt_contains_question_contexts_and_guardrail():
    prompt = build_prompt("What port is Qdrant on?", ["Qdrant is on 6333.", "More text."])
    assert "What port is Qdrant on?" in prompt
    assert "Qdrant is on 6333." in prompt
    assert "ONLY the context" in prompt


class _FakeStore:
    """Stand-in for VectorStore that returns canned hits, no network."""

    def __init__(self, hits):
        self._hits = hits

    def __call__(self, *args, **kwargs):  # constructed as VectorStore(...)
        return self

    def search(self, vector, limit):
        return self._hits


def _patch(monkeypatch, hits, reranked, answer):
    monkeypatch.setattr(pipeline.ollama_client, "embed", lambda texts, **kw: [[0.1, 0.2]])
    monkeypatch.setattr(pipeline, "VectorStore", _FakeStore(hits))
    monkeypatch.setattr(pipeline.rerank, "rerank", lambda q, texts, **kw: reranked)
    monkeypatch.setattr(pipeline.ollama_client, "chat", lambda msgs, **kw: answer)


def test_run_pipeline_orchestrates_stages(monkeypatch):
    _patch(
        monkeypatch,
        hits=[("chunk a", 0.9), ("chunk b", 0.8)],
        reranked=["chunk a"],
        answer="  Qdrant listens on port 6333.  ",
    )
    answer, contexts = run_pipeline("which port?", CFG)
    assert answer == "Qdrant listens on port 6333."
    assert contexts == ["chunk a"]


def test_run_pipeline_returns_no_answer_when_retrieval_empty(monkeypatch):
    _patch(monkeypatch, hits=[], reranked=[], answer="should not be called")
    answer, contexts = run_pipeline("anything", CFG)
    assert answer == NO_ANSWER
    assert contexts == []
