# API reference

The API uses JSON except for document uploads. A generated OpenAPI document is available at `/openapi.json`. The default CDN-hosted documentation UI is disabled to keep the workspace self-contained and compatible with its same-origin content-security policy.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Application readiness and configured provider, without testing provider connectivity |
| GET | `/api/stats` | Document/chunk totals and retrieval mode |
| GET | `/api/documents` | Indexed document metadata |
| POST | `/api/documents` | Multipart upload using the `file` field |
| DELETE | `/api/documents/{id}` | Remove a document and its chunks |
| POST | `/api/demo` | Add the five sample documents; repeated calls are duplicate-safe |
| POST | `/api/search` | Retrieve and inspect ranked evidence without generation |
| POST | `/api/query` | Retrieve evidence and produce excerpts or structured generated claims |
| POST | `/api/evaluate` | Evaluate hybrid and BM25 retrieval on an isolated reference collection |

## Query input

```json
{
  "question": "How does hybrid search combine retrieval strategies?",
  "k": 4,
  "mode": "hybrid"
}
```

`question`: 2–2,000 characters, not blank. `k`: 1–8 chunks. `mode`: `hybrid` or `bm25`.

## Query output

```json
{
  "insufficient": false,
  "claims": [
    {"text": "A supported claim or verbatim source excerpt.", "sources": [1]}
  ],
  "sources": [
    {
      "number": 1,
      "id": 7,
      "document_id": "content-derived-id",
      "name": "guide.pdf",
      "page": 3,
      "text": "The original retrieved passage.",
      "score": 0.032787,
      "bm25": 1.85,
      "secondary": 0.72,
      "secondary_type": "embedding_cosine"
    }
  ],
  "answer_type": "generated",
  "retrieval_ms": 25.4,
  "total_ms": 860.2,
  "provider": "openai",
  "mode": "hybrid"
}
```

This response is illustrative, not a measured performance claim. Source numbers are response-local. In demo mode, `answer_type` is `extractive`, `provider` is `demo`, and the secondary score is character TF-IDF cosine similarity. `score` is an RRF ranking value, not a confidence estimate. An insufficiency response has an empty `claims` array and may still contain retrieved sources when the model judges those sources insufficient.

## Errors

- `403`: cross-origin browser mutation rejected.
- `404`: document does not exist.
- `409`: stored embeddings do not match the configured embedding model/provider.
- `422`: invalid query, unsupported format, unreadable content, or extraction/file limit.
- `502`: provider unavailable, malformed provider output, invalid embeddings, or invalid citations.

Provider errors intentionally omit raw provider responses and credentials. Server-side configuration is not editable through the public API.
