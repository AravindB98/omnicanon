"""Pure-stdlib BM25 (Okapi) implementation.

Implemented from scratch rather than pulled in as a dependency: the core
package stays dependency-free, and the ~60 lines below are the whole of the
lexical ranking model. Dense/embedding retrieval plugs in beside this via
Retriever's pluggable scorer interface.
"""

from __future__ import annotations

import math
import re
from collections import Counter

_TOKEN = re.compile(r"[a-z0-9']+")

_STOPWORDS = frozenset(
    "a an and are as at be but by for from he her him his i in is it its me my not of on or "
    "our she so that the thee thou thy to unto upon was we were what which who whom will with ye you your".split()
)


def tokenize(text: str, keep_stopwords: bool = False) -> list[str]:
    tokens = _TOKEN.findall(text.lower())
    if keep_stopwords:
        return tokens
    return [t for t in tokens if t not in _STOPWORDS] or tokens


class BM25Index:
    def __init__(self, documents: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.doc_tokens = [tokenize(d) for d in documents]
        self.doc_lens = [len(t) for t in self.doc_tokens]
        self.avg_len = (sum(self.doc_lens) / len(self.doc_lens)) if self.doc_lens else 0.0
        self.tfs = [Counter(t) for t in self.doc_tokens]
        df: Counter[str] = Counter()
        for tf in self.tfs:
            df.update(tf.keys())
        n = len(self.doc_tokens)
        # BM25+-style floor keeps IDF non-negative for very common terms.
        self.idf = {
            term: max(0.25, math.log((n - dfreq + 0.5) / (dfreq + 0.5) + 1.0))
            for term, dfreq in df.items()
        }

    def score(self, query: str, index: int) -> float:
        tf = self.tfs[index]
        dl = self.doc_lens[index]
        score = 0.0
        for term in tokenize(query):
            if term not in tf:
                continue
            idf = self.idf.get(term, 0.0)
            freq = tf[term]
            denom = freq + self.k1 * (1 - self.b + self.b * dl / (self.avg_len or 1.0))
            score += idf * (freq * (self.k1 + 1)) / denom
        return score

    def search(self, query: str, top_k: int = 5) -> list[tuple[int, float]]:
        scored = [(i, self.score(query, i)) for i in range(len(self.doc_tokens))]
        scored = [(i, s) for i, s in scored if s > 0]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]
