"""Qdrant vector store wrapper: collection lifecycle, upsert, search."""
from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


class VectorStore:
    def __init__(self, url: str, api_key: str, collection: str):
        self.client = QdrantClient(url=url, api_key=api_key or None)
        self.collection = collection

    def recreate(self, dim: int) -> None:
        """Drop and recreate the collection — idempotent ingestion."""
        self.client.recreate_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

    def upsert(self, vectors: list[list[float]], payloads: list[dict]) -> None:
        points = [
            PointStruct(id=i, vector=vec, payload=payload)
            for i, (vec, payload) in enumerate(zip(vectors, payloads))
        ]
        self.client.upsert(collection_name=self.collection, points=points)

    def search(self, vector: list[float], limit: int) -> list[tuple[str, float]]:
        """Return ``(text, score)`` for the top ``limit`` matches."""
        result = self.client.query_points(
            collection_name=self.collection,
            query=vector,
            limit=limit,
            with_payload=True,
        )
        return [(p.payload["text"], p.score) for p in result.points]
