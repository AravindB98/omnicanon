import pytest

from omnicanon.corpus.loader import load_default_registry
from omnicanon.scriptorium.pipeline import OcrPipeline


@pytest.fixture(scope="module")
def pipeline():
    return OcrPipeline(load_default_registry())


def test_ocr_noise_snaps_to_canonical_verse(pipeline):
    # Classic OCR confusions: I/l, rn/m, missing punctuation.
    noisy = "And God said, Iet there be Iight: and there was Iight."
    result = pipeline.correct_text(noisy)
    assert result.identified_verses == ["kjv:genesis.1.3"]
    assert result.corrections[0].snapped
    assert "Let there be light" in result.corrected_text


def test_unrelated_text_is_not_snapped(pipeline):
    result = pipeline.correct_text("Invoice #4521 for office supplies, total $89.99")
    assert result.identified_verses == []
    assert not result.corrections[0].snapped


def test_multiline_page(pipeline):
    page = (
        "The LORD is my shepherd; I shaII not want.\n"
        "completely unrelated noise line 12345\n"
    )
    result = pipeline.correct_text(page)
    assert "kjv:psalms.23.1" in result.identified_verses
