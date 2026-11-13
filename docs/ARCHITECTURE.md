# Architecture

Bayan-RAG separates the document lifecycle, retrieval strategy, and answer-generation boundary. FastAPI exposes the pipeline through a same-origin web interface and a typed HTTP API.

## Components

| Module | Responsibility |
| --- | --- |
| `app/store.py` | Format validation, text extraction, page-aware chunking, content hashing, and SQLite persistence |
| `app/retrieval.py` | Normalization, BM25, character TF-IDF, embedding cosine similarity, and rank fusion |
| `app/provider.py` | Explicit OpenAI/Ollama adapters, embedding validation, structured-answer validation |
| `app/main.py` | Request validation, API routes, evaluation orchestration, and browser security headers |
| `app/static/` | Framework-free workspace, document management, source inspection, and evaluation views |
| `scripts/evaluate.py` | Reproducible retrieval report against the reference corpus |
| `tests/` | Behavioral checks for ingestion, retrieval, provider contracts, and evidence boundaries |

## Document lifecycle

1. Accept one supported file, capped at 10 MB at the application read boundary.
2. Extract text; reject encrypted, unreadable, empty, and over-limit documents.
3. Split each PDF page independently into windows of 150 whitespace-separated words, with a 30-word overlap. DOCX paragraphs and tables are extracted into a logical page.
4. Compute a SHA-256 digest. Identical contents are indexed once, regardless of file name.
5. Compute embeddings when a connected provider is configured.
6. Acquire an immediate SQLite write transaction, recheck duplication, and commit the document and all chunks atomically.

Provider failure occurs before persistence, preventing partially indexed documents. Connections close after each operation. Deletion uses foreign-key cascading to remove dependent chunks. PDF processing is limited to 300 pages; extracted text is limited to 300,000 characters; DOCX expanded content is limited to 30 MB. These limits do not replace parser sandboxing or request limits at a reverse proxy.

## Retrieval

BM25 uses `k1 = 1.5` and `b = 0.75`. Tokenization normalizes Unicode, lowercases text, removes a small English/Arabic stop-word list, and normalizes common Arabic orthographic variants. It is intentionally lightweight and does not implement stemming or translation.

Connected hybrid search computes a query embedding and cosine similarity against stored document embeddings. Offline hybrid search computes character TF-IDF similarity with character n-grams of length 3–5. That fallback is lexical and is never presented as dense semantic retrieval.

Candidates need positive BM25 overlap, or a connected embedding cosine similarity of at least `0.35`. Candidate lists are sorted independently and fused using:

```text
RRF(document) = sum(1 / (60 + rank_in_list))
```

The threshold is an uncalibrated heuristic. BM25 mode uses lexical ranking only and makes no query-embedding request. It reports a one-list RRF transformation for a consistent inspection format. Ties are resolved deterministically by chunk ID. Changing the embedding model, provider, or provider URL requires re-indexing; mismatched indexes return HTTP 409.

Every request loads the indexed chunks and computes rankings directly. This is straightforward for a small corpus, but memory consumption and latency grow with corpus size. There is no approximate nearest-neighbor index, learned reranker, background job queue, or distributed cache.

## Answer boundary

Offline mode returns up to two retrieved passages as exact excerpts. Connected mode passes the retrieved context to the language model in a user-data envelope, separate from the system instructions. The model returns an insufficiency flag and a list of claims with source numbers.

The adapter validates response structure, nonempty claims, and citation membership. Unknown or missing citations are rejected instead of being silently removed. No model tools are exposed. This validates the output contract, not factual entailment. A relevant keyword match alone cannot establish that an answer exists in a document.

The UI retains a citation's original source snapshot when inspecting a previous answer. Conversation history is session-only and is not sent to the model; each question is independent. Follow-up questions should include the relevant subject explicitly.

## Data and deployment boundaries

The application is designed for one user on a trusted machine. There is no account system or tenant boundary. It does not execute retrieved instructions, fetch user-supplied URLs, or expose provider keys to the frontend. Browser mutations are checked against the request origin. A content security policy restricts scripts, styles, and network connections to the same origin.

Demo mode performs no model-provider requests. OpenAI mode sends chunks for embeddings and sends questions and retrieved passages for generation. Ollama sends those inputs to its configured server. No original document files are retained; extracted text, file metadata, and optional embeddings are stored in SQLite. Deletion removes database records, but forensic erasure from SQLite pages, filesystem snapshots, or backups is not guaranteed.
