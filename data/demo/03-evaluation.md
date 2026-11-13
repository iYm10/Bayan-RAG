# Retrieval evaluation

Document-level Recall@k measures the fraction of expected relevant documents appearing in the first k retrieved chunks. Multiple chunks from the same document count once. Mean Reciprocal Rank at k averages the inverse rank of the first relevant document in the deduplicated returned document list. A missing relevant result contributes zero. Queries with no relevant document are evaluated separately for retrieval abstention.


A small handcrafted demo set is useful for regression checks, not a claim of production accuracy. Retrieval evaluation does not establish factual correctness, faithfulness, or completeness of generated answers. A stronger study needs held-out questions, diverse real documents, judged relevance, answer-level evaluation, latency distributions, and a comparison against a keyword-only baseline. Benchmark corpus, query set, k, retrieval configuration, and limitations must be reported with every score.

## Separating failure types

A retrieval failure occurs when the useful evidence does not enter the context budget. A generation failure occurs when a model receives useful evidence but produces an unsupported, incomplete, or contradictory answer. Improving the prompt cannot reliably recover a missing passage, while improving retrieval does not guarantee that the model will use a passage correctly. Keep retrieval and generation metrics separate so that an experiment changes the component responsible for the observed error. Source membership checks are useful contract tests, but semantic citation support requires a separate judgment.

## Building a useful test set

Questions should represent realistic user needs rather than simply repeat document headings. Include paraphrases, exact identifiers, questions needing more than one document, and questions that are plausible but not answerable from the corpus. Negative examples with overlapping vocabulary are especially valuable because a keyword match can look relevant without containing an answer. Relevance labels should be reviewed before tuning retrieval. Keep validation questions separate from a final held-out test set; repeatedly changing a system to fit the final set turns it into another development set.

## Performance and experimental discipline

Measure latency across repeated queries and report a distribution rather than one fast request. Record corpus size, index size, provider, embedding model, hardware, context budget, and any caching. Compare retrieval strategies under the same conditions. A top-four chunk budget is not the same as a top-four document budget, because several returned chunks can come from one document. Ceiling scores on a tiny collection are useful for checking regressions but reveal little about which strategy will work better on a larger corpus. Report ties and failures directly, and preserve per-question results so that an aggregate score can be examined.
