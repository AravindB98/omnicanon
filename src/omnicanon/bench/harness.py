"""TheoBench harness.

A "system under test" is any callable (question: str) -> str. That means you
can benchmark:
- Omnicanon's own AnswerEngine (the built-in baseline)
- any LLM via a thin adapter
- any other RAG system

Results aggregate attribution accuracy, hallucination rate, and trap pass rate.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Callable

from omnicanon.corpus.loader import CorpusRegistry
from omnicanon.bench.scoring import TaskScore, score_response
from omnicanon.engine.verifier import CitationVerifier


def load_tasks(path: str | Path | None = None) -> list[dict]:
    if path:
        text = Path(path).read_text(encoding="utf-8")
    else:
        text = (resources.files("omnicanon.bench") / "tasks" / "theobench_v1.jsonl").read_text(
            encoding="utf-8"
        )
    return [json.loads(line) for line in text.splitlines() if line.strip()]


@dataclass
class BenchResult:
    system: str
    scores: list[TaskScore] = field(default_factory=list)

    @property
    def attribution_accuracy(self) -> float:
        relevant = [s for s in self.scores if s.attribution is not None]
        return sum(s.attribution for s in relevant) / len(relevant) if relevant else 0.0

    @property
    def hallucination_rate(self) -> float:
        return sum(s.hallucination for s in self.scores) / len(self.scores) if self.scores else 0.0

    @property
    def trap_pass_rate(self) -> float | None:
        traps = [s for s in self.scores if s.trap_passed is not None]
        if not traps:
            return None
        return sum(1 for s in traps if s.trap_passed) / len(traps)

    def summary(self) -> dict:
        return {
            "system": self.system,
            "tasks": len(self.scores),
            "attribution_accuracy": round(self.attribution_accuracy, 3),
            "hallucination_rate": round(self.hallucination_rate, 3),
            "trap_pass_rate": None if self.trap_pass_rate is None else round(self.trap_pass_rate, 3),
        }


def run_benchmark(
    system_fn: Callable[[str], str],
    registry: CorpusRegistry,
    system_name: str = "system-under-test",
    tasks: list[dict] | None = None,
) -> BenchResult:
    verifier = CitationVerifier(registry)
    tasks = tasks if tasks is not None else load_tasks()
    result = BenchResult(system=system_name)
    for task in tasks:
        response = system_fn(task["question"])
        result.scores.append(score_response(task, response, verifier))
    return result
