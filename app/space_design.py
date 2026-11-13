"""Escaped presentation helpers for the Gradio workspace."""

import html
import json
from collections import Counter

from app.space_session import ROOT

EMPTY_SOURCES = '<div class="empty-evidence"><span>▧</span><h3>Your source trail</h3><p>Ask a question to inspect the passages behind the answer.</p></div>'


def stats(session):
    return f'<div class="stats-strip"><div><strong>{len(session["documents"])}</strong><span>Documents indexed</span></div><div><strong>{len(session["chunks"])}</strong><span>Searchable chunks</span></div><div><strong class="text-stat">Hybrid</strong><span>Evidence-first retrieval</span></div></div>'


def library(session):
    counts = Counter(c["document_id"] for c in session["chunks"])
    rows = []
    for digest, name in session["documents"].items():
        rows.append(
            f'<div class="library-row"><span class="file-icon">{html.escape(name.rsplit(".", 1)[-1].upper())}</span><div><b>{html.escape(name)}</b><small>{counts[digest]} searchable chunks · Available in this session</small></div><span class="indexed">● Indexed</span></div>'
        )
    return '<div class="library-list">' + "".join(rows) + "</div>"


def present(question, result, elapsed_ms, mode):
    text, rows, sources = result
    header = f'<div class="question-bubble"><span>YOUR QUESTION</span><p>{html.escape(question)}</p></div>'
    if not sources:
        return (
            text,
            header
            + '<div class="answer-card"><span class="answer-label">NO MATCHING EVIDENCE</span><p>There is not enough matching evidence in your collection. Try a more specific question or add a relevant document.</p></div>',
            EMPTY_SOURCES,
            "No evidence found",
            rows,
        )
    excerpts = "".join(
        f'<div class="excerpt"><p>{html.escape(s["text"])}</p><a class="citation-link" href="#evidence-{s["source"]}">[{s["source"]}] {html.escape(s["document"])} · page {s["page"]} →</a></div>'
        for s in sources[:2]
    )
    answer_html = (
        header
        + f'<div class="answer-card"><span class="answer-label">✧ &nbsp; SOURCE EXCERPTS</span>{excerpts}<div class="answer-foot">{len(sources)} sources retrieved <span>·</span> {elapsed_ms:,.0f} ms <span>·</span> {html.escape(mode)}</div></div>'
    )
    cards = []
    for source, row in zip(sources, rows):
        cards.append(
            f'<details class="evidence-card" id="evidence-{source["source"]}"><summary><span class="source-num">{source["source"]:02}</span><b>{html.escape(source["document"])}</b><span class="page-label">p. {source["page"]}</span></summary><p>{html.escape(source["text"])}</p><div class="score-line">RRF {row[3]:.5f} &nbsp; · &nbsp; BM25 {row[4]:.3f}</div></details>'
        )
    return text, answer_html, "".join(cards), f"{len(sources)} passages · {mode}", rows


def evaluation():
    report = json.loads((ROOT / "docs/evaluation-results.json").read_text())
    metrics = report["hybrid"]
    cards = (
        '<div class="evaluation-metrics">'
        + "".join(
            f"<div><span>{label}</span><strong>{value}</strong><small>{description}</small></div>"
            for label, value, description in [
                ("RECALL @ 4", f"{metrics['recall_at_k']:.3f}", "Relevant documents retrieved"),
                ("MRR @ 4", f"{metrics['mrr_at_k']:.3f}", "First relevant document rank"),
                (
                    "NEGATIVE ABSTENTION",
                    f"{metrics['negative_abstention_rate']:.0%}",
                    "Out-of-scope questions rejected",
                ),
            ]
        )
        + "</div>"
    )
    rows = []
    for item in metrics["results"]:
        rows.append(
            [
                item["question"],
                ", ".join(item["expected"]) or "No relevant document",
                ", ".join(item["retrieved"]) or "None",
                "Abstained"
                if item["expected_abstention"] and item["retrieval_abstained"]
                else f"Recall {item['recall']}",
            ]
        )
    return cards, rows, report
