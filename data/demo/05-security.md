# RAG security and operational boundaries

Prompt injection occurs when untrusted document text tries to override application instructions. Retrieved passages must be treated as data, never as privileged system instructions. Keeping the system message separate, requiring structured output, validating citation IDs, and limiting tool access reduce risk but do not eliminate prompt injection. Bayan-RAG gives the answering model no tools and no access to server-side API keys.


This is a single-user reference application, not an authenticated multi-tenant service. Run it on a trusted machine or private network. Public hosting needs authentication, authorization, rate limits, request body limits at a reverse proxy, malware scanning, robust parsing isolation, HTTPS, and retention policies. API keys stay in server-side environment variables. Demo mode makes no model-provider calls. OpenAI mode sends indexed text and questions to the configured cloud provider. Ollama mode sends them to the configured local server.

## File and browser boundaries

Uploaded files are untrusted parser inputs. File extensions, byte limits, expanded archive limits, extracted-text limits, and page-count limits reduce accidental resource use but do not turn a parser into a security sandbox. A publicly hosted service should isolate extraction workers and apply network-level request limits before a multipart upload is buffered. Filenames and retrieved text must be rendered as text in the browser rather than inserted as HTML. A same-origin content-security policy and origin checks provide additional browser protections; they do not replace user authentication.

## Secrets and model access

A language model receives a bounded evidence payload, not the process environment. Provider keys belong in server-side configuration and should not appear in HTML, JavaScript, logs, or returned provider error bodies. No execution, browsing, filesystem, or shell tools are attached to the answering model. This limits what a malicious passage can cause through the model interface. It does not prove immunity to misleading instructions or unsupported answers. Treat any statement about injection resistance as a hypothesis to evaluate with adversarial cases, not a guarantee from a prompt.

## Storage and access control

Deleting a document removes its database records and dependent chunks from the searchable collection. It does not guarantee forensic erasure from SQLite free pages, backups, or filesystem snapshots. A multi-user version would need authorization checks before retrieval, not merely hide documents in the interface after a search. Cloud provider selection also changes the data boundary: users need to understand which text leaves their machine before indexing sensitive material. Operational plans should specify retention, backup access, secret rotation, and incident response alongside model and retrieval choices.
