"""Bayan-RAG Gradio workspace: evidence, documents, and evaluation."""

import os
import time
from pathlib import Path

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import gradio as gr  # noqa: E402

from app.space_design import EMPTY_SOURCES, evaluation, library, present, stats  # noqa: E402
from app.space_session import ROOT, add_document, answer, new_session  # noqa: E402
from app.store import MAX_BYTES  # noqa: E402

if os.getenv("SPACE_ID"):
    import spaces

    from app.semantic_space import semantic_answer

    semantic_job = spaces.GPU(semantic_answer, duration=120)
else:
    semantic_job = None


def ask(question, session, strategy, k, semantic=False):
    started = time.perf_counter()
    try:
        if semantic:
            if semantic_job is None:
                raise ValueError(
                    "Semantic search is available on the hosted ZeroGPU Space. You can use Find evidence here."
                )
            result = semantic_job(question, session, k)
        else:
            result = answer(question, session, strategy, k)
        mode = (
            "Semantic + BM25"
            if semantic
            else ("Hybrid retrieval" if strategy == "hybrid" else "BM25 retrieval")
        )
        return present(question, result, (time.perf_counter() - started) * 1000, mode)
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc


def choices(session):
    return gr.update(
        choices=[(name, digest) for digest, name in session["documents"].items()], value=None
    )


def upload(path, session):
    if not path:
        raise gr.Error("Choose a document first.")
    try:
        with open(path, "rb") as file:
            updated, message = add_document(session, Path(path).name, file.read(MAX_BYTES + 1))
        gr.Info(message)
        return updated, message, None, stats(updated), library(updated), choices(updated)
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc


def reset():
    session = new_session()
    gr.Info("Your session has been reset to the reference collection.")
    return (
        session,
        "Sample collection restored for your session.",
        None,
        stats(session),
        library(session),
        choices(session),
        "",
        "",
        EMPTY_SOURCES,
        "Your evidence will appear here",
        [],
    )


def remove(document, session):
    if not document or document not in session["documents"]:
        raise gr.Error("Select a document to remove.")
    updated = {
        "documents": {k: v for k, v in session["documents"].items() if k != document},
        "chunks": [c for c in session["chunks"] if c["document_id"] != document],
    }
    gr.Info("Document removed from your session.")
    return (
        updated,
        "Document removed from this session.",
        stats(updated),
        library(updated),
        choices(updated),
        "",
        "",
        EMPTY_SOURCES,
        "Your evidence will appear here",
        [],
    )


def html_component(value="", **kwargs):
    return gr.HTML(value, apply_default_css=False, **kwargs)


seed = new_session()
metric_cards, evaluation_rows, report = evaluation()
theme = gr.themes.Base(
    primary_hue="green", secondary_hue="green", neutral_hue="stone", font=["Arial", "sans-serif"]
).set(
    body_background_fill="#f8f9f3",
    body_background_fill_dark="#f8f9f3",
    body_text_color="#253a2a",
    body_text_color_dark="#253a2a",
    block_background_fill="#fcfdf7",
    block_background_fill_dark="#fcfdf7",
    input_background_fill="#fffef9",
    input_background_fill_dark="#fffef9",
    input_border_color="#d7e1cc",
    input_border_color_dark="#d7e1cc",
    border_color_primary="#dfe4d6",
    border_color_primary_dark="#dfe4d6",
    button_primary_background_fill="#2d543b",
    button_primary_background_fill_dark="#2d543b",
    button_primary_text_color="#ffffff",
    button_primary_text_color_dark="#ffffff",
    slider_color="#6f965a",
    slider_color_dark="#6f965a",
)

with gr.Blocks(
    title="Bayan-RAG · Knowledge, grounded.", fill_width=True, delete_cache=(300, 3600)
) as demo:
    session = gr.State(value=new_session, time_to_live=3600)
    with gr.Row(elem_id="bayan-shell"):
        with gr.Column(scale=1, min_width=238, elem_id="sidebar"):
            html_component(
                '<div class="brand"><span class="brand-mark"><i></i><i></i><i></i><i></i></span><div>Bayan<span class="brand-light">-RAG</span><small>KNOWLEDGE, GROUNDED.</small></div></div><div class="sidebar-label">YOUR WORKSPACE</div>'
            )
            assistant_nav = gr.Button("✧   Knowledge assistant", elem_id="nav-assistant")
            library_nav = gr.Button("▤   Document library", elem_id="nav-library")
            evaluation_nav = gr.Button("▥   Evaluation lab", elem_id="nav-evaluation")
            html_component(
                '<div class="sidebar-story"><span class="sidebar-label">THE APPROACH</span><h3>Every answer starts<br>with evidence.</h3><p>Retrieve the right context.<br>Make the source visible.<br>Measure what matters.</p><div class="pipeline">RETRIEVE &nbsp; → &nbsp; GROUND &nbsp; → &nbsp; VERIFY</div></div><div class="sidebar-status"><span class="status-light">●</span> &nbsp; Your session, your documents<small>Temporary collection · No paid inference</small><a href="https://github.com/iYm10/Bayan-RAG" target="_blank" rel="noopener noreferrer">Explore the project →</a></div>'
            )
        with gr.Column(scale=5, min_width=0, elem_id="main-column"):
            html_component(
                '<div class="topbar"><div>Workspace<span class="slash">/</span><strong>Knowledge studio</strong></div><div class="topbar-right"><span class="session-tag">PERSONAL SESSION</span><span class="avatar">B</span></div></div>'
            )
            with gr.Tabs(selected="assistant", elem_id="workspace-tabs") as tabs:
                with gr.Tab("Knowledge assistant", id="assistant"):
                    with gr.Row(elem_id="assistant-layout"):
                        with gr.Column(scale=3, min_width=0, elem_id="conversation"):
                            html_component(
                                '<div class="hero"><div class="eyebrow">YOUR TECHNICAL KNOWLEDGE, CONNECTED</div><h1>Good questions deserve<br><em>grounded answers.</em></h1><p>Turn your documents into a knowledge workspace.<br>Ask a question. Follow the evidence. See how it was found.</p></div>'
                            )
                            statistics = html_component(stats(seed))
                            html_component(
                                '<div class="section-caption">A GOOD PLACE TO START</div>'
                            )
                            with gr.Row(elem_id="suggestions"):
                                example_retrieval = gr.Button(
                                    "01 / RETRIEVAL\nWhat makes hybrid search effective?"
                                )
                                example_evaluation = gr.Button(
                                    "02 / EVALUATION\nHow do we measure retrieval quality?"
                                )
                                example_security = gr.Button(
                                    "03 / SECURITY\nHow do we handle untrusted text?"
                                )
                            result_html = html_component("")
                            with gr.Group(elem_id="composer"):
                                question = gr.Textbox(
                                    label="Ask about your documents",
                                    show_label=False,
                                    placeholder="Ask a question about your documents…",
                                    lines=2,
                                    max_lines=5,
                                    max_length=2000,
                                    elem_id="question-box",
                                )
                                with gr.Row(elem_id="composer-actions"):
                                    search = gr.Button(
                                        "Find evidence  →",
                                        variant="primary",
                                        elem_id="ask-button",
                                        scale=2,
                                    )
                                    semantic = gr.Button(
                                        "Semantic search · ZeroGPU",
                                        elem_id="semantic-button",
                                        scale=2,
                                    )
                            html_component(
                                '<div class="composer-note"><b>Answers linked to your sources.</b> This demo returns verbatim excerpts, not generated synthesis. Semantic search uses free ZeroGPU quota; first use can take longer.</div>'
                            )
                            with gr.Accordion("Copy source excerpts", open=False):
                                response = gr.Textbox(
                                    label="Source excerpts",
                                    lines=8,
                                    interactive=False,
                                    buttons=["copy"],
                                    elem_id="source-excerpts",
                                )
                        with gr.Column(scale=1, min_width=250, elem_id="context-column"):
                            html_component(
                                '<div class="panel-heading">RETRIEVAL CONTEXT <span>⌁</span></div>'
                            )
                            strategy = gr.Dropdown(
                                [
                                    ("Hybrid search", "hybrid"),
                                    ("Keyword (BM25)", "bm25"),
                                ],
                                value="hybrid",
                                label="Search strategy",
                            )
                            k = gr.Slider(
                                1,
                                8,
                                value=4,
                                step=1,
                                label="Evidence budget",
                                info="Fewer passages for focus. More for context.",
                            )
                            html_component('<div class="panel-heading">SOURCE TRAIL</div>')
                            retrieval_status = gr.Markdown(
                                "Your evidence will appear here", elem_id="retrieval-status"
                            )
                            source_cards = html_component(EMPTY_SOURCES)
                            html_component(
                                '<div class="context-note">ⓘ &nbsp; Retrieval scores rank evidence. They are not confidence estimates.</div>'
                            )
                            with gr.Accordion("Inspect ranking scores", open=False):
                                evidence = gr.Dataframe(
                                    headers=["Source", "Document", "Page", "RRF", "BM25"],
                                    interactive=False,
                                    label="Evidence ranking",
                                )
                with gr.Tab("Session library", id="library"):
                    with gr.Column(elem_classes="library-area"):
                        html_component(
                            '<div class="page-title"><div class="eyebrow">THE KNOWLEDGE LAYER</div><h1>Your document library.</h1><p>A clear source of truth. Every document is split, indexed, and traceable.</p></div>'
                        )
                        file = gr.File(
                            label="Add knowledge to your workspace · PDF, DOCX, MD, TXT · up to 10 MB",
                            file_types=[".pdf", ".docx", ".md", ".txt"],
                            type="filepath",
                            elem_id="upload-file",
                        )
                        with gr.Row():
                            ingest = gr.Button(
                                "Index in my session  →", variant="primary", elem_id="ingest-button"
                            )
                            clear = gr.Button("Reset to sample collection", elem_id="reset-button")
                        status = gr.Textbox(
                            value="Five reference documents are ready to explore.",
                            label="Library status",
                            interactive=False,
                        )
                        html_component(
                            '<div class="section-caption">INDEXED DOCUMENTS · CONTENT-ADDRESSED & DUPLICATE-SAFE</div>'
                        )
                        documents = html_component(library(seed))
                        with gr.Accordion("Manage your collection", open=False):
                            selected_document = gr.Dropdown(
                                choices=[
                                    (name, digest) for digest, name in seed["documents"].items()
                                ],
                                label="Document to remove",
                            )
                            delete = gr.Button("Remove selected document", elem_id="remove-button")
                        html_component(
                            '<div class="quiet-label">Your collection is isolated to this browser session and expires after inactivity or a restart. Uploads may remain in the temporary cache for up to an hour. Use non-sensitive documents in this public demo.<br>PDF sources retain original page numbers. DOCX and text files use logical page 1. Scanned PDFs require OCR.</div>'
                        )
                with gr.Tab("Reference evaluation", id="evaluation"):
                    with gr.Column(elem_classes="evaluation-area"):
                        html_component(
                            '<div class="page-title"><div class="eyebrow">MEASURE BEFORE YOU CLAIM</div><h1>Evidence meets evaluation.</h1><p>A transparent reference benchmark. Every result has a question behind it.</p></div>'
                        )
                        html_component(
                            '<div class="evaluation-banner"><b>A small benchmark. An honest signal.</b><br>12 hand-authored questions · 5 reference documents · top 4 chunks. These committed results measure offline retrieval, not generated-answer correctness. Uploaded documents and ZeroGPU search are excluded.</div>'
                        )
                        html_component(metric_cards)
                        html_component(
                            '<div class="quiet-label">BM25 and offline hybrid search tie on this reference collection. This is a regression baseline, not evidence of superiority or production accuracy.</div>'
                        )
                        gr.Dataframe(
                            value=evaluation_rows,
                            headers=[
                                "Question",
                                "Expected document",
                                "Retrieved documents",
                                "Result",
                            ],
                            interactive=False,
                            label="Question-level results",
                            wrap=True,
                        )
                        with gr.Accordion("Inspect the full benchmark report", open=False):
                            gr.JSON(value=report, label="Reproducible reference results")
    query_outputs = [response, result_html, source_cards, retrieval_status, evidence]
    search.click(ask, [question, session, strategy, k], query_outputs, api_visibility="private")
    question.submit(ask, [question, session, strategy, k], query_outputs, api_visibility="private")
    semantic.click(
        lambda q, s, mode, count: ask(q, s, mode, count, semantic=True),
        [question, session, strategy, k],
        query_outputs,
        api_visibility="private",
    )
    for button, prompt in [
        (example_retrieval, "How does hybrid search combine BM25 and vector similarity?"),
        (example_evaluation, "What do Recall and Mean Reciprocal Rank measure?"),
        (example_security, "How can prompt injection in retrieved documents be mitigated?"),
    ]:
        button.click(lambda value=prompt: value, outputs=question, api_visibility="private").then(
            ask, [question, session, strategy, k], query_outputs, api_visibility="private"
        )
    ingest.click(
        upload,
        [file, session],
        [session, status, file, statistics, documents, selected_document],
        api_visibility="private",
    )
    clear.click(
        reset,
        [],
        [session, status, file, statistics, documents, selected_document, *query_outputs],
        api_visibility="private",
    )
    delete.click(
        remove,
        [selected_document, session],
        [session, status, statistics, documents, selected_document, *query_outputs],
        api_visibility="private",
    )
    assistant_nav.click(
        lambda: gr.Tabs(selected="assistant"), outputs=tabs, api_visibility="private"
    )
    library_nav.click(lambda: gr.Tabs(selected="library"), outputs=tabs, api_visibility="private")
    evaluation_nav.click(
        lambda: gr.Tabs(selected="evaluation"), outputs=tabs, api_visibility="private"
    )

if __name__ == "__main__":
    demo.queue(max_size=20, default_concurrency_limit=2).launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        max_file_size="10mb",
        state_session_capacity=100,
        share=False,
        theme=theme,
        css=(ROOT / "app/static/gradio.css").read_text(),
        footer_links=[],
    )
