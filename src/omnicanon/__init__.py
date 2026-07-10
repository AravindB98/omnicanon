"""Omnicanon — citation-verified AI infrastructure for the world's sacred texts.

Four pillars:
- corpus:      canonical multi-faith text data model + loaders
- engine:      retrieval with programmatic citation verification (zero-hallucination-by-construction)
- bench:       TheoBench, an LLM benchmark for scriptural accuracy and attribution
- scriptorium: OCR pipeline for digitizing scanned manuscripts, with canon-aware post-correction
"""

__version__ = "0.1.0"

from omnicanon.corpus.loader import CorpusRegistry, load_default_registry
from omnicanon.corpus.models import Verse, VerseRef, Work
from omnicanon.engine.retriever import Retriever
from omnicanon.engine.verifier import CitationVerifier, VerificationResult

__all__ = [
    "CorpusRegistry",
    "load_default_registry",
    "Verse",
    "VerseRef",
    "Work",
    "Retriever",
    "CitationVerifier",
    "VerificationResult",
    "__version__",
]
