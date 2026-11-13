# Retrieval-augmented generation

RAG retrieves evidence from an external corpus before asking a language model to answer. The pipeline is ingestion, chunking, indexing, retrieval, and grounded generation. Documents can be updated without retraining the language model. Retrieval failures and generation failures must be evaluated separately.


Hybrid search combines keyword-based retrieval such as BM25 with dense vector similarity. Reciprocal Rank Fusion combines ranked lists using the sum of 1 / (60 + rank) for each candidate. RRF avoids assuming that BM25 scores and cosine similarity share a comparable scale. Character TF-IDF is a lexical baseline and must not be described as a semantic embedding model.

## Lexical retrieval

BM25 scores matching terms using term frequency, inverse document frequency, and document-length normalization. Rare terms contribute more evidence than terms that occur almost everywhere in a collection. Term-frequency saturation prevents repeated mentions from increasing a score without bound. The length normalization parameter adjusts how strongly a long passage is penalized compared with a shorter one. Exact identifiers, error codes, and product names are often good matches for lexical retrieval. A query using a different vocabulary from the source can still fail even when the source contains the desired information.

## Dense retrieval

An embedding model maps a question and a passage into numerical vectors in a shared space. Cosine similarity compares their directions. This can retrieve passages that express a related idea using different words, provided the embedding model has learned the relationship. Similarity is not a probability of correctness, and a seemingly high cosine score does not establish that a passage contains an answer. Model choice, language coverage, domain vocabulary, and query formulation all affect results. Document and query embeddings must use compatible models and dimensions.

## Combining and inspecting results

Rank fusion uses the positions of candidates rather than directly adding incompatible raw scores. A passage that performs well in both rankings can rise above a passage that appears in only one. The resulting list still needs a bounded context budget: sending every passage to a language model increases cost, can bury the relevant evidence, and makes source inspection harder. A top-k setting should be evaluated against the kinds of questions the application needs to answer. A learned reranker can refine a candidate list, but it adds a separate model call and should be introduced only after measuring the retrieval failure it is intended to fix.
