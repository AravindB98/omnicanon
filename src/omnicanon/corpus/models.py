"""Canonical data model for multi-faith scripture.

Every verse in every tradition gets a single, unambiguous canonical ID:

    <work>:<book>.<chapter>.<verse>        e.g.  kjv:john.1.1
    <work>:<chapter>.<verse>               e.g.  quran:1.5   gita:2.47

Canonical IDs are the backbone of citation verification: an answer may only
cite IDs that resolve to real verses, and quoted text must match the canon.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class VerseRef:
    """A parsed, canonical verse reference."""

    work: str
    book: str | None
    chapter: int
    verse: int

    _PATTERN = re.compile(
        r"^(?P<work>[a-z0-9_-]+):"
        r"(?:(?P<book>[a-z0-9_-]+)\.)?"
        r"(?P<chapter>\d+)\.(?P<verse>\d+)$"
    )

    @classmethod
    def parse(cls, ref: str) -> "VerseRef":
        m = cls._PATTERN.match(ref.strip().lower())
        if not m:
            raise ValueError(f"Invalid canonical reference: {ref!r}")
        return cls(
            work=m.group("work"),
            book=m.group("book"),
            chapter=int(m.group("chapter")),
            verse=int(m.group("verse")),
        )

    def __str__(self) -> str:
        if self.book:
            return f"{self.work}:{self.book}.{self.chapter}.{self.verse}"
        return f"{self.work}:{self.chapter}.{self.verse}"


@dataclass(frozen=True)
class Verse:
    """A single verse with its canonical ID and text."""

    ref: VerseRef
    text: str
    original: str | None = None  # source-language text if available

    @property
    def id(self) -> str:
        return str(self.ref)


@dataclass
class Work:
    """A scriptural work (e.g. the KJV Bible, the Qur'an) as an ordered verse list."""

    slug: str
    title: str
    tradition: str
    language: str
    translation: str
    license: str
    verses: list[Verse] = field(default_factory=list)

    _by_id: dict[str, Verse] = field(default_factory=dict, repr=False)

    def add(self, verse: Verse) -> None:
        self.verses.append(verse)
        self._by_id[verse.id] = verse

    def get(self, ref: str | VerseRef) -> Verse | None:
        return self._by_id.get(str(ref) if isinstance(ref, VerseRef) else ref.strip().lower())

    def __len__(self) -> int:
        return len(self.verses)
