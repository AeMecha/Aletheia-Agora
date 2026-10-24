# Architecture

## Independent distribution

This repository includes its own Python app and archive/model core. It needs neither original Aletheia nor its sibling. There is no Electron, Node.js, SillyTavern, Transformers.js or Sharp runtime dependency. Use separate environments and profiles. The sibling includes its own core copy; port core changes with their tests.

## Interface boundary

FastAPI in server.py owns one Service through its lifespan. Vanilla files in static/ use a narrow fetch bridge with no framework or build step. Every /api/ operation requires a per-server bearer token. The launcher passes it in the URL fragment, removed into per-tab session storage. Provider keys never return in state. Static responses apply CSP and expose no private files. Binding defaults to loopback; network binding requires an explicit access token. Run one process per profile and use HTTPS for network deployments.

## Archive and retrieval

config.py validates preferences and saves JSON atomically. A profile lock prevents concurrent processes. archive.py treats knowledge/ Markdown as authoritative; SQLite FTS5 is derived. Imports preserve valid IDs, duplicate IDs fail closed, and SHA-256 revisions protect title edits from overwriting external changes. Periodic scans discover changed files.

Keyword mode uses Python/SQLite with no native ML imports. Optional embeddings.py loads text-only BGE ONNX, applies masked mean pooling and normalizes 384-dimensional vectors. Hybrid search merges lexical and vector passage results. Index signatures distinguish search modes and rebuild derived rows while preserving originals. Source spans use exact Unicode offsets. The Python database is separate from the original JavaScript index.

Inventory questions use complete counts/titles without inference. Other questions retrieve selected passages and pass only bounded evidence to the model. A selected search does not prove archive-wide absence.

## Model ownership and validation

model.py owns a loopback llama-server child or connects to an external Chat Completions API. External servers are never stopped. Local files must be GGUF v2/v3 with an architecture and chat template supported by the engine. assets.py verifies pinned sizes/digests, resumes weight downloads, selects Windows/Linux/macOS x64/ARM64 engines and contains extracted paths. A custom executable supports separately built native engines. Available packages do not guarantee every CPU, GPU or OS version.

Default Qwen is optional. Generic models use schema/JSON/prompt negotiation. protocol.py validates complete responses, metadata, citations and simulated dialogue/tool activity in every mode. Archivist generates metadata, retaining full source verbatim in a review draft; saving is separate. Remote APIs receive input and retrieved passages.

## Verification

Run python -m unittest discover -s tests -v and python -m build. Tests use disposable profiles and synthetic model responses. API acceptance tests exercise the real lifespan, authentication, archive operations and vanilla static assets. CI covers Windows, Linux, macOS and Linux ARM64. Local inference and optional semantic dependencies need platform-specific validation.
