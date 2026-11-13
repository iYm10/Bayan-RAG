"""Gradio entrypoint for the no-provider-cost Hugging Face demo."""

import json
import os
from pathlib import Path

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import gradio as gr  # noqa: E402

from app.space_session import ROOT, add_document, answer, new_session  # noqa: E402
from app.store import MAX_BYTES  # noqa: E402

# ZeroGPU requires a registered GPU workload. Plain CPU retrieval remains separate.
if os.getenv("SPACE_ID"):
    import spaces

    from app.semantic_space import semantic_answer

    semantic_job = spaces.GPU(semantic_answer, duration=120)
else:
    semantic_job = None


def ask_semantic(question, session, k):
    if semantic_job is None:
        raise gr.Error("Semantic search is available on the hosted ZeroGPU Space.")
    try:
        return semantic_job(question, session, k)
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc


def ask(question, session, strategy, k):
    try:
        return answer(question, session, strategy, k)
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc


def upload(path, session):
    if not path:
        raise gr.Error("Choose a document first.")
    try:
        with open(path, "rb") as file:
            content = file.read(MAX_BYTES + 1)
        updated, message = add_document(session, Path(path).name, content)
        return updated, message, None
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc


def reset():
    return new_session(), "Sample collection restored for your session.", "", [], [], None


with gr.Blocks(title="Bayan-RAG", delete_cache=(300, 3600)) as demo:
    session = gr.State(value=new_session, time_to_live=3600)
    gr.Markdown(
        "# Bayan-RAG\n### Knowledge, grounded.\nExplore technical documents through traceable evidence and inspectable retrieval."
    )
    gr.Markdown(
        "**Free demo:** BM25 + character TF-IDF retrieval with verbatim source excerpts. No generative LLM, API key, or paid inference service is used."
    )
    with gr.Tab("Knowledge assistant"):
        question = gr.Textbox(
            label="Ask about your documents",
            placeholder="How does hybrid search work?",
            max_lines=4,
        )
        with gr.Row():
            strategy = gr.Dropdown(["hybrid", "bm25"], value="hybrid", label="Retrieval strategy")
            k = gr.Slider(1, 8, value=4, step=1, label="Evidence budget")
        with gr.Row():
            search = gr.Button("Find evidence", variant="primary")
            semantic = gr.Button("Semantic search · ZeroGPU")
        gr.Markdown(
            "Semantic search adds MiniLM embeddings and uses your free ZeroGPU quota. First use downloads model weights and can take longer. Both search options return source excerpts, not generated answers."
        )
        gr.Examples(
            [
                ["How does hybrid search combine BM25 and vector similarity?"],
                ["What do Recall and Mean Reciprocal Rank measure?"],
                ["What is the price of gold today?"],
            ],
            inputs=question,
        )
        response = gr.Textbox(label="Source excerpts", lines=12, interactive=False)
        evidence = gr.Dataframe(
            headers=["Source", "Document", "Page", "RRF", "BM25"],
            interactive=False,
            label="Evidence ranking",
        )
        gr.Markdown(
            "Ranking scores are not confidence estimates. PDF pages retain source numbering; text and DOCX use logical page 1."
        )
        passages = gr.JSON(label="Full evidence passages")
    with gr.Tab("Session library"):
        gr.Markdown(
            "Each browser session starts with five sample documents. Uploaded text is isolated in your session and is temporary. Avoid sensitive files on a public demo. Gradio may cache upload files for up to an hour; the collection resets after inactivity or a server restart."
        )
        file = gr.File(
            label="Add a document", file_types=[".pdf", ".docx", ".md", ".txt"], type="filepath"
        )
        ingest = gr.Button("Index in my session")
        status = gr.Textbox(
            value="Five reference documents are ready to explore.",
            label="Library status",
            interactive=False,
        )
        clear = gr.Button("Reset to sample collection")
    with gr.Tab("Reference evaluation"):
        gr.Markdown(
            "The committed offline benchmark uses 12 questions and 5 documents. Both retrieval strategies tie on this small reference set. These scores do not measure generated-answer accuracy or your uploaded documents."
        )
        gr.JSON(
            value=json.loads((ROOT / "docs/evaluation-results.json").read_text()),
            label="Reproducible reference results",
        )
    semantic.click(
        ask_semantic,
        [question, session, k],
        [response, evidence, passages],
        api_visibility="private",
    )
    search.click(
        ask,
        [question, session, strategy, k],
        [response, evidence, passages],
        api_visibility="private",
    )
    question.submit(
        ask,
        [question, session, strategy, k],
        [response, evidence, passages],
        api_visibility="private",
    )
    ingest.click(upload, [file, session], [session, status, file], api_visibility="private")
    clear.click(
        reset, [], [session, status, response, evidence, passages, file], api_visibility="private"
    )

if __name__ == "__main__":
    demo.queue(max_size=20, default_concurrency_limit=2).launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        max_file_size="10mb",
        state_session_capacity=100,
        share=False,
    )
