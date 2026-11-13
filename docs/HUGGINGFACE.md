# Gradio on Hugging Face Spaces

The `space_app.py` entrypoint runs the offline retrieval pipeline through Gradio. The root README contains Spaces metadata, and `requirements.txt` declares the Gradio dependency. The existing FastAPI application remains available as a separate entrypoint.

## Free hosting eligibility

Check the platform's current terms before creating a Space. As checked on November 13, 2026, Hugging Face documents free hosting for up to two ZeroGPU Gradio Spaces on eligible personal accounts: verified email and an account older than 30 days. Ordinary compute-backed Space creation may require a paid plan. Do not select paid hardware for a no-cost deployment.

Official references: [Spaces overview](https://huggingface.co/docs/hub/spaces-overview) and [ZeroGPU eligibility](https://huggingface.co/docs/hub/spaces-zerogpu).

This application does not request a GPU or call an inference provider. Its hosting still requires an eligible free Space allocation. If the account does not offer a free allocation, stop rather than enabling billing.

## Publish

1. Create a public Space called `Bayan-RAG` under your account, selecting the Gradio SDK and an available free hardware option.
2. Upload this repository's tracked files, retaining their directories. Exclude local environments, `.env`, runtime databases, and `.git`.
3. Ensure the root README retains its YAML metadata, particularly `app_file: space_app.py` and the pinned SDK version.
4. Wait for the build and inspect the application logs if startup fails.

No secrets are needed for this demo. API access to create or upload a Space requires authentication; knowing a public account URL does not grant write access.

## GitHub publishing

The `Publish Gradio Space` workflow targets `yahya-ai10/Bayan-RAG`. It uploads source to an existing Gradio Space and never creates paid resources or changes hardware. Without a deployment credential, it reports a skipped upload.

After creating an eligible free Space, create a fine-grained Hugging Face access token with write permission limited to that Space. Add it to the GitHub repository under **Settings → Secrets and variables → Actions**, using the name `HF_TOKEN`. Never put the token in chat, a commit, or the README. Run **Actions → Publish Gradio Space → Run workflow**. Subsequent pushes to `main` also publish updates.

The publisher checks the existing hardware allocation and rejects unknown or paid selections. A successful upload is not proof of a successful application build: inspect the Space runtime and logs afterward.

## Session behavior

Each browser session gets its own in-memory collection, initialized with five reference documents. Uploaded content does not enter another visitor's collection. State expires after an hour of inactivity and is lost on server restart. Uploaded files can remain in Gradio's temporary cache for up to an hour, with periodic cleanup. Reset restores the sample collection; it is not a promise of immediate forensic deletion from caches or platform backups.

The upload limit is 10 MB per file. Sessions are bounded to 15 documents, 600,000 characters of chunk text, and 100 active states. The queue allows 20 waiting requests and two concurrent handlers per event. These limits support a small demonstration, not a production multi-user document service. Avoid uploading sensitive documents to a public demo.

The response contains verbatim passages with numbered sources, not model-generated synthesis. The evaluation tab displays the committed offline reference results, independently of visitors' uploads.

## Local verification

```bash
python -m pip install -r requirements.txt
python space_app.py
```

Open `http://localhost:7860`. The app never switches to a paid provider based on environment variables.
