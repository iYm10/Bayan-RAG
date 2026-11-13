import json
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.provider import Provider, ProviderError
from app.retrieval import rank
from app.store import MAX_BYTES, Store

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


class Query(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    k: int = Field(default=4, ge=1, le=8)
    mode: Literal["hybrid", "bm25"] = "hybrid"


def search(store, provider, question, k, mode):
    chunks = store.chunks()
    vector = None
    if provider.kind != "demo" and chunks and mode == "hybrid":
        if any(c["fingerprint"] != provider.fingerprint or c["vector"] is None for c in chunks):
            raise HTTPException(
                409,
                "Embedding configuration changed. Re-index documents using the current provider.",
            )
        vector = provider.embed([question])[0]
    return rank(question, chunks, k, mode, vector)


def public_chunk(c, number):
    return {
        key: c[key]
        for key in (
            "id",
            "document_id",
            "name",
            "page",
            "text",
            "score",
            "bm25",
            "secondary",
            "secondary_type",
        )
    } | {"number": number}


def evaluate(store, provider, dataset, mode="hybrid"):
    """Document-level Recall@k and MRR@k on answerable cases only."""
    rows = []
    for item in dataset:
        results = search(store, provider, item["question"], 4, mode)
        expected = set(item["expected_documents"])
        ranked_docs = list(dict.fromkeys(c["name"] for c in results))
        positions = [i + 1 for i, name in enumerate(ranked_docs) if name in expected]
        rows.append(
            {
                "question": item["question"],
                "expected": sorted(expected),
                "retrieved": ranked_docs,
                "recall": len(expected.intersection(ranked_docs)) / len(expected)
                if expected
                else None,
                "reciprocal_rank": 1 / min(positions) if positions else (0 if expected else None),
                "expected_abstention": not expected,
                "retrieval_abstained": not results,
            }
        )
    answerable = [r for r in rows if r["recall"] is not None]
    negative = [r for r in rows if r["expected_abstention"]]
    return {
        "k": 4,
        "mode": mode,
        "cases": len(rows),
        "answerable_cases": len(answerable),
        "recall_at_k": round(sum(r["recall"] for r in answerable) / len(answerable), 4)
        if answerable
        else None,
        "mrr_at_k": round(sum(r["reciprocal_rank"] for r in answerable) / len(answerable), 4)
        if answerable
        else None,
        "negative_abstention_rate": round(
            sum(r["retrieval_abstained"] for r in negative) / len(negative), 4
        )
        if negative
        else None,
        "scope": "Small, hand-authored demo retrieval set; does not measure generated-answer correctness.",
        "results": rows,
    }


def create_app(database=None, provider=None):
    store = Store(database or os.getenv("RAG_DATABASE", str(ROOT / "storage/bayan.db")))
    provider = provider or Provider()

    @asynccontextmanager
    async def lifespan(app):
        # Explicit seed action keeps uploaded corpora and evaluation data separate.
        yield

    app = FastAPI(
        title="Bayan-RAG", version="1.0.0", lifespan=lifespan, docs_url=None, redoc_url=None
    )
    app.state.store, app.state.provider = store, provider

    @app.middleware("http")
    async def headers(request: Request, call_next):
        # Block cross-origin browser mutations. This is a single-user local app.
        if request.method in {"POST", "DELETE", "PUT", "PATCH"}:
            origin = request.headers.get("origin")
            if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
                return JSONResponse(
                    {"detail": "Cross-origin requests are not allowed."}, status_code=403
                )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        return response

    @app.exception_handler(ProviderError)
    async def provider_error(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=502)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "provider": provider.kind, "generation": provider.kind != "demo"}

    @app.get("/api/stats")
    def stats():
        documents = store.documents()
        return {
            "documents": len(documents),
            "chunks": sum(d["chunks"] for d in documents),
            "provider": provider.kind,
            "generation": provider.kind != "demo",
            "retrieval": "BM25 + character TF-IDF"
            if provider.kind == "demo"
            else "BM25 + dense embeddings",
            "model": None if provider.kind == "demo" else provider.chat_model,
        }

    @app.get("/api/documents")
    def documents():
        return store.documents()

    @app.post("/api/documents", status_code=201)
    def upload(file: UploadFile):
        data = file.file.read(MAX_BYTES + 1)
        name = (file.filename or "document").replace("\\", "/").split("/")[-1][:150]
        try:
            return store.ingest(name, data, provider)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        finally:
            file.file.close()

    @app.delete("/api/documents/{doc_id}")
    def delete(doc_id: str):
        if not store.delete(doc_id):
            raise HTTPException(404, "Document not found.")
        return {"deleted": True}

    @app.post("/api/demo")
    def seed():
        results = [
            store.ingest(p.name, p.read_bytes(), provider)
            for p in sorted((ROOT / "data/demo").glob("*.md"))
        ]
        return {"documents": len(results), "added": sum(not r["duplicate"] for r in results)}

    @app.post("/api/search")
    def retrieve(query: Query):
        start = time.perf_counter()
        if not query.question.strip():
            raise HTTPException(422, "Question cannot be blank.")
        found = search(store, provider, query.question, query.k, query.mode)
        return {
            "sources": [public_chunk(c, i + 1) for i, c in enumerate(found)],
            "latency_ms": round((time.perf_counter() - start) * 1000, 1),
        }

    @app.post("/api/query")
    def query(query: Query):
        start = time.perf_counter()
        if not query.question.strip():
            raise HTTPException(422, "Question cannot be blank.")
        found = search(store, provider, query.question, query.k, query.mode)
        retrieval_ms = round((time.perf_counter() - start) * 1000, 1)
        if not found:
            answer = {"insufficient": True, "claims": []}
        elif provider.kind == "demo":
            # Exact extracts: never misrepresent an offline baseline as generation.
            answer = {
                "insufficient": False,
                "claims": [
                    {"text": c["text"], "sources": [i + 1]} for i, c in enumerate(found[:2])
                ],
            }
        else:
            answer = provider.generate(query.question, found)
        return {
            **answer,
            "sources": [public_chunk(c, i + 1) for i, c in enumerate(found)],
            "answer_type": "extractive" if provider.kind == "demo" else "generated",
            "retrieval_ms": retrieval_ms,
            "total_ms": round((time.perf_counter() - start) * 1000, 1),
            "provider": provider.kind,
            "mode": query.mode,
        }

    @app.post("/api/evaluate")
    def evaluation():
        # Temporary, isolated store: results cannot be inflated by the user's uploads.
        import tempfile

        with tempfile.TemporaryDirectory() as temp:
            evaluation_store = Store(Path(temp) / "evaluation.db")
            for p in sorted((ROOT / "data/demo").glob("*.md")):
                evaluation_store.ingest(p.name, p.read_bytes(), provider)
            dataset = json.loads((ROOT / "data/evaluation.json").read_text())
            report = evaluate(evaluation_store, provider, dataset)
            baseline = evaluate(evaluation_store, provider, dataset, "bm25")
            report["baseline"] = {
                key: baseline[key]
                for key in ("mode", "recall_at_k", "mrr_at_k", "negative_abstention_rate")
            }
            return report

    app.mount("/static", StaticFiles(directory=ROOT / "app/static"), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(ROOT / "app/static/index.html")

    return app


app = create_app()
