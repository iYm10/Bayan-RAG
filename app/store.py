"""SQLite document store; atomic ingestion and page-aware overlapping chunks."""

import hashlib
import io
import json
import sqlite3
import zipfile
from contextlib import contextmanager
from pathlib import Path

from docx import Document
from pypdf import PdfReader

MAX_BYTES = 10 * 1024 * 1024
MAX_CHARS = 300_000


def extract(name: str, content: bytes) -> list[tuple[int, str]]:
    suffix = Path(name).suffix.lower()
    if len(content) > MAX_BYTES:
        raise ValueError("Maximum file size is 10 MB.")
    try:
        if suffix == ".pdf":
            reader = PdfReader(io.BytesIO(content))
            if reader.is_encrypted:
                raise ValueError("Encrypted PDFs are unsupported.")
            if len(reader.pages) > 300:
                raise ValueError("Maximum PDF length is 300 pages.")
            pages = [(i + 1, p.extract_text() or "") for i, p in enumerate(reader.pages)]
        elif suffix == ".docx":
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if sum(f.file_size for f in archive.infolist()) > 30 * 1024 * 1024:
                    raise ValueError("Expanded DOCX exceeds the 30 MB limit.")
            doc = Document(io.BytesIO(content))
            text = "\n".join(p.text for p in doc.paragraphs)
            tables = "\n".join(
                " | ".join(c.text for c in row.cells) for t in doc.tables for row in t.rows
            )
            pages = [(1, text + "\n" + tables)]
        elif suffix in {".md", ".txt"}:
            pages = [(1, content.decode("utf-8-sig"))]
        else:
            raise ValueError("Supported formats: PDF, DOCX, Markdown, UTF-8 text.")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Cannot read this document. Check its format and encoding.") from exc
    if sum(len(t) for _, t in pages) > MAX_CHARS:
        raise ValueError("Maximum extracted text length is 300,000 characters.")
    if not any(t.strip() for _, t in pages):
        raise ValueError("No text found. Scanned PDFs need OCR before upload.")
    return pages


def chunk_pages(pages, size=150, overlap=30):
    if size <= overlap or overlap < 0:
        raise ValueError("Chunk size must exceed nonnegative overlap")
    chunks = []
    for page, text in pages:
        words = text.split()
        for start in range(0, len(words), size - overlap):
            section = words[start : start + size]
            if section:
                chunks.append({"page": page, "text": " ".join(section)})
            if start + size >= len(words):
                break
    return chunks


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, digest TEXT UNIQUE NOT NULL,
                pages INTEGER NOT NULL, bytes INTEGER NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY, document_id TEXT REFERENCES documents(id) ON DELETE CASCADE,
                page INTEGER, text TEXT NOT NULL, vector TEXT, fingerprint TEXT);
            CREATE INDEX IF NOT EXISTS chunks_document ON chunks(document_id);
            """)

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def documents(self):
        with self.connect() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    "SELECT d.*, COUNT(c.id) AS chunks FROM documents d LEFT JOIN chunks c ON d.id=c.document_id GROUP BY d.id ORDER BY d.created,d.name"
                )
            ]

    def ingest(self, name, content, provider):
        digest = hashlib.sha256(content).hexdigest()
        with self.connect() as conn:
            existing = conn.execute("SELECT id FROM documents WHERE digest=?", (digest,)).fetchone()
            if existing:
                return {"id": existing["id"], "duplicate": True}
        pages = extract(name, content)
        chunks = chunk_pages(pages)
        vectors = provider.embed([c["text"] for c in chunks])
        doc_id = digest[:20]
        # Extraction and provider calls finish before opening the write transaction.
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if conn.execute("SELECT id FROM documents WHERE digest=?", (digest,)).fetchone():
                return {"id": doc_id, "duplicate": True}
            conn.execute(
                "INSERT INTO documents(id,name,digest,pages,bytes) VALUES(?,?,?,?,?)",
                (doc_id, name, digest, len(pages), len(content)),
            )
            conn.executemany(
                "INSERT INTO chunks(document_id,page,text,vector,fingerprint) VALUES(?,?,?,?,?)",
                [
                    (
                        doc_id,
                        c["page"],
                        c["text"],
                        json.dumps(v) if v else None,
                        provider.fingerprint,
                    )
                    for c, v in zip(chunks, vectors)
                ],
            )
        return {"id": doc_id, "duplicate": False, "chunks": len(chunks)}

    def chunks(self):
        with self.connect() as conn:
            rows = [
                dict(r)
                for r in conn.execute(
                    "SELECT c.*, d.name FROM chunks c JOIN documents d ON c.document_id=d.id ORDER BY c.id"
                )
            ]
        for r in rows:
            r["vector"] = json.loads(r["vector"]) if r["vector"] else None
        return rows

    def delete(self, doc_id):
        with self.connect() as conn:
            return conn.execute("DELETE FROM documents WHERE id=?", (doc_id,)).rowcount > 0
