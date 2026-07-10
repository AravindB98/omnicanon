#!/usr/bin/env python3
"""Ingest full public-domain texts into data/full/ (git-ignored).

Bundled corpus samples are intentionally tiny; this script fetches complete
texts and converts them into Omnicanon's corpus JSON format. Start with the
KJV from Project Gutenberg; contributions of additional ingesters (Tanzil
Quran XML, SBE volumes, Sefaria exports) are very welcome — see CONTRIBUTING.

Usage:
    python scripts/ingest.py kjv
    omnicanon works  # after: OMNICANON_DATA_DIR=data/full
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "full"

KJV_URL = "https://www.gutenberg.org/cache/epub/10/pg10.txt"

# Gutenberg KJV verse lines look like: "1:1 In the beginning God created..."
VERSE_LINE = re.compile(r"^(\d+):(\d+)\s+(.*)$")


def slugify_book(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


def ingest_kjv() -> Path:
    print(f"Fetching {KJV_URL} ...")
    raw = urllib.request.urlopen(KJV_URL, timeout=60).read().decode("utf-8-sig")

    # Strip the Gutenberg header/footer.
    body = raw.split("*** START OF", 1)[-1].split("*** END OF", 1)[0]

    verses: list[dict] = []
    current_book: str | None = None
    buffer: list[str] = []

    def flush(book: str | None, buf: list[str]) -> None:
        if not (book and buf):
            return
        m = VERSE_LINE.match(" ".join(buf))
        if m:
            chapter, verse, text = m.groups()
            verses.append(
                {"id": f"kjv:{slugify_book(book)}.{chapter}.{verse}", "text": text.strip()}
            )

    for line in body.splitlines():
        line = line.rstrip()
        if not line:
            flush(current_book, buffer)
            buffer = []
            continue
        if VERSE_LINE.match(line):
            flush(current_book, buffer)
            buffer = [line]
        elif buffer:
            buffer.append(line)
        else:
            # Book title lines are short, non-verse text (e.g. "The First Book
            # of Moses: Called Genesis"). Heuristic; refine as needed.
            if 3 < len(line) < 80 and not line[0].isdigit():
                current_book = line.split(":")[-1].replace("Called", "").strip() or current_book
    flush(current_book, buffer)

    payload = {
        "slug": "kjv",
        "title": "The Holy Bible, King James Version",
        "tradition": "Christianity",
        "language": "en",
        "translation": "King James Version (1611), Project Gutenberg #10",
        "license": "Public domain",
        "verses": verses,
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "kjv.json"
    out.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(verses)} verses -> {out}")
    return out


INGESTERS = {"kjv": ingest_kjv}


def main() -> int:
    targets = sys.argv[1:] or ["kjv"]
    for target in targets:
        fn = INGESTERS.get(target)
        if fn is None:
            print(f"No ingester for {target!r}. Available: {', '.join(INGESTERS)}. "
                  "PRs adding ingesters are welcome!")
            return 1
        fn()
    return 0


if __name__ == "__main__":
    sys.exit(main())
