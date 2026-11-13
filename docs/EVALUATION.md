# Evaluation methodology

The reference evaluation answers a narrow question: does retrieval surface the expected document near the top of a small, fixed corpus?

## Protocol

- Corpus: five hand-authored English technical reference documents in `data/demo/`.
- Questions: twelve fixed cases in `data/evaluation.json`.
- Positive cases: nine questions with one expected document each.
- Negative cases: three questions with no relevant reference document.
- Evidence budget: the top four retrieved **chunks**.
- Strategies: BM25 and hybrid RRF.
- Isolation: a fresh temporary database, separate from uploaded user documents.
- Generation: excluded. No model is asked to judge an answer.

The committed report uses offline mode. Its hybrid strategy combines BM25 and character TF-IDF. Connected runs use the configured embedding provider and should be reported separately.

## Metrics

**Document Recall@4.** Take the first four retrieved chunks, deduplicate their document names, and divide the number of expected documents found by the number of expected documents. Average across positive cases. Multiple chunks from one document cannot increase document recall.

**Document MRR@4.** Deduplicate the first four chunks into an ordered document list, then take the reciprocal rank of the first expected document. A missing expected document contributes zero. Average across positive cases. This is a document-ranking metric over the chunk-limited result list, not chunk-level reciprocal rank.

**Negative-query abstention.** The fraction of negative cases for which retrieval returns no candidates. This does not measure whether a language model abstains after seeing irrelevant passages.

## Interpretation

The committed offline results show Recall@4, MRR@4, and negative-query abstention of `1.0` for both strategies. The collection is small, the questions are written against it, and the positive cases contain helpful lexical overlap. A tie at the ceiling is expected and gives no evidence that hybrid search outperforms BM25.

The evaluation is a transparent regression check, not a general accuracy benchmark. It does not establish performance on unseen corpora, cross-language retrieval, paraphrase-heavy questions, hard negatives with overlapping vocabulary, prompt-injection attacks, or generated-answer faithfulness. The `0.35` dense similarity threshold has not been calibrated on a labeled held-out set.

## Validation layers

1. Behavioral tests validate persistence, deduplication, format handling, empty results, citation contracts, provider failures, and index configuration changes.
2. The fixed retrieval report makes per-question expected and retrieved documents inspectable.
3. Browser checks exercise uploads, navigation, querying, source inspection, evaluation, removal, and mobile overflow.
4. Provider contract tests use mocked responses. They do not establish live provider availability or answer quality. Live OpenAI/Ollama generation requires a configured key/server and a separate evaluation.

## A stronger next experiment

Build an independently reviewed corpus of at least 50 documents and 100–200 held-out questions. Include paraphrases, multiple-source questions, overlapping-vocabulary negatives, and questions with insufficient evidence. Establish relevance labels before changing the retrieval configuration.

Compare keyword-only, dense-only, and hybrid retrieval using the same corpus, evidence budget, and labels. Report recall and rank quality alongside latency distributions. Evaluate answer faithfulness and citation support separately with human review. Keep a final test split untouched while selecting chunk sizes, thresholds, and embedding models.
