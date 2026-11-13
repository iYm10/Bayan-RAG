"""Inspectable lexical and vector retrieval with reciprocal rank fusion."""

import math
import re
import unicodedata
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

STOP = set(
    "the a an is are of to in and for with how what does do can it on as be from this that ما هو هي في من على عن كيف هل و او أو الى إلى الذي التي عند with when why".split()
)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text.lower())
    text = re.sub(r"[\u064b-\u065f\u0670\u0640]", "", text)
    return text.translate(str.maketrans("أإآى", "اااي"))


def tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"[^\W_]+", normalize(text)) if len(w) > 1 and w not in STOP]


def bm25(query: str, texts: list[str]) -> list[float]:
    docs = [tokens(t) for t in texts]
    avg = sum(map(len, docs)) / max(len(docs), 1) or 1
    q = set(tokens(query))
    dfs = {w: sum(w in d for d in docs) for w in q}
    scores = []
    for d in docs:
        counts = Counter(d)
        score = 0.0
        for w in q:
            tf = counts[w]
            idf = math.log(1 + (len(docs) - dfs[w] + 0.5) / (dfs[w] + 0.5))
            score += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * len(d) / avg))
        scores.append(score)
    return scores


def rank(
    query: str, chunks: list[dict], k: int = 5, mode: str = "hybrid", query_vector=None
) -> list[dict]:
    if not chunks or not tokens(query):
        return []
    texts = [c["text"] for c in chunks]
    lexical = np.array(bm25(query, texts))
    if query_vector is not None:
        matrix = np.array([c["vector"] for c in chunks], dtype=float)
        second = cosine_similarity([query_vector], matrix)[0]
        second_name = "embedding_cosine"
    else:
        # Character TF-IDF is a lexical baseline, not a semantic embedding.
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), preprocessor=normalize)
        try:
            matrix = vectorizer.fit_transform(texts)
            second = cosine_similarity(vectorizer.transform([query]), matrix)[0]
        except ValueError:
            second = np.zeros(len(chunks))
        second_name = "character_tfidf"
    # Fixed heuristic thresholds; these are not probabilities of correctness.
    eligible = [
        i
        for i in range(len(chunks))
        if lexical[i] > 0 or (query_vector is not None and second[i] >= 0.35)
    ]
    if not eligible:
        return []
    lists = [sorted(eligible, key=lambda i: (-lexical[i], chunks[i]["id"]))]
    if mode == "hybrid":
        lists.append(sorted(eligible, key=lambda i: (-second[i], chunks[i]["id"])))
    fused = {i: sum(1 / (60 + order.index(i) + 1) for order in lists) for i in eligible}
    ordered = sorted(eligible, key=lambda i: (-fused[i], -lexical[i], chunks[i]["id"]))[:k]
    return [
        {
            **chunks[i],
            "score": round(fused[i], 6),
            "bm25": round(float(lexical[i]), 4),
            "secondary": round(float(second[i]), 4),
            "secondary_type": second_name,
        }
        for i in ordered
    ]
