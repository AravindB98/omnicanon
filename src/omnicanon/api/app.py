"""FastAPI service exposing search, grounded answers, and verification.

Run:  pip install 'omnicanon[api]' && uvicorn omnicanon.api.app:app --reload
Docs: http://localhost:8000/docs
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from omnicanon import __version__
from omnicanon.corpus.loader import load_default_registry
from omnicanon.engine.answer import AnswerEngine
from omnicanon.engine.retriever import Retriever
from omnicanon.engine.verifier import CitationVerifier

app = FastAPI(
    title="Omnicanon API",
    version=__version__,
    description="Citation-verified search and Q&A over the world's sacred texts.",
)

registry = load_default_registry()
retriever = Retriever(registry)
engine = AnswerEngine(registry)
verifier = CitationVerifier(registry)


class VerifyRequest(BaseModel):
    text: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__, "verses_loaded": len(registry)}


@app.get("/works")
def works() -> list[dict]:
    return [
        {
            "slug": w.slug,
            "title": w.title,
            "tradition": w.tradition,
            "translation": w.translation,
            "license": w.license,
            "verses": len(w),
        }
        for w in registry.works.values()
    ]


@app.get("/search")
def search(q: str, top_k: int = 5, work: str | None = None) -> list[dict]:
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")
    return [
        {"id": h.verse.id, "text": h.verse.text, "score": round(h.score, 4)}
        for h in retriever.search(q, top_k=top_k, work=work)
    ]


@app.get("/answer")
def answer(q: str, top_k: int = 3, work: str | None = None, use_llm: bool = False) -> dict:
    result = engine.answer(q, top_k=top_k, work=work, use_llm=use_llm)
    return {
        "question": result.question,
        "answer": result.answer,
        "mode": result.mode,
        "verified": result.verification.verified,
        "verification": result.verification.reason,
    }


@app.get("/verse/{ref}")
def verse(ref: str) -> dict:
    v = registry.get_verse(ref)
    if v is None:
        raise HTTPException(status_code=404, detail=f"No verse {ref!r} in the loaded canon.")
    return {"id": v.id, "text": v.text}


@app.post("/verify")
def verify(req: VerifyRequest) -> dict:
    result = verifier.verify(req.text)
    return {
        "verified": result.verified,
        "reason": result.reason,
        "hallucinated_refs": result.hallucinated_refs,
        "misquotes": result.misquotes,
        "checks": [
            {"ref": c.ref, "resolved": c.resolved, "fidelity": c.fidelity, "passed": c.passed}
            for c in result.checks
        ],
    }
