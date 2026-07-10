import pytest

from omnicanon.corpus.loader import load_default_registry
from omnicanon.corpus.models import VerseRef


@pytest.fixture(scope="module")
def registry():
    return load_default_registry()


def test_registry_loads_all_sample_works(registry):
    assert set(registry.works) == {"kjv", "quran", "gita", "dhammapada"}
    assert len(registry) > 20


def test_verse_ref_parsing_with_book():
    ref = VerseRef.parse("kjv:john.1.1")
    assert (ref.work, ref.book, ref.chapter, ref.verse) == ("kjv", "john", 1, 1)
    assert str(ref) == "kjv:john.1.1"


def test_verse_ref_parsing_without_book():
    ref = VerseRef.parse("quran:1.5")
    assert (ref.work, ref.book, ref.chapter, ref.verse) == ("quran", None, 1, 5)


def test_invalid_ref_raises():
    with pytest.raises(ValueError):
        VerseRef.parse("not a ref")


def test_get_verse_resolution(registry):
    verse = registry.get_verse("kjv:genesis.1.3")
    assert verse is not None
    assert "light" in verse.text.lower()


def test_get_verse_missing_returns_none(registry):
    assert registry.get_verse("kjv:genesis.1.999") is None
    assert registry.get_verse("garbage") is None
