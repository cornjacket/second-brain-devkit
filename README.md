# Second Brain Developer Kit

> **Write for Humans, Index for Machines.**

A dev kit for building a **dual-interface knowledge graph** — a Second Brain that
serves a human (via [Obsidian](https://obsidian.md)) and an AI (via models like
Claude or Gemini) from the same local, plain-text source of truth.

## The Problem

Humans and machines explore knowledge differently:

- **Humans** excel at spatial organization, visual linking, and iterative writing.
- **AI** excels at semantic search, pattern recognition across massive datasets,
  and structured data extraction.

A standard Obsidian vault is great for a human, but feeding raw, unindexed
Markdown to an AI is messy, slow, and expensive against context-window limits.
Conversely, a pure database is a terrible interface for a human trying to write a
journal entry or map out a project.

## The Philosophy

This kit creates a **symbiotic relationship** between the two interfaces instead
of forcing a choice between them:

```
[ Human Interface ]  --->  Obsidian (.md files)
                                 │
                                 ▼  (Automated Tooling / Scripts)
[ Machine Interface ] --->  SQLite Cache (vec0)  --->  AI Agents / LLMs
```

You write plain Markdown. Tooling mirrors those notes — with their tags, links,
and vector embeddings — into a local SQLite cache that AI agents can query
deterministically and cheaply.

## Value for Each Interface

### For the Obsidian User (Human Interface)

- **Zero-friction writing** — keep the clean, future-proof, local-first
  experience of raw Markdown plus Obsidian's plugin ecosystem and graph view.
- **Local ownership** — your notes stay yours, unproprietary, and fully readable
  even if the database layer disappears.
- **Enhanced by AI** — the SQLite layer powers local tools for semantic search,
  backlink suggestions, and structured insights fed back into Obsidian.

### For AI Models (Machine Interface)

- **Structured context (deterministic retrieval)** — query exact context
  (e.g. *"all notes from the last 7 days tagged `#architecture`"*) instead of
  making an LLM parse hundreds of loose text files.
- **Vector / semantic readiness** — `sqlite-vec` stores embeddings alongside
  notes for fast, fully local RAG.
- **Token efficiency** — agents consume dense, clean query results rather than
  burning budget on raw frontmatter, blank lines, and irrelevant file structure.

## How It Works

The pipeline keeps the human-authored Markdown and the machine-readable cache in
sync automatically:

1. **Source Note** → staged → **pre-commit hook** updates a per-note
   `*.embed.json` sidecar (a 768-dim vector array).
2. **Sidecar vectors** → bulk scan → **hydrate** a SQLite `vec0` virtual-table
   cache.
3. **Claude / Gemini terminal input** → Python CLI matcher → SIMD-accelerated
   cosine-distance results.

Embeddings use `nomic-embed-text` (local, via [Ollama](https://ollama.com)). The
**same** model must produce both the committed note vectors and the search-query
vectors — mismatched models yield incomparable results.

> **Authoritative specs.** This README is an overview. The contracts live in two
> places: the **system spec** ([SPEC.md](SPEC.md)) for the three-repo workflow,
> roles, and lifecycle; and the **product spec** (`../second-brain-test/SPEC.md`)
> for a single brain's PARA layout, sidecar schema, embedding contract, cache
> DDL, search CLI, and `register`. Details below are summaries — defer to those.

## The Kit's Mission

This repository is a **generator**. Spinning up a new Second Brain with it should
instantly configure:

- A standardized directory structure (PARA-style or similar clean layout).
- A parsing pipeline that mirrors notes, tags, and links into a local SQLite file.
- An AI-ready interface layer, so pointing a local script, a Claude wrapper, or a
  Gemini pipeline at the cache is trivial.

The result scales: no matter how large the knowledge base grows, it stays
structured enough for an AI to read instantly, yet simple enough to open and edit
in plain text.

## Generate a brain

Create a real Second Brain you own — its own git repo, at a path you choose:

```bash
python3 tools/new_brain.py ~/my-brain
```

This copies the tracked template, seeds the PARA vault, and bootstraps the target
as its **own** git repository (`git init`, the embed pre-commit hook wired via
`core.hooksPath`, and a first commit). The brain is yours from that point on — the
devkit never touches it again. Then:

```bash
cd ~/my-brain
pip install -r requirements.txt     # embed pipeline deps
python3 scripts/self_test.py        # confirm the pipeline is wired
```

- It **refuses** a non-empty target unless you pass `--force` (protects your data).
- It **refuses** to nest inside an existing git repo — a brain must be its own
  top-level repo (choose a standalone path like `~/my-brain`).
- The scaffold is byte-identical to what the devkit validates against the golden
  (Mode A ≡ Mode B), so production output is trusted without re-diffing.

Under the hood, `tools/new_brain.py` (production, Mode B) and the validation
harness `tools/run_sandbox.py` (Mode A) share one generator core
(`tools/generate.py`); only the post-step differs — a first commit you keep vs. a
diff-and-discard. See [SPEC §5.1](SPEC.md).

## Tech Stack

- **Runtime:** Python 3.11+
- **Storage:** flat-file SQLite 3 with the `sqlite-vec` extension (768-dim
  vectors, cosine distance)
- **Embeddings:** `nomic-embed-text` (local, via Ollama)
- **Encoding:** UTF-8 (strict)
- **Frontends:** Claude (Claude Code) and Gemini (Gemini CLI) share one project
  memory file — `GEMINI.md` is a symlink to `CLAUDE.md`.

## Commands

```bash
# Build / hydrate the SQLite cache from sidecar vectors
python3 scripts/hydrate_cache.py

# Run a semantic search over the vault
python3 scripts/search_vault.py "<query>"

# Environment sanity check
python3 -c "import sqlite3, sqlite_vec; print(sqlite_vec.__version__)"
```

## Safety Prohibitions

- **Never** use third-party cloud vector stores (Pinecone, Milvus, Supabase) —
  this kit is local-first by design.
- **Never** allow git conflict markers into sidecar files (`merge=binary` is
  enforced for `.*.embed.json`).

## Project Layout

| Path                 | Purpose                                                        |
| -------------------- | ------------------------------------------------------------- |
| `CLAUDE.md`          | System memory & conventions (shared with Gemini via symlink). |
| `SPEC.md`            | System specification & generator/validation loop.             |
| `PLAN.md`            | Durable milestone tracker for the devkit itself.              |
| `open-questions.md`  | Unresolved design decisions (resolve before finalizing).      |
| `docs/`              | Deep-dive design docs — [`source-map.md`](docs/source-map.md) (what every file does), [`mcp-server.md`](docs/mcp-server.md), [`claude-desktop-workflow.md`](docs/claude-desktop-workflow.md), [`retrieval-quality.md`](docs/retrieval-quality.md). |
| `daily-plan.md`      | Forward-looking, single-day plan (aggregated cross-repo).     |
| `emit-manifest.toml` | What a generated brain contains — classifies every golden file. |
| `template/`          | The tracked, cleaned scaffold the generator copies into a brain. |
| `tests/golden/`      | Vendored golden — the tracked regression baseline the harness diffs against (OQ-1 Option A). |
| `tools/`             | The generator + validation harness (`new_brain.py`, `update_brain.py`, `generate.py`, `run_sandbox.py`, `vendor_golden.py`, `ci.py`, the `check_*` guards). |
| `.github/workflows/` | CI — runs `tools/ci.py` on every push/PR to `main`.           |
| `sandbox/`           | Throwaway generated output for validation (gitignored).       |

The **golden reference** is vendored **into** this repo at `tests/golden/` (plain
tracked files, no `.git`) so the devkit is self-contained — CI checks out only this
repo and never reaches outside it (OQ-1 → Option A). A live sibling at
`../second-brain-test/` (its own `.git` + remote) remains the hand-prototyping
surface where the pre-commit hook fires for real; refresh the snapshot from it with
`python3 tools/vendor_golden.py` (a dev-machine step — CI never runs it).

> **Development model:** *Prototype* a feature by hand in the live golden
> (`../second-brain-test/`), *productize* it into the kit, `vendor_golden.py` to
> refresh `tests/golden/`, then *validate* with `python3 tools/ci.py` (regenerate
> into `sandbox/scratch/` and diff against the vendored golden, plus a Mode-B
> smoke). A clean run is the acceptance test — the same gate CI runs. See
> [CLAUDE.md](CLAUDE.md) for the full workflow and
> [open-questions.md](open-questions.md) for design decisions.

## License

See [LICENSE](LICENSE).
</content>
</invoke>
