import pytest

from omnicanon.corpus.loader import load_default_registry
from omnicanon.engine.retriever import Retriever


@pytest.fixture(scope="module")
def retriever():
    return Retriever(load_default_registry())


def test_search_finds_relevant_verse(retriever):
    hits = retriever.search("let there be light")
    assert hits
    assert hits[0].verse.id == "kjv:genesis.1.3"


def test_search_cross_tradition(retriever):
    hits = retriever.search("hatred ceases by love")
    assert hits[0].verse.id == "dhammapada:1.5"


def test_work_filter(retriever):
    hits = retriever.search("the merciful", work="quran")
    assert hits
    assert all(h.verse.ref.work == "quran" for h in hits)


def test_no_match_returns_empty(retriever):
    assert retriever.search("quantum chromodynamics blockchain") == []
