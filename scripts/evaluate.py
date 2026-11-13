"""Write a reproducible offline retrieval report without touching user data."""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.main import evaluate  # noqa: E402
from app.provider import Provider  # noqa: E402
from app.store import Store  # noqa: E402


def main():
    provider = Provider()
    with tempfile.TemporaryDirectory() as directory:
        store = Store(Path(directory) / "evaluation.db")
        for path in sorted((ROOT / "data/demo").glob("*.md")):
            store.ingest(path.name, path.read_bytes(), provider)
        dataset = json.loads((ROOT / "data/evaluation.json").read_text())
        report = {
            "provider": provider.kind,
            "corpus_documents": len(store.documents()),
            "corpus_chunks": len(store.chunks()),
            "hybrid": evaluate(store, provider, dataset),
            "bm25": evaluate(store, provider, dataset, "bm25"),
        }
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/evaluation-results.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n")
    for name in ("hybrid", "bm25"):
        metrics = report[name]
        print(
            f"{name}: Recall@4={metrics['recall_at_k']} MRR@4={metrics['mrr_at_k']} negative-abstention={metrics['negative_abstention_rate']}"
        )


if __name__ == "__main__":
    main()
