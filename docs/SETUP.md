# Technical setup

## Local environment

Use Python 3.11 or newer. Python 3.12 is the container default.

```bash
git clone https://github.com/iYm10/Bayan-RAG.git
cd Bayan-RAG
python -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements.lock
cp .env.example .env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

On Windows, activate with `.venv\Scripts\activate` instead. Open `http://localhost:8000`. In **Document library**, load the sample collection or add a supported document. The application starts with an empty library; it never silently mixes sample data into an uploaded corpus.

`RAG_PROVIDER=demo` is the default. It runs retrieval without a language model and returns clearly labeled source excerpts. Questions are independent; conversation history is not used as model context. Uploaded source files are not retained. Extracted text and optional vectors are stored in `storage/bayan.db`.

## OpenAI

Set these values in the local `.env` file:

```dotenv
RAG_PROVIDER=openai
OPENAI_API_KEY=your-own-key
OPENAI_CHAT_MODEL=gpt-4.1-mini
OPENAI_EMBED_MODEL=text-embedding-3-small
RAG_DATABASE=storage/openai.db
```

Restart the server and ingest documents into the new database. This mode sends document text and questions to OpenAI and can incur provider charges. Keep the key server-side, and never commit `.env`. Model availability depends on the account. A provider error remains an error; there is no silent fallback to a different model.

## Ollama

Install and start Ollama separately, then prepare compatible embedding and chat models:

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
```

```dotenv
RAG_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=qwen2.5:7b
OLLAMA_EMBED_MODEL=nomic-embed-text
RAG_DATABASE=storage/ollama.db
```

Restart and ingest the corpus. Hardware requirements depend on the selected models. If the embedding model, provider, or provider URL changes, use a new database or remove and re-upload the documents. Mixing incompatible embeddings is rejected.

## Verification

```bash
python -m unittest discover -s tests -v
python scripts/evaluate.py
```

The evaluation script honors `RAG_PROVIDER`. Use `RAG_PROVIDER=demo python scripts/evaluate.py` for an offline report. Pass a destination file to preserve the committed reference report during experiments. Connected evaluation embeds a fresh reference collection and sends queries to the configured provider; it does not generate answers.

Optional code-quality and browser tools:

```bash
python -m pip install '.[dev]'
ruff check app tests scripts
ruff format --check app tests scripts
python -m playwright install chromium
python scripts/browser_check.py
```

The browser check requires the application to be running. It uploads and removes a temporary fixture and loads the sample collection. Run it against a disposable demo database. Set `BAYAN_BASE_URL` to select another local server; `CHROMIUM_PATH` selects an existing browser executable.

## Container

```bash
docker build -t bayan-rag .
docker run --rm -p 127.0.0.1:8000:8000 -v bayan-data:/app/storage bayan-rag
```

The container uses a non-root user, a health check, and offline demo mode by default. Bind to loopback for personal use. When connecting to a host-based Ollama server from a container, configure a URL reachable from inside the container; `localhost` refers to the container itself.

## Deployment boundary

Do not expose the application directly to untrusted users. Public hosting needs authentication, authorization, HTTPS, reverse-proxy body limits, rate limits, file-scanning/parser isolation, and retention policies. The 10 MB file-read limit is not a complete network request-body limit. This reference application does not provide those production controls.
