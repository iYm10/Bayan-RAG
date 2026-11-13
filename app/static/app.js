const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};
let busy = false;
let toastTimer;

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) {
    const message =
      typeof data.detail === "string"
        ? data.detail
        : "The request could not be processed.";
    throw new Error(message);
  }
  return data;
}
const post = (path, payload) =>
  api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
function toast(text, error = false) {
  clearTimeout(toastTimer);
  $("#toast").textContent = text;
  $("#toast").className = error ? "error" : "";
  $("#toast").hidden = false;
  toastTimer = setTimeout(() => {
    $("#toast").hidden = true;
  }, 6000);
}
function switchView(view) {
  $$(".view").forEach((n) =>
    n.classList.toggle("active", n.id === `${view}-view`),
  );
  $$(".nav").forEach((n) =>
    n.classList.toggle("active", n.dataset.view === view),
  );
  $("#page-label").textContent = {
    assistant: "Knowledge assistant",
    library: "Document library",
    evaluation: "Evaluation lab",
  }[view];
  if (view === "library") refreshDocuments();
}
$$(".nav").forEach((n) =>
  n.addEventListener("click", () => switchView(n.dataset.view)),
);

async function refreshStats() {
  const stats = await api("/api/stats");
  $("#stat-docs").textContent = stats.documents;
  $("#stat-chunks").textContent = stats.chunks;
  $("#provider-label").textContent = stats.generation
    ? `${stats.provider === "openai" ? "OpenAI" : "Ollama"} connected`
    : "Offline demo mode";
  $("#provider-description").textContent = stats.generation
    ? stats.model
    : "No model-provider calls";
  $("#mode-tag").textContent = stats.generation
    ? `${stats.provider.toUpperCase()} WORKSPACE`
    : "OFFLINE DEMO";
  $("#answer-note").textContent = stats.generation
    ? "Generated answers cite retrieved evidence. Verify important claims."
    : "Demo mode returns source excerpts. Connect a model for generated answers.";
}

function showSources(sources, searched = true) {
  $("#source-count").textContent = sources.length;
  $("#sources").replaceChildren();
  if (!sources.length) {
    const empty = el("div", "empty-sources");
    empty.append(
      el("div", "document-symbol", "▧"),
      el(
        "b",
        "",
        searched ? "No matching evidence" : "Evidence will appear here",
      ),
      el(
        "p",
        "",
        searched
          ? "Try a different question or add relevant documents to the library."
          : "Ask a question to inspect the passages behind the answer.",
      ),
    );
    $("#sources").append(empty);
  }
  sources.forEach((source) => {
    const card = el("article", "source-card");
    card.id = `source-${source.number}`;
    const heading = el("div", "source-heading");
    heading.append(
      el("span", "source-number", String(source.number)),
      el("span", "source-name", source.name),
      el("span", "source-page", `p. ${source.page}`),
    );
    const details = el("details");
    details.append(
      el("summary", "", "Inspect full passage & scores"),
      el("p", "", source.text),
    );
    const scores = el("div", "source-scores");
    scores.append(
      el("div", "", `RRF ${source.score} · BM25 ${source.bm25}`),
      el("div", "", `${source.secondary_type}: ${source.secondary}`),
    );
    details.append(scores);
    card.append(heading, el("p", "", source.text), details);
    $("#sources").append(card);
  });
}

function addMessage(role, text) {
  const message = el("article", `message ${role}`);
  const label = el("div", "message-role");
  label.append(
    el("span", "role-icon", role === "user" ? "→" : "✧"),
    el("span", "", role === "user" ? "YOUR QUESTION" : "BAYAN-RAG"),
  );
  const body = el("div", "message-body", text);
  message.append(label, body);
  $("#messages").append(message);
  return body;
}

async function ask(question) {
  if (busy || !question.trim()) return;
  busy = true;
  $("#ask-button").disabled = true;
  $("#welcome").hidden = true;
  addMessage("user", question);
  const body = addMessage("assistant", "");
  body.append(el("div", "loading", "Retrieving evidence…"));
  $("#question").value = "";
  try {
    const data = await post("/api/query", {
      question,
      k: Number($("#top-k").value),
      mode: $("#strategy").value,
    });
    body.replaceChildren();
    body.append(
      el(
        "div",
        "answer-badge",
        data.answer_type === "extractive"
          ? "SOURCE EXCERPTS · NO LANGUAGE MODEL"
          : "GENERATED ANSWER · CHECK THE EVIDENCE",
      ),
    );
    if (data.insufficient) {
      body.append(
        el(
          "p",
          "claim",
          "There is not enough evidence in the retrieved documents to answer this question. Add a relevant document or make the question more specific.",
        ),
      );
    } else {
      data.claims.forEach((claim) => {
        const p = el("p", "claim", claim.text + " ");
        claim.sources.forEach((n) => {
          const source = data.sources.find((s) => s.number === n);
          const button = el("button", "citation", String(n));
          button.title = source
            ? `${source.name} · page ${source.page}`
            : "Source";
          button.setAttribute("aria-label", `Inspect source ${n}`);
          button.addEventListener("click", () => {
            showSources(data.sources);
            const card = $(`#source-${n}`);
            if (card) {
              card.classList.add("flash");
              card.querySelector("details").open = true;
              card.scrollIntoView({ behavior: "smooth", block: "center" });
              setTimeout(() => card.classList.remove("flash"), 1800);
            }
          });
          p.append(button);
        });
        body.append(p);
      });
    }
    const meta = el("div", "answer-meta");
    meta.append(
      el("span", "", `${data.sources.length} sources retrieved`),
      el("span", "", `${data.retrieval_ms} ms retrieval`),
      el("span", "", `${data.total_ms} ms total`),
    );
    body.append(meta);
    showSources(data.sources);
  } catch (error) {
    body.replaceChildren(el("div", "error-message", error.message));
  } finally {
    busy = false;
    $("#ask-button").disabled = false;
    body.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}
$("#question-form").addEventListener("submit", (e) => {
  e.preventDefault();
  ask($("#question").value.trim());
});
$("#question").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    ask($("#question").value.trim());
  }
});
$$("[data-question]").forEach((button) =>
  button.addEventListener("click", () => ask(button.dataset.question)),
);
$("#top-k").addEventListener("input", () => {
  $("#k-value").textContent = `${$("#top-k").value} chunks`;
});
$("#clear-chat").addEventListener("click", () => {
  if (busy) return;
  $("#messages").replaceChildren();
  $("#welcome").hidden = false;
  showSources([], false);
  $("#question").focus();
});

async function refreshDocuments() {
  try {
    const docs = await api("/api/documents");
    $("#library-count").textContent = docs.length;
    $("#document-list").replaceChildren();
    if (!docs.length)
      $("#document-list").append(
        el(
          "div",
          "library-empty",
          "Your library is ready. Upload a document or load the sample collection to begin.",
        ),
      );
    docs.forEach((doc) => {
      const row = el("div", "document-row");
      const info = el("div", "doc-info");
      info.append(
        el("b", "", doc.name),
        el(
          "small",
          "",
          `${doc.chunks} chunks · ${doc.pages} ${doc.pages === 1 ? "page" : "pages"} · ${(doc.bytes / 1024).toFixed(1)} KB`,
        ),
      );
      const remove = el("button", "delete-doc", "Remove");
      remove.setAttribute("aria-label", `Remove ${doc.name}`);
      remove.addEventListener("click", async () => {
        if (!confirm(`Remove "${doc.name}" and its indexed chunks?`)) return;
        remove.disabled = true;
        try {
          await api(`/api/documents/${doc.id}`, { method: "DELETE" });
          await Promise.all([refreshDocuments(), refreshStats()]);
          showSources([], false);
          toast("Document removed.");
        } catch (error) {
          toast(error.message, true);
          remove.disabled = false;
        }
      });
      row.append(
        el("span", "doc-format", doc.name.split(".").pop().toUpperCase()),
        info,
        el("span", "doc-indexed", "● Indexed"),
        remove,
      );
      $("#document-list").append(row);
    });
  } catch (error) {
    toast(error.message, true);
  }
}

async function upload(file) {
  if (!file) return;
  if (file.size > 10 * 1024 * 1024) {
    toast("Maximum file size is 10 MB.", true);
    return;
  }
  const form = new FormData();
  form.append("file", file);
  $("#upload").disabled = true;
  toast("Extracting and indexing your document…");
  try {
    const result = await api("/api/documents", { method: "POST", body: form });
    await Promise.all([refreshDocuments(), refreshStats()]);
    toast(
      result.duplicate
        ? "This document is already in your library."
        : "Document indexed. Your knowledge workspace is up to date.",
    );
  } catch (error) {
    toast(error.message, true);
  } finally {
    $("#upload").value = "";
    $("#upload").disabled = false;
  }
}
$("#upload").addEventListener("change", (e) => upload(e.target.files[0]));
const zone = $("#upload-zone");
zone.addEventListener("dragover", (e) => {
  e.preventDefault();
  zone.classList.add("dragging");
});
zone.addEventListener("dragleave", () => zone.classList.remove("dragging"));
zone.addEventListener("drop", (e) => {
  e.preventDefault();
  zone.classList.remove("dragging");
  upload(e.dataTransfer.files[0]);
});
$("#seed-button").addEventListener("click", async () => {
  $("#seed-button").disabled = true;
  try {
    const result = await post("/api/demo", {});
    await Promise.all([refreshDocuments(), refreshStats()]);
    toast(`${result.added} sample documents added. Ready to explore.`);
  } catch (error) {
    toast(error.message, true);
  } finally {
    $("#seed-button").disabled = false;
  }
});

$("#evaluate-button").addEventListener("click", async () => {
  const button = $("#evaluate-button");
  button.disabled = true;
  button.textContent = "Evaluating…";
  try {
    const data = await post("/api/evaluate", {});
    $("#eval-recall").textContent = data.recall_at_k.toFixed(3);
    $("#eval-mrr").textContent = data.mrr_at_k.toFixed(3);
    $("#eval-abstention").textContent =
      `${(data.negative_abstention_rate * 100).toFixed(0)}%`;
    $("#baseline-comparison").textContent = data.baseline
      ? `BM25 baseline — Recall@4: ${data.baseline.recall_at_k.toFixed(3)} · MRR@4: ${data.baseline.mrr_at_k.toFixed(3)}. Scores are specific to this small reference set.`
      : data.scope;
    $("#evaluation-results").className = "";
    $("#evaluation-results").replaceChildren();
    data.results.forEach((result) => {
      const row = el("div", "eval-row");
      const details = el("div");
      details.append(
        el("b", "", result.question),
        el(
          "small",
          "",
          `Expected: ${result.expected.join(", ") || "No relevant document"}`,
        ),
        el("small", "", `Retrieved: ${result.retrieved.join(", ") || "None"}`),
      );
      const passed = result.expected_abstention
        ? result.retrieval_abstained
        : result.recall === 1;
      row.append(
        details,
        el(
          "span",
          `eval-result${passed ? "" : " fail"}`,
          result.expected_abstention
            ? passed
              ? "Abstained"
              : "False match"
            : `Recall ${result.recall.toFixed(2)}`,
        ),
      );
      $("#evaluation-results").append(row);
    });
    toast(`Evaluation complete · ${data.cases} questions inspected.`);
  } catch (error) {
    toast(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = "Run evaluation →";
  }
});

refreshStats().catch((error) => {
  $("#provider-label").textContent = "Connection unavailable";
  $("#provider-description").textContent = "Check the server and retry";
  toast(error.message, true);
});
