"""Omnicanon CLI.

    omnicanon search "let there be light"
    omnicanon answer "What did God create in the beginning?"
    omnicanon verify 'As it says, "and there was light" [kjv:genesis.1.3]'
    omnicanon bench
    omnicanon correct "Iet there be Iight and there was Iight"
    omnicanon works
"""

from __future__ import annotations

import argparse
import json
import sys

from omnicanon import __version__
from omnicanon.corpus.loader import load_default_registry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omnicanon", description=__doc__)
    parser.add_argument("--version", action="version", version=f"omnicanon {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="BM25 search over the canon")
    p_search.add_argument("query")
    p_search.add_argument("--top-k", type=int, default=5)
    p_search.add_argument("--work", default=None)

    p_answer = sub.add_parser("answer", help="Citation-verified grounded answer")
    p_answer.add_argument("question")
    p_answer.add_argument("--top-k", type=int, default=3)
    p_answer.add_argument("--work", default=None)
    p_answer.add_argument("--llm", action="store_true", help="Use LLM composer if an API key is set")

    p_verify = sub.add_parser("verify", help="Verify citations in a piece of text")
    p_verify.add_argument("text")

    sub.add_parser("bench", help="Run TheoBench against the built-in engine")

    p_correct = sub.add_parser("correct", help="Canon-aware correction of OCR text")
    p_correct.add_argument("text")

    sub.add_parser("works", help="List loaded works")

    args = parser.parse_args(argv)
    registry = load_default_registry()

    if args.command == "search":
        from omnicanon.engine.retriever import Retriever

        for hit in Retriever(registry).search(args.query, top_k=args.top_k, work=args.work):
            print(f"{hit.score:6.2f}  [{hit.verse.id}]  {hit.verse.text}")

    elif args.command == "answer":
        from omnicanon.engine.answer import AnswerEngine

        result = AnswerEngine(registry).answer(
            args.question, top_k=args.top_k, work=args.work, use_llm=args.llm
        )
        print(result.answer)
        print()
        status = "VERIFIED" if result.verification.verified else "UNVERIFIED"
        print(f"[{status} | mode={result.mode}] {result.verification.reason}")

    elif args.command == "verify":
        from omnicanon.engine.verifier import CitationVerifier

        result = CitationVerifier(registry).verify(args.text)
        print(json.dumps({
            "verified": result.verified,
            "reason": result.reason,
            "hallucinated_refs": result.hallucinated_refs,
            "misquotes": result.misquotes,
        }, indent=2))

    elif args.command == "bench":
        from omnicanon.bench.harness import run_benchmark
        from omnicanon.engine.answer import AnswerEngine

        engine = AnswerEngine(registry)
        result = run_benchmark(
            lambda q: engine.answer(q).answer, registry, system_name="omnicanon-extractive"
        )
        print(json.dumps(result.summary(), indent=2))

    elif args.command == "correct":
        from omnicanon.scriptorium.pipeline import OcrPipeline

        result = OcrPipeline(registry).correct_text(args.text)
        for c in result.corrections:
            marker = f"-> [{c.verse_id}] ({c.confidence:.2f})" if c.snapped else "(no canon match)"
            print(f"{c.ocr_text!r} {marker}")
            if c.snapped:
                print(f"    {c.corrected_text}")

    elif args.command == "works":
        for w in registry.works.values():
            print(f"{w.slug:12s} {w.tradition:14s} {len(w):5d} verses  {w.title} — {w.translation}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
