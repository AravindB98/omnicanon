"""Retrieval over the corpus registry."""

from __future__ import annotations

from dataclasses import dataclass

from omnicanon.corpus.loader import CorpusRegistry
from omnicanon.corpus.models import Verse
from omnicanon.engine.bm25 import BM25Index


@dataclass(frozen=True)
class Hit:
    verse: Verse
    score: float


class Retriever:
    """BM25 retriever over all registered works, optionally filtered by work slug.

    Dense retrieval can be layered on by passing rerank_fn (e.g. an embedding
    cosine-similarity reranker); the core stays offline and dependency-free.
    """

    def __init__(self, registry: CorpusRegistry, rerank_fn=None) -> None:
        self.registry = registry
        self.verses = registry.all_verses()
        self.index = BM25Index([v.text for v in self.verses])
        self.rerank_fn = rerank_fn

    def search(self, query: str, top_k: int = 5, work: str | None = None) -> list[Hit]:
        # Over-fetch when filtering so the filter doesn't starve results.
        fetch_k = top_k * 5 if work else top_k
        hits = [
            Hit(verse=self.verses[i], score=score)
            for i, score in self.index.search(query, top_k=fetch_k)
        ]
        if work:
            hits = [h for h in hits if h.verse.ref.work == work][:top_k]
        if self.rerank_fn:
            hits = self.rerank_fn(query, hits)[:top_k]
        return hits
