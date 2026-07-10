"""Programmatic citation verification — the heart of Omnicanon.

An answer is only trustworthy if every claim it makes about scripture can be
checked mechanically. The verifier enforces three invariants:

1. RESOLUTION  — every cited reference must resolve to a real verse in the canon.
2. FIDELITY   — every quoted passage must actually appear in the verse it is
                attributed to (normalized fuzzy match above a threshold).
3. COVERAGE   — an answer with no verifiable citation is flagged, not trusted.

This turns "the model sounds confident" into "the canon agrees", which is the
difference between a demo and infrastructure.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from omnicanon.corpus.loader import CorpusRegistry

# Citations appear inline as [kjv:john.1.1] or [quran:1.5]
CITATION_RE = re.compile(r"\[([a-z0-9_-]+:(?:[a-z0-9_-]+\.)?\d+\.\d+)\]", re.IGNORECASE)
# Quotes attributed to the immediately following/preceding citation
QUOTE_RE = re.compile(r"[\"“]([^\"”]{8,})[\"”]\s*\[([a-z0-9_.:-]+)\]", re.IGNORECASE)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


@dataclass
class CitationCheck:
    ref: str
    resolved: bool
    quoted_text: str | None = None
    fidelity: float | None = None  # None when no quote was attributed to this ref
    passed: bool = False


@dataclass
class VerificationResult:
    checks: list[CitationCheck] = field(default_factory=list)
    verified: bool = False
    reason: str = ""

    @property
    def hallucinated_refs(self) -> list[str]:
        return [c.ref for c in self.checks if not c.resolved]

    @property
    def misquotes(self) -> list[str]:
        return [c.ref for c in self.checks if c.resolved and c.fidelity is not None and not c.passed]


class CitationVerifier:
    def __init__(self, registry: CorpusRegistry, fidelity_threshold: float = 0.82) -> None:
        self.registry = registry
        self.fidelity_threshold = fidelity_threshold

    def verify(self, answer: str) -> VerificationResult:
        result = VerificationResult()
        cited = [m.group(1).lower() for m in CITATION_RE.finditer(answer)]
        quotes = {m.group(2).lower(): m.group(1) for m in QUOTE_RE.finditer(answer)}

        if not cited:
            result.reason = "No citations found — answer cannot be verified against the canon."
            return result

        for ref in dict.fromkeys(cited):  # de-dupe, preserve order
            verse = self.registry.get_verse(ref)
            check = CitationCheck(ref=ref, resolved=verse is not None)
            if verse is None:
                check.passed = False
            elif ref in quotes:
                quoted = quotes[ref]
                check.quoted_text = quoted
                # Quoted fragment must appear in the verse: compare against the
                # best-matching window as well as the whole verse.
                check.fidelity = max(
                    similarity(quoted, verse.text),
                    1.0 if normalize(quoted) in normalize(verse.text) else 0.0,
                )
                check.passed = check.fidelity >= self.fidelity_threshold
            else:
                check.passed = True  # reference-only citation: resolution is the requirement
            result.checks.append(check)

        result.verified = all(c.passed for c in result.checks)
        if result.verified:
            result.reason = f"All {len(result.checks)} citation(s) verified against the canon."
        else:
            bad = result.hallucinated_refs + result.misquotes
            result.reason = f"Failed checks: {', '.join(bad)}"
        return result
