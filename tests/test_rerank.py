import requests

from rag import rerank as rerank_mod
from rag.rerank import rerank


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_rerank_orders_by_score_and_truncates(monkeypatch):
    payload = [{"index": 0, "score": 0.1}, {"index": 1, "score": 0.9}, {"index": 2, "score": 0.5}]
    monkeypatch.setattr(rerank_mod.requests, "post", lambda *a, **k: _Resp(payload))
    assert rerank("q", ["a", "b", "c"], url="http://t", top_k=2) == ["b", "c"]


def test_rerank_falls_back_to_vector_order_on_failure(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("reranker down")

    monkeypatch.setattr(rerank_mod.requests, "post", boom)
    assert rerank("q", ["a", "b", "c", "d"], url="http://t", top_k=2) == ["a", "b"]


def test_rerank_empty_input_returns_empty():
    assert rerank("q", [], url="http://t", top_k=5) == []
