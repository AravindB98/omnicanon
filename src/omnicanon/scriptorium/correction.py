"""Canon-aware OCR post-correction.

Generic OCR mangles scripture ("Iet there be light"). But when the target text
belongs to a known canon, we can do better than a spellchecker: match each OCR
line against the corpus and, above a confidence threshold, snap it to the
canonical verse — recovering both clean text AND the verse identity. This is
the corpus and the OCR pipeline reinforcing each other.
"""

from __future__ import annotations

from dataclasses import dataclass

from omnicanon.corpus.loader import CorpusRegistry
from omnicanon.engine.retriever import Retriever
from omnicanon.engine.verifier import similarity


@dataclass
class Correction:
    ocr_text: str
    corrected_text: str
    verse_id: str | None
    confidence: float
    snapped: bool


class CanonCorrector:
    def __init__(self, registry: CorpusRegistry, snap_threshold: float = 0.75) -> None:
        self.registry = registry
        self.retriever = Retriever(registry)
        self.snap_threshold = snap_threshold

    def correct_line(self, ocr_line: str) -> Correction:
        ocr_line = ocr_line.strip()
        if not ocr_line:
            return Correction(ocr_line, ocr_line, None, 0.0, snapped=False)
        hits = self.retriever.search(ocr_line, top_k=3)
        best_verse, best_sim = None, 0.0
        for hit in hits:
            sim = similarity(ocr_line, hit.verse.text)
            if sim > best_sim:
                best_verse, best_sim = hit.verse, sim
        if best_verse and best_sim >= self.snap_threshold:
            return Correction(ocr_line, best_verse.text, best_verse.id, best_sim, snapped=True)
        return Correction(ocr_line, ocr_line, None, best_sim, snapped=False)

    def correct_page(self, ocr_text: str) -> list[Correction]:
        return [self.correct_line(line) for line in ocr_text.splitlines() if line.strip()]
