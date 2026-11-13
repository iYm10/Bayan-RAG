# Chunking and document ingestion

Chunking splits documents into units that fit a retrieval and generation context. Small chunks may omit necessary context; large chunks may dilute relevance. Overlap keeps a small amount of shared text between adjacent chunks. The correct chunk size depends on the corpus, language, model tokenization, and evaluation results.


Bayan-RAG uses page-aware windows of 150 whitespace-separated words with 30 words of overlap. These are word counts, not model token counts. PDF chunks retain their original page number. DOCX and text documents use a logical page value of 1 because reliable rendered pagination is unavailable. SHA-256 content hashes prevent duplicate uploads. Extraction and embeddings finish before the database write transaction, so failed embeddings do not leave partially indexed documents.

## Extraction quality

Text extraction is a distinct stage from retrieval. A digitally generated PDF may contain selectable text, while a scanned page may contain only pixels. A text-only parser cannot read the latter without an OCR stage. Even selectable text can arrive in the wrong reading order when a page has columns, complex tables, headers, or positioned labels. Reviewing extracted passages is therefore part of validating a corpus. A successful file upload means the parser found text; it does not guarantee that the extracted text preserves every relationship in the original layout.

## Boundary tradeoffs

Fixed word windows are predictable and easy to inspect, but can split a sentence or separate a heading from its explanation. Overlap helps preserve nearby context at the cost of repeated text and additional index entries. Page boundaries create a different tradeoff: retaining them keeps PDF page citations accurate, but a paragraph that crosses a page may be separated. Alternatives include sentence boundaries, recursive separators, section-aware splitting, and parent-child retrieval. These approaches need evaluation on representative documents before replacing the simple baseline.

## Updating a collection

Content-addressed ingestion detects the same file bytes even if the filename changes. A revised document has a new digest and is treated as a separate item. Remove the older version when only the latest version should be searched. The application stores extracted passages rather than original files, so source names and page metadata must remain attached to every chunk. Embeddings also need a model identity: vectors from incompatible embedding models cannot be mixed just because their lengths happen to match. A model change should trigger a deliberate re-indexing step rather than silently reusing old vectors.
