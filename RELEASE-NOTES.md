# Aletheia Agora 0.1.1

This patch fixes ordinary library inventory questions in the independent FastAPI application with its vanilla browser interface.

- "Do I have anything in the library?" and "Can you check if I have anything in the collection?" now use complete archive counts and real saved titles with source links.
- Empty-library checks and conversational phrasing work without a generation model, including when typed into chat.
- Questions about specific topics or dates remain document searches.
- Regression tests cover empty/populated libraries, external Markdown additions and authenticated API requests.

Requires Python 3.12+. Create a separate virtual environment, install `aletheia_agora-0.1.1-py3-none-any.whl` with pip, and run `aletheia-agora`. Existing users can install the wheel with `python -m pip install --upgrade ./aletheia_agora-0.1.1-py3-none-any.whl` in their application environment. Settings, models and Markdown remain in the existing profile. Keyword search works offline; local inference and optional semantic search retain their existing platform and hardware requirements. Qwen remains an optional default download; compatible GGUF and Chat Completions connections are supported.

The release includes a Python wheel, source distribution and SHA-256 checksums. Python is required; Electron and Node.js are not. See README.md for setup and data locations. AGPL-3.0-only; upstream history and attribution retained.
