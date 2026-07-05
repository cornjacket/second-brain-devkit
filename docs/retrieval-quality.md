# Retrieval quality — hybrid search & embedding prefixes (design)

**Status:** design / backlog (not built). Tracked in
[PLAN.md → Retrieval quality](../PLAN.md#retrieval-quality-backlog-surfaced-2026-07-04).
This document explains two independent improvements to how a brain retrieves notes.

## TL;DR

A brain currently retrieves with **dense vector search only** — it embeds the note
and the query with `nomic-embed-text` and returns nearest-by-cosine. That's excellent
for *meaning* but has a **lexical blind spot**: exact tokens (error codes, identifiers,
API/function names, config keys, rare acronyms) and very short keyword queries can miss,
and the gap widens as the corpus grows. Two orthogonal fixes:

1. **Embedding task prefixes** — use `nomic-embed-text` the way it was trained
   (`search_document:` on notes, `search_query:` on queries). Small, principled, but
   changes the vectors, so it needs a one-time re-embed. *Correctness*, not a big win.
2. **Hybrid lexical + vector search** — add a **SQLite FTS5** (BM25) index beside the
   vector index in the *same* `data/brain.db` and fuse the two rankings with **Reciprocal
   Rank Fusion**. This is the real robustness fix for exact-match and scale.

> **Guard against phantom problems.** This was raised after a Claude Desktop chat
> reported that the query "magic number" failed to retrieve `magic-number.md`. That was
> **hallucinated** — the actual brain ranks it #1 at cosine 0.26. Verify a retrieval
> claim with `search_vault.py` before treating it as real. **Build trigger:** genuine
> recall failures observed on a *populated* brain, not a single anecdote.

---

## 1. Embedding task prefixes (`search_document:` / `search_query:`)

### What it is

`nomic-embed-text` is an **instruction-tuned** embedding model. It expects each input
to be prefixed with a short task descriptor that tells the model *what role* the text
plays:

- `search_document: <note text>` — text you are **storing/indexing** (the notes).
- `search_query: <the query>` — text you are **searching with** (the query).

(The model also defines `classification:` and `clustering:` prefixes for other tasks.)

These prefixes are **not cosmetic**. The model was fine-tuned so that a query embedded
with `search_query:` lands close to the *note that answers it* embedded with
`search_document:`. This is **asymmetric retrieval**: a query ("magic number") and the
note that answers it ("# What is the magic number? …") are different lengths and
phrasings, and the prefixes steer the model into a shared "this query → this document"
space rather than a generic "these two strings look similar" space. Drop the prefixes
and you get the generic mode, which keys more on surface form and is more
phrasing-sensitive.

### Current state

`scripts/embedder.py` sends the raw text to Ollama with **no prefix** —
`{"model": "nomic-embed-text", "prompt": text}` — for both notes and queries.

### The change

Prefix note text with `search_document: ` at embed time (`embed_vault.py` /
`embed_staged.py`) and query text with `search_query: ` at search time
(`search_vault.search()`), inside `embedder.py` so there is one place to keep them
consistent. The `test` backend is untouched.

### Why it's "separate, with a re-embed cost"

Adding a prefix **changes every vector**, so every existing note's `.embed.json`
sidecar must be regenerated — a one-time `embed_vault.py` → `hydrate_cache.py` per real
brain. Two invariants to respect:

- **Same-scheme invariant.** If notes are embedded with `search_document:`, queries
  **must** use `search_query:`. Mixing prefixed and unprefixed vectors makes retrieval
  *worse*. This extends the existing same-model invariant.
- **CI is unaffected.** Fixtures and CI use the deterministic `test` backend (no
  Ollama), so the byte-exact structural diff doesn't change.

Honesty check: measured on the current corpus, prefixes made **near-zero difference**
(`"magic number"` retrieves the target at ~0.13 either way). Do it for correctness and
future-proofing, not as a fix for a demonstrated problem. It is **independent** of
hybrid search — ship them separately.

---

## 2. Hybrid lexical + vector search (SQLite FTS5 + RRF)

### What FTS5 is

**FTS5** is SQLite's built-in full-text search module — a **BM25-ranked inverted
index** over text. It does classic **lexical / keyword** matching: it finds notes that
contain the literal query terms and ranks by term frequency × inverse document
frequency. It is the exact complement of vector search:

| | matches on | strong at | weak at |
|---|---|---|---|
| vector (vec0) | **meaning** | paraphrase, concept, synonyms | exact tokens, rare strings, very short queries |
| FTS5 (BM25) | **literal terms** | identifiers, error codes, exact phrases | paraphrase, synonyms, intent |

FTS5 ships **inside SQLite** (verified available in the brain's build via `sqlite3`/
`apsw`), so it adds **no new dependency**.

### Architecture — a second table in the same one derived cache

Add an FTS5 virtual table **beside** the existing vec0 table in the *same*
`data/brain.db`:

```
data/brain.db
├── notes       (vec0)  source_file, embedding      ← semantic, today
└── notes_fts   (fts5)  source_file, body, tags     ← lexical, new
```

Both are **derived cache**, both rebuilt from the vault by the **same** flow the git
hooks already drive:

- `hydrate_cache.py` (full rebuild) populates **both** tables in its one in-place
  transaction (OQ-5 layer 2 already makes that atomic).
- `update_cache.py --upsert/--delete` maintains **both** tables for a single note.

So: **no new file, no new dependency, and the "one derived cache, safe to rebuild"
model is preserved** — `data/brain.db` stays the single derived artifact, hydrated by
the same sidecar/hook pipeline.

### Query path — fuse in the one shared `search()`

`search_vault.search(query, k)` runs **both** retrievers and merges them:

1. vector KNN over `notes` (as today),
2. BM25 query over `notes_fts`,
3. fuse with **Reciprocal Rank Fusion (RRF)**.

Because the fusion lives in the single shared `search()`, **all three consumers — the
CLI (`search_vault.py`), the skill (`query.py`), and the MCP server — get hybrid search
for free**, with no per-consumer change.

### Why Reciprocal Rank Fusion

The two retrievers produce **incomparable scores**: cosine distance (≈0–2, lower =
better) vs BM25 (unbounded, higher = better). Normalizing them against each other is
fiddly and brittle. RRF sidesteps that by using only each result's **rank** in each
list:

```
score(doc) = Σ_over_lists  1 / (k_rrf + rank_in_list(doc))      # k_rrf ≈ 60
```

A note ranked high in **either** list scores well; a note ranked high in **both** scores
best. RRF is scale-free, parameter-light (one constant), and the standard way to merge
heterogeneous rankers. Return the top-k by fused score.

### Why not the alternatives

- **A separate index file** (the first instinct) forks the "one derived cache" model
  and adds its own sync/rebuild burden. FTS5 in `brain.db` gets the same benefit with
  zero of that — reuse the pipeline that already exists.
- **A manual `keywords:` note section** pushes authoring work onto the user to restate
  words that are **already in the note body** (which FTS5 indexes) and **already in
  `tags:`** (which we fold into the lexical text). Real cost, marginal gain — declined.
  Revisit only if concrete synonym gaps appear.

### Emission / CI impact

- `search_vault.py`, `hydrate_cache.py`, `update_cache.py`, `embedder.py` stay
  **verbatim** emits — byte-diffed, never executed in CI.
- CI's structural diff is unaffected (schema/logic change, deterministic `test`
  backend). The hybrid ranking is behavior best covered by the opt-in semantic /
  MCP behavioral tests (see PLAN → MCP coverage), not the byte-exact gate.

### Sequencing

Independent of the prefix change. Build when a **populated** brain shows real recall
failures. Ship prefixes first if desired (cheaper), or hybrid first — they don't depend
on each other.
