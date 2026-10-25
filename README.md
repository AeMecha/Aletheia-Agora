# Aletheia Agora

Aletheia's personal knowledge library as a **FastAPI application with a vanilla HTML/CSS/JavaScript browser interface**. Agora is the meeting place for your archive. No Electron, Node.js, frontend framework or build step is required.

Derived from [Aletheia 0.2.0](https://github.com/AeMecha/Aletheia/tree/v0.2.0), with its Git history and AGPL-3.0-only license retained. The independent native Qt sibling is Aletheia Athenaeum.

## Run

Download the [0.1.1 wheel and source archive](https://github.com/AeMecha/Aletheia-Agora/releases/tag/v0.1.1), or install from this checkout as follows.

Requires Python 3.12+ with SQLite FTS5. The browser interface works on Windows, Linux and macOS; the server can also run headlessly. From this repository:

```sh
python -m venv .venv
# Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install .
aletheia-agora
```

The launcher opens your browser at port 8765. Keyword search works immediately, offline, without native ML libraries or model downloads. Local inference engines download on first use; the large Qwen weights remain an optional, resumable default download. Downloads are SHA-256 verified.

For semantic hybrid search, install `python -m pip install '.[semantic]'`, then choose **Semantic hybrid** in Settings. This downloads the pinned 34 MB BGE search model once. ONNX Runtime and tokenizer wheels must support your platform. Switching search modes rebuilds only the derived index and preserves original Markdown.

Pinned local llama.cpp engines are available for Windows, Linux and macOS on x64 and ARM64. Settings also accept a custom native llama-server executable. Native library availability, OS/CPU/GPU requirements and model memory still govern local inference. API mode needs no local inference engine; this does not claim every architecture is supported.

`python -m aletheia_agora --no-browser` starts without opening a tab. Use the printed launch address, including its private `#token=...` fragment, or enter that server token in the browser dialog. It protects archive, settings, import and model operations and is separate from an AI provider key. `--port` and `--home` select a port and independent data directory. Keep one server process per profile.

By default the server binds only to `127.0.0.1`. For an intentional network deployment, set `ALETHEIA_ACCESS_TOKEN` and select `--host`; put the service behind HTTPS and restrict access. This is a single-user personal library, not a multi-user authorization system.

## Use

- **Librarian:** full-text passage search, optional semantic hybrid search, validated answers and source buttons. Archive overview counts the complete archive without requiring a generation model.
- **Archivist:** generate title, summary, keywords and type; the complete original text remains in the review draft. Saving is always a separate action.
- **Your library:** import Markdown files/folders, filter titles, view originals, edit titles with revision checks, and download exports.
- **Local models:** choose a server-side GGUF path or upload a GGUF from the browser. The model runs on the server computer. It needs a llama.cpp-supported instruction/chat architecture, an embedded chat template and sufficient memory. Qwen is a default, not an identity restriction.
- **APIs:** configurable Chat Completions base URL, key and model ID, model discovery/manual IDs, and LM Studio/Ollama presets. Other native API protocols need a compatible gateway. Models must follow structured JSON instructions; schema/JSON/prompt negotiation retains the same validators.
- **Preferences:** saved light/dark theme, context size, response budget, CPU/automatic acceleration and output-limit parameter. Stored provider keys never return to the browser; blank key fields keep an existing key for the same endpoint, with an explicit clear checkbox.

Default data lives in `%APPDATA%/AletheiaAgora` on Windows or `$XDG_CONFIG_HOME/AletheiaAgora` (normally `~/.config/AletheiaAgora`) on Linux. `ALETHEIA_HOME` overrides it; `ALETHEIA_RESOURCES` selects a pre-provisioned asset cache. Markdown under `knowledge/` is authoritative. `archive-python.sqlite3` is derived; this app does not reuse the Electron search database. Import copies originals and preserves safe Metadata IDs. Back up the profile and externally selected GGUFs. Do not open one profile simultaneously in both applications.

Generation through a remote API sends the current input and retrieved passages to that API. Local generation and search run on the server computer. Browser uploads are stored there. The server's archive path button reports its location; it does not open a file manager on the browser computer.

## Development

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python -m build
```

The Python core is included in this repository so Agora runs independently. Its sibling contains the same core source; neither app requires installing or starting the other. See `ARCHITECTURE.md` for boundaries and `NOTICE` / `THIRD-PARTY-NOTICES.md` for attribution and model licenses.
