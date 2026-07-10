import pytest

from omnicanon.bench.harness import load_tasks, run_benchmark
from omnicanon.corpus.loader import load_default_registry
from omnicanon.engine.answer import AnswerEngine


@pytest.fixture(scope="module")
def registry():
    return load_default_registry()


def test_tasks_load(registry):
    tasks = load_tasks()
    assert len(tasks) >= 10
    assert any(t.get("trap") for t in tasks)


def test_builtin_engine_beats_hallucination(registry):
    engine = AnswerEngine(registry)
    result = run_benchmark(lambda q: engine.answer(q).answer, registry, "omnicanon-extractive")
    # The extractive engine cites only real verses, so hallucination must be 0.
    assert result.hallucination_rate == 0.0
    assert result.attribution_accuracy >= 0.7


def test_fabricating_system_scores_badly(registry):
    def liar(question: str) -> str:
        return 'Scripture clearly says "kings never die" [kjv:genesis.1.999].'

    result = run_benchmark(liar, registry, "liar")
    assert result.hallucination_rate == 1.0
    assert result.trap_pass_rate == 0.0
