import pytest

from omnicanon.corpus.loader import load_default_registry
from omnicanon.engine.verifier import CitationVerifier


@pytest.fixture(scope="module")
def verifier():
    return CitationVerifier(load_default_registry())


def test_valid_reference_only_citation_passes(verifier):
    result = verifier.verify("Creation is described in [kjv:genesis.1.1].")
    assert result.verified
    assert result.hallucinated_refs == []


def test_hallucinated_reference_fails(verifier):
    result = verifier.verify("As stated in [kjv:genesis.1.999], kings are immortal.")
    assert not result.verified
    assert result.hallucinated_refs == ["kjv:genesis.1.999"]


def test_exact_quote_passes(verifier):
    result = verifier.verify(
        'Scripture says, "And God said, Let there be light: and there was light." [kjv:genesis.1.3]'
    )
    assert result.verified


def test_misquote_fails(verifier):
    result = verifier.verify(
        'Scripture says, "And God said, let there be darkness upon all the earth forever" [kjv:genesis.1.3]'
    )
    assert not result.verified
    assert "kjv:genesis.1.3" in result.misquotes


def test_partial_quote_within_verse_passes(verifier):
    result = verifier.verify('It teaches "hatred ceases by love" [dhammapada:1.5].')
    assert result.verified


def test_uncited_answer_is_unverified(verifier):
    result = verifier.verify("God created everything in the beginning.")
    assert not result.verified
    assert "No citations" in result.reason


def test_mixed_valid_and_invalid(verifier):
    result = verifier.verify("See [quran:1.2] and also [quran:99.99].")
    assert not result.verified
    assert result.hallucinated_refs == ["quran:99.99"]
