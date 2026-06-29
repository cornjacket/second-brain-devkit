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

## Development Workflow
This repo is a **generator**: it produces a `second-brain/` repo. Build each feature with this loop:
1. **Prototype** the feature by hand in the golden reference (`second-brain-test/`) and confirm it behaves as expected. The golden is the known-good *expected output* and serves as the regression baseline.
2. **Productize** it into the devkit — the script, prompt, or harness that generates the feature.
3. **Validate** by running the devkit against a throwaway repo at `sandbox/scratch/`. The harness must **wipe-and-regenerate** `sandbox/scratch/` on every run (never test against stale state), then **diff** the generated output against the golden reference. A clean diff is the acceptance test.

- `sandbox/` is gitignored — it is regenerated output, never committed.
- `second-brain-test/` (golden) answers *"does the feature work?"*; `sandbox/scratch/` answers *"does the devkit generate it correctly?"*
- **Note:** where the golden reference physically lives (and how it stays version-controlled while still exercising the pre-commit hook) is unresolved — see OQ-1 in [open-questions.md](open-questions.md).
