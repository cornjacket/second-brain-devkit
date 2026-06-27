# Second Brain Developer Kit — System Memory

## Tech Stack
- Runtime: Python 3.11+
- Databases: Flat-file SQLite 3 (utilizing the `sqlite-vec` binary extension)
- Embeddings: `nomic-embed-text` (local, via Ollama) — 768-dimension vectors, cosine distance. The SAME model MUST be used by the pre-commit hook (note embedding) and the search query path; mismatched models produce incomparable vectors.
- Encoding: UTF-8 strict

## Style & Conventions
- Naming: Lowercase kebab-case for all source notes (`sample-note.md`)
- Vector Payload: Dotted prefix with explicit suffix naming convention (`.sample-note.embed.json`) in the same directory. This ensures it is hidden by default.
- Imports: Use standard library unless explicitly defined in requirements.txt

## Execution Commands
- Build/Hydrate Cache: `python3 scripts/hydrate_cache.py`
- Execute Search: `python3 scripts/search_vault.py "<query>"`
- Environment Sanity Check: `python3 -c "import sqlite3, sqlite_vec; print(sqlite_vec.__version__)"`

## Safety Prohibitions
- NEVER use third-party cloud vector stores (Pinecone, Milvus, Supabase)
- NEVER allow git conflict markers to inject into sidecar files (`merge=binary` enforced for `.*.embed.json`)
