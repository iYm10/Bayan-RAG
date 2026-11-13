"""Bounded, session-local evidence collections for the public Gradio demo."""

import hashlib
from pathlib import Path

from app.retrieval import rank
from app.store import chunk_pages, extract

ROOT = Path(__file__).resolve().parent.parent


def add_document(session, name, content):
    digest = hashlib.sha256(content).hexdigest()
    if digest in session["documents"]:
        return session, "This document is already indexed in your session."
    if len(session["documents"]) >= 15:
        raise ValueError(
            "Session limit reached. Reset the collection before adding more documents."
        )
    chunks = chunk_pages(extract(name, content))
    if sum(len(c["text"]) for c in session["chunks"] + chunks) > 600_000:
        raise ValueError("Session text limit reached. Reset the collection to continue.")
    start = max((c["id"] for c in session["chunks"]), default=0)
    added = [
        {**c, "id": start + i + 1, "name": name, "document_id": digest}
        for i, c in enumerate(chunks)
    ]
    updated = {
        "documents": {**session["documents"], digest: name},
        "chunks": session["chunks"] + added,
    }
    return (
        updated,
        f"Indexed {len(added)} chunks. Your session contains {len(updated['documents'])} documents.",
    )


def new_session():
    session = {"documents": {}, "chunks": []}
    for path in sorted((ROOT / "data/demo").glob("*.md")):
        session, _ = add_document(session, path.name, path.read_bytes())
    return session


def answer(question, session, strategy="hybrid", k=4):
    if not question.strip() or len(question) > 2000:
        raise ValueError("Enter a question between 1 and 2,000 characters.")
    if strategy not in {"hybrid", "bm25"} or not 1 <= int(k) <= 8:
        raise ValueError("Invalid retrieval settings.")
    found = rank(question, session["chunks"], int(k), strategy)
    return format_evidence(found)


def format_evidence(found):
    if not found:
        return (
            "No matching evidence. Add a relevant document or make your question more specific.",
            [],
            [],
        )
    text = "VERBATIM SOURCE EXCERPTS\n\n" + "\n\n".join(
        f"[{i + 1}] {c['name']} · page {c['page']}\n{c['text']}" for i, c in enumerate(found[:2])
    )
    rows = [[i + 1, c["name"], c["page"], c["score"], c["bm25"]] for i, c in enumerate(found)]
    passages = [
        {"source": i + 1, "document": c["name"], "page": c["page"], "text": c["text"]}
        for i, c in enumerate(found)
    ]
    return text, rows, passages
