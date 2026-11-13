"""Dense retrieval executed inside the Hugging Face ZeroGPU allocation."""

from app.retrieval import rank
from app.space_session import format_evidence


def semantic_answer(question, session, k=4):
    # Import model libraries only inside the GPU job, after Spaces initializes.
    import torch
    from sentence_transformers import SentenceTransformer

    if not question.strip() or len(question) > 2000 or not 1 <= int(k) <= 8:
        raise ValueError("Enter a valid question and an evidence budget between 1 and 8.")
    if not torch.cuda.is_available():
        raise ValueError(
            "Semantic search requires the hosted ZeroGPU allocation. Use Find evidence for CPU search."
        )
    chunks = session["chunks"]
    model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2",
        device="cuda",
        trust_remote_code=False,
        model_kwargs={"use_safetensors": True},
    )
    vectors = model.encode(
        [question] + [c["text"] for c in chunks],
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    indexed = [{**c, "vector": v.tolist()} for c, v in zip(chunks, vectors[1:])]
    return format_evidence(rank(question, indexed, int(k), "hybrid", vectors[0]))
