# Evidence, citations and abstention

Each generated claim must reference one or more evidence IDs from the actual retrieved context. Citation validation rejects IDs outside that context. This verifies citation membership, not whether a cited passage logically supports every claim. Human review or a separately evaluated entailment model is needed to assess semantic support.


Abstention means declining to answer when evidence is missing or insufficient. Lexical overlap and cosine thresholds are heuristics, not calibrated probabilities of correctness. In offline demo mode, Bayan-RAG returns verbatim retrieved excerpts. In connected mode, a language model produces structured claims and can mark the evidence insufficient. The application never silently substitutes a language-model answer with an unlabelled demo response.

## Claims and source boundaries

A citation number is local to one response and identifies one retrieved passage, not an entire external knowledge base. A claim with several clauses needs support for all of those clauses. Attaching a real citation to an invented detail still produces an unsupported answer. The evidence panel exposes the full passage and document metadata so a reader can compare the claim with its source. Source excerpts provide a useful offline inspection mode, but they are not a synthesized answer and should be labeled accordingly.

## Insufficient context

There are two opportunities to abstain. Retrieval can find no candidates under its eligibility rules, or a connected model can judge that the retrieved candidates do not answer the question. A document mentioning a subject does not necessarily provide the requested date, quantity, or procedure. A good insufficiency response states the gap without filling it from unstated outside knowledge. Because the current query interface handles each question independently, a follow-up such as "what about its limitations?" should include the subject explicitly rather than assume that earlier conversation turns were sent to the model.

## Inspectability and trust

The application reports retrieval time separately from total answer time, because model generation can dominate the latter. Raw ranking signals help diagnose why a passage was selected, but cannot be interpreted as calibrated answer confidence. Correctness checks should focus on the evidence and the claim rather than a persuasive tone or a visually precise score. For important decisions, a human should review both the source passage and the original document when available. A future answer-level evaluation should judge faithfulness, completeness, citation support, and whether abstention was appropriate.
