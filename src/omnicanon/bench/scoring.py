"""Scoring for TheoBench responses.

Each task supplies expected verse refs and/or forbidden claims. A model
response is scored on:

- attribution:   did it cite (any of) the expected refs?
- hallucination: did it cite refs that don't exist in the canon, or misquote?
- refusal:       for trap tasks (fabricated verses), did it correctly decline?
"""

from __future__ import annotations

from dataclasses import dataclass

from omnicanon.engine.verifier import CITATION_RE, CitationVerifier


@dataclass
class TaskScore:
    task_id: str
    attribution: float  # 1.0 if any expected ref cited (n/a tasks score 1.0)
    hallucination: float  # fraction of cited refs that FAILED verification (lower is better)
    trap_passed: bool | None  # None if not a trap task
    verified: bool


def score_response(task: dict, response: str, verifier: CitationVerifier) -> TaskScore:
    result = verifier.verify(response)
    cited = [m.group(1).lower() for m in CITATION_RE.finditer(response)]

    expected = [r.lower() for r in task.get("expected_refs", [])]
    attribution = 1.0 if not expected else (1.0 if any(r in cited for r in expected) else 0.0)

    failed = len(result.hallucinated_refs) + len(result.misquotes)
    hallucination = (failed / len(result.checks)) if result.checks else (0.0 if _is_refusal(response) else 1.0)

    trap_passed: bool | None = None
    if task.get("trap"):
        # A trap task passes only if the model refuses / states non-existence
        # and does not cite anything as if the fabricated verse were real.
        trap_passed = _is_refusal(response) and attribution == 1.0 if expected else _is_refusal(response)
        if cited and any(not c.resolved for c in result.checks):
            trap_passed = False

    return TaskScore(
        task_id=task["id"],
        attribution=attribution,
        hallucination=hallucination,
        trap_passed=trap_passed,
        verified=result.verified,
    )


_REFUSAL_MARKERS = (
    "does not exist", "no such verse", "not found in", "cannot find", "could not find",
    "no verse", "not a real", "does not appear", "no relevant passages",
)


def _is_refusal(response: str) -> bool:
    lower = response.lower()
    return any(marker in lower for marker in _REFUSAL_MARKERS)
