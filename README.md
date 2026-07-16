# Omnicanon

**Citation-verified AI infrastructure for the world's sacred texts.**

[![CI](https://github.com/AravindB98/omnicanon/actions/workflows/ci.yml/badge.svg)](https://github.com/AravindB98/omnicanon/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](pyproject.toml)

LLMs confidently misquote scripture, invent verses, and misattribute teachings — in a domain where accuracy matters deeply to billions of people. Omnicanon treats this as an engineering problem: **an answer about scripture is only trustworthy if a machine can check it against the canon.**

⭐ **If this project is useful to you, please [star it](https://github.com/AravindB98/omnicanon/stargazers) and [fork it](https://github.com/AravindB98/omnicanon/fork)** — stars help others discover it, and forking is step one of contributing (see [Contributing](#contributing)).

## The four pillars

| Pillar | Module | What it does |
|---|---|---|
| 📚 **Corpus** | `omnicanon.corpus` | Canonical multi-faith data model. Every verse in every tradition gets one unambiguous ID (`kjv:john.1.1`, `quran:1.5`, `gita:2.47`, `dhammapada:1.5`). |
| 🔍 **Engine** | `omnicanon.engine` | Retrieval (pure-stdlib BM25, pluggable dense reranking) + **programmatic citation verification**: cited refs must resolve, quotes must match the canon. Unverified LLM output is never returned. |
| 📊 **TheoBench** | `omnicanon.bench` | An open benchmark for LLM scriptural accuracy: attribution, hallucination rate, and *trap tasks* (fabricated verses a correct system must refuse). Benchmark any system — it's just a `(question) -> answer` callable. |
| 📜 **Scriptorium** | `omnicanon.scriptorium` | OCR pipeline for scanned manuscripts with **canon-aware post-correction**: OCR lines are snapped to the verse they actually are, recovering clean text *and* verse identity. |

The pillars reinforce each other: the corpus powers verification, verification powers the benchmark, and the corpus makes OCR self-correcting.

## Quickstart

```bash
git clone https://github.com/AravindB98/omnicanon.git
cd omnicanon
pip install -e ".[dev]"        # core has ZERO runtime dependencies

# Search across four traditions at once
omnicanon search "let there be light"
omnicanon search "the merciful" --work quran

# Citation-verified answers (offline, extractive — correct by construction)
omnicanon answer "Where does the Gita say one has a right to action but not its fruits?"

# Verify any text's citations against the canon
omnicanon verify 'It says "and there was light" [kjv:genesis.1.3]'   # ✅ verified
omnicanon verify 'It says kings are immortal [kjv:genesis.1.999]'    # ❌ hallucinated ref

# Run TheoBench against the built-in engine
omnicanon bench

# Canon-aware OCR correction (classic I/l confusion)
omnicanon correct "And God said, Iet there be Iight: and there was Iight."
```

### REST API

```bash
pip install -e ".[api]"
uvicorn omnicanon.api.app:app --reload
# interactive docs at http://localhost:8000/docs
```

Endpoints: `/search`, `/answer`, `/verify`, `/verse/{ref}`, `/works`, `/health`.

### Python

```python
from omnicanon import load_default_registry, Retriever, CitationVerifier

registry = load_default_registry()
hits = Retriever(registry).search("hatred ceases by love")
print(hits[0].verse.id)   # dhammapada:1.5

result = CitationVerifier(registry).verify('See [quran:99.99].')
print(result.verified, result.hallucinated_refs)   # False ['quran:99.99']
```

## How verification works

Answers cite verses inline as `[work:book.chapter.verse]`. The verifier enforces three invariants:

1. **Resolution** — every cited reference must exist in the canon.
2. **Fidelity** — every quoted passage must actually appear in the verse it's attributed to (normalized fuzzy match, threshold 0.82).
3. **Coverage** — an uncited answer is flagged as unverifiable, never trusted.

In LLM mode (`--llm`, requires `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`), generated prose must pass verification before it is returned; otherwise the engine falls back to the extractive answer. **The system is architecturally incapable of shipping an unverified citation.**

## TheoBench

TheoBench v1 ships attribution tasks across four traditions plus trap tasks built on fabricated verses (`Genesis 1:99`, `Quran 1:15`, …). Metrics:

- **attribution_accuracy** — cited the expected verse
- **hallucination_rate** — fraction of citations that failed verification
- **trap_pass_rate** — refused fabricated verses instead of inventing them

```python
from omnicanon import load_default_registry
from omnicanon.bench import run_benchmark

registry = load_default_registry()
result = run_benchmark(my_llm_call, registry, system_name="gpt-x")
print(result.summary())
```

Contributions of tasks — especially in underrepresented traditions and languages — are the highest-impact PRs you can make. Leaderboard for frontier models is on the [roadmap](#roadmap).

## Corpus & data

Bundled corpora are small public-domain samples (KJV 1611, Pickthall 1930, Telang 1882, Müller 1881) used for tests and demos. Fetch full texts with:

```bash
python scripts/ingest.py kjv    # Project Gutenberg → data/full/ (git-ignored)
```

Sample excerpts should be re-verified against printed sources during full ingestion; the ingest pipeline is the source of truth for production corpora.

## Roadmap

- [ ] Full-text ingesters: Tanzil (Qur'an), Sefaria (Tanakh/Talmud), SBE volumes, sutta collections
- [ ] Original-language texts + verse-aligned cross-lingual retrieval (Hebrew, Arabic, Sanskrit, Pali, Greek)
- [ ] Dense embedding retrieval + reranking behind the existing pluggable interface
- [ ] TheoBench leaderboard: scores for frontier models, published in-repo
- [ ] Scriptorium: layout detection and non-Latin script OCR (Devanagari, Arabic)
- [ ] Community-reviewed theological annotation layer (commentary refs, parallel passages)

## Contributing

All contributions are welcome — code, benchmark tasks, corpus ingesters, docs, and issue reports. **Please read [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.** The short version:

1. ⭐ **Star this repo** (visibility helps the project grow) and **fork it** to your account.
2. **Clone your fork** and create a branch: `git checkout -b feat/my-change`.
3. **Set up dev env**: `pip install -e ".[api,dev]"`.
4. **Make your change** with tests. Run `pytest` and `ruff check src tests` locally.
5. **Open a pull request** against `main` with a clear description of what and why.
6. A maintainer reviews; CI must pass across Python 3.10–3.12.

Good first issues: add a TheoBench task for a tradition you know well, add a corpus ingester, or improve OCR preprocessing. Religious texts demand respect and accuracy — see our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

[Apache-2.0](LICENSE). Bundled scripture texts are public-domain translations; each corpus file declares its translation and license.

---

## 🧒 Explain Like I'm 5

A search engine for holy books that is physically unable to make quotes up: ask about the Bible, Quran, Torah, Gita and more, and every answer comes strictly from verified scripture text with exact verse citations. It also includes TheoBench — a test that grades AI models on how accurately they handle sacred texts.

## 🧰 Tech Stack

Python · multi-faith text corpus · zero-hallucination RAG (citation-verified) · TheoBench LLM benchmark

## 🌍 Real-Life Applications

- Students of religion comparing what different scriptures actually say
- Faith communities building trustworthy scripture Q&A tools
- Measuring LLM reliability on religious content (TheoBench)
