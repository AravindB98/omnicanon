"""Corpus loading and the cross-work registry.

Bundled JSON files under corpus/data/ are small public-domain samples used for
tests and demos. Full texts are fetched by scripts/ingest.py into data/full/
(git-ignored) and loaded the same way.
"""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from omnicanon.corpus.models import Verse, VerseRef, Work


def load_work_from_dict(payload: dict) -> Work:
    work = Work(
        slug=payload["slug"],
        title=payload["title"],
        tradition=payload["tradition"],
        language=payload["language"],
        translation=payload["translation"],
        license=payload["license"],
    )
    for row in payload["verses"]:
        ref = VerseRef.parse(row["id"])
        if ref.work != work.slug:
            raise ValueError(f"Verse {row['id']} does not belong to work {work.slug}")
        work.add(Verse(ref=ref, text=row["text"], original=row.get("original")))
    return work


def load_work_from_path(path: str | Path) -> Work:
    with open(path, encoding="utf-8") as f:
        return load_work_from_dict(json.load(f))


class CorpusRegistry:
    """All loaded works, addressable by slug; the single source of truth for verification."""

    def __init__(self) -> None:
        self.works: dict[str, Work] = {}

    def register(self, work: Work) -> None:
        self.works[work.slug] = work

    def get_verse(self, ref: str | VerseRef) -> Verse | None:
        if isinstance(ref, str):
            try:
                ref = VerseRef.parse(ref)
            except ValueError:
                return None
        work = self.works.get(ref.work)
        return work.get(ref) if work else None

    def all_verses(self) -> list[Verse]:
        return [v for w in self.works.values() for v in w.verses]

    def __len__(self) -> int:
        return sum(len(w) for w in self.works.values())


def load_default_registry(extra_dir: str | Path | None = None) -> CorpusRegistry:
    """Load all bundled sample corpora, plus any JSON corpora in extra_dir."""
    registry = CorpusRegistry()
    data_pkg = resources.files("omnicanon.corpus") / "data"
    for entry in sorted(data_pkg.iterdir(), key=lambda e: e.name):
        if entry.name.endswith(".json"):
            registry.register(load_work_from_dict(json.loads(entry.read_text(encoding="utf-8"))))
    if extra_dir:
        for path in sorted(Path(extra_dir).glob("*.json")):
            registry.register(load_work_from_path(path))
    return registry
