"""OCR pipeline for scanned manuscripts.

preprocess -> OCR (tesseract, optional dependency) -> canon-aware correction

The OCR step requires the [ocr] extra (pillow + pytesseract + a tesseract
binary). Everything downstream — including correction — is dependency-free, so
correct_text() also works on OCR output produced elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from omnicanon.corpus.loader import CorpusRegistry
from omnicanon.scriptorium.correction import CanonCorrector, Correction


@dataclass
class OcrResult:
    source: str
    raw_text: str
    corrections: list[Correction] = field(default_factory=list)

    @property
    def corrected_text(self) -> str:
        return "\n".join(c.corrected_text for c in self.corrections)

    @property
    def identified_verses(self) -> list[str]:
        return [c.verse_id for c in self.corrections if c.verse_id]


class OcrPipeline:
    def __init__(self, registry: CorpusRegistry, lang: str = "eng") -> None:
        self.corrector = CanonCorrector(registry)
        self.lang = lang

    def process_image(self, image_path: str | Path) -> OcrResult:
        try:
            import pytesseract
            from PIL import Image, ImageFilter, ImageOps
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "OCR requires the [ocr] extra: pip install 'omnicanon[ocr]' "
                "and a tesseract binary (apt install tesseract-ocr)."
            ) from exc

        image = Image.open(image_path)
        image = self._preprocess(image, ImageOps, ImageFilter)
        raw = pytesseract.image_to_string(image, lang=self.lang)
        return self.correct_text(raw, source=str(image_path))

    def correct_text(self, raw_text: str, source: str = "<text>") -> OcrResult:
        return OcrResult(
            source=source,
            raw_text=raw_text,
            corrections=self.corrector.correct_page(raw_text),
        )

    @staticmethod
    def _preprocess(image, ImageOps, ImageFilter):
        image = ImageOps.grayscale(image)
        image = ImageOps.autocontrast(image)
        return image.filter(ImageFilter.MedianFilter(size=3))
