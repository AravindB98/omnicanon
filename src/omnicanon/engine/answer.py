"""Grounded answer composition.

Default mode is fully offline and extractive: the answer is BUILT from
retrieved verses, so citations are correct by construction. An optional LLM
composer (Anthropic/OpenAI) can generate fluent prose, but its output must
pass CitationVerifier before it is returned — if verification fails, we fall
back to the extractive answer rather than ship an unverified one.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from omnicanon.corpus.loader import CorpusRegistry
from omnicanon.engine.retriever import Retriever
from omnicanon.engine.verifier import CitationVerifier, VerificationResult


@dataclass
class GroundedAnswer:
    question: str
    answer: str
    verification: VerificationResult
    mode: str  # "extractive" | "llm" | "llm-fallback"


def compose_extractive(question: str, retriever: Retriever, top_k: int = 3,
                       work: str | None = None) -> str:
    hits = retriever.search(question, top_k=top_k, work=work)
    if not hits:
        return "No relevant passages were found in the loaded canon for this question."
    lines = ["The most relevant passages in the canon are:", ""]
    for h in hits:
        lines.append(f'- "{h.verse.text}" [{h.verse.id}]')
    return "\n".join(lines)


class AnswerEngine:
    def __init__(self, registry: CorpusRegistry) -> None:
        self.registry = registry
        self.retriever = Retriever(registry)
        self.verifier = CitationVerifier(registry)

    def answer(self, question: str, top_k: int = 3, work: str | None = None,
               use_llm: bool = False) -> GroundedAnswer:
        extractive = compose_extractive(question, self.retriever, top_k=top_k, work=work)

        if use_llm and (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")):
            llm_answer = self._compose_llm(question, top_k=top_k, work=work)
            if llm_answer:
                verification = self.verifier.verify(llm_answer)
                if verification.verified:
                    return GroundedAnswer(question, llm_answer, verification, mode="llm")
                # Unverified LLM output is never returned — fall back.
                fallback = self.verifier.verify(extractive)
                return GroundedAnswer(question, extractive, fallback, mode="llm-fallback")

        verification = self.verifier.verify(extractive)
        return GroundedAnswer(question, extractive, verification, mode="extractive")

    def _compose_llm(self, question: str, top_k: int, work: str | None) -> str | None:
        hits = self.retriever.search(question, top_k=top_k, work=work)
        if not hits:
            return None
        context = "\n".join(f"[{h.verse.id}] {h.verse.text}" for h in hits)
        prompt = (
            "Answer the question using ONLY the passages below. Every claim must "
            "carry an inline citation in the form [work:book.chapter.verse]. Quote "
            "exactly when quoting.\n\n"
            f"Passages:\n{context}\n\nQuestion: {question}"
        )
        try:
            if os.environ.get("ANTHROPIC_API_KEY"):
                import anthropic

                client = anthropic.Anthropic()
                msg = client.messages.create(
                    model=os.environ.get("OMNICANON_ANTHROPIC_MODEL", "claude-sonnet-5"),
                    max_tokens=600,
                    messages=[{"role": "user", "content": prompt}],
                )
                return msg.content[0].text
            import openai

            client = openai.OpenAI()
            resp = client.chat.completions.create(
                model=os.environ.get("OMNICANON_OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.choices[0].message.content
        except Exception:
            return None
