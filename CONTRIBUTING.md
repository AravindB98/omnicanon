# Contributing to Omnicanon

Thank you for considering a contribution! This project spans retrieval, evaluation, data engineering, and OCR — there is meaningful work here for many skill sets.

## Step-by-step

1. **Star and fork.** Star the repo (it genuinely helps discovery) and fork it via the Fork button.
2. **Clone your fork:**
   ```bash
   git clone https://github.com/<your-username>/omnicanon.git
   cd omnicanon
   git remote add upstream https://github.com/AravindB98/omnicanon.git
   ```
3. **Set up the environment:**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -e ".[api,dev]"
   ```
4. **Create a branch:** `git checkout -b feat/short-description`
5. **Make your change.** Every behavior change needs a test. Keep the core dependency-free — new runtime deps go behind an optional extra.
6. **Check locally:** `pytest -q && ruff check src tests`
7. **Commit and push** with a descriptive message, then **open a PR** against `main`. Explain what, why, and how you tested it.
8. **Respond to review.** Squash-merge once CI is green and a maintainer approves.

## What to contribute

| Area | Examples | Difficulty |
|---|---|---|
| TheoBench tasks | Attribution/trap tasks for traditions you know well | ⭐ good first issue |
| Corpus ingesters | Tanzil XML, Sefaria API, SBE volumes → `scripts/ingest.py` | ⭐⭐ |
| Retrieval | Dense embeddings/reranking behind `Retriever(rerank_fn=...)` | ⭐⭐⭐ |
| Scriptorium | Preprocessing, layout detection, non-Latin scripts | ⭐⭐⭐ |
| Docs | Tutorials, API examples, corpus documentation | ⭐ |

## Ground rules for religious content

- **Accuracy over interpretation.** Corpus data must come from citable, license-clear sources (public domain or explicitly licensed). Cite your source in the PR.
- **No tradition is second-class.** Benchmarks and corpora should treat all traditions with equal rigor.
- **Descriptive, not devotional or polemical.** Code, comments, and docs stay neutral; the project serves scholars and practitioners of every tradition (and none).

## Reporting issues

Use GitHub Issues. For corpus errors (wrong verse text, bad ID), include the verse ID, the incorrect text, and a citable source for the correction.
