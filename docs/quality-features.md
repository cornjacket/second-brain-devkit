# Quality-enhancement features — the catalog (task #13)

A single inventory of every retrieval / graph **quality feature** a generated brain has or
plans, each with its mechanism, **cost class** (index-time vs query-time), intended **config
toggle**, and **status**. This is the input to the **#12 ablation harness** (which turns these
into toggles and measures each one's contribution against the [#15 benchmark corpus](benchmark-corpus.md))
and the outline for the [#14 tutorial](../PLAN.md). Docs-only; nothing here changes behaviour.

## The two cost classes (why the ablation cares)

Every feature is one of two kinds, and the distinction drives how the ablation runs:

- **Index-time** — changes the *stored vectors*, so flipping it forces a **full re-embed** of
  the corpus (expensive; the harness must matrix/cache these runs). Also bound by the
  **same-model invariant**: notes and queries must be embedded the same way.
- **Query-time** — evaluated per query (or per offline graph pass) and **flips for free**, no
  re-embed. The harness can sweep these cheaply.

## Summary

| Feature | What / why | Class | Toggle (proposed) | Status |
|---|---|---|---|---|
| Canonical substance view | Embed the body, not metadata — breaks the auto-link feedback loop | index-time | `canonical_view` | **built** (#8) |
| Nomic task prefixes | Use the model as trained (`search_document:` / `search_query:`) | index-time | `task_prefixes` | **built** (#3) |
| `content_hash` no-op gate | Skip re-embed of unchanged substance (kills neural-noise churn) | index-time (efficiency) | `content_hash_skip` | **built** (#8) |
| Embedder model / backend | The model decides how far topics land; swap for separation | index-time | `backend` (`config/embedder.toml`) | **built** abstraction; model comparison via #12 |
| Hybrid lexical + vector | FTS5/BM25 + Reciprocal Rank Fusion — exact-token recall | query-time | `hybrid_search` (+ `rrf_k`) | **planned** (#3) |
| Auto-link `related_auto:` | Materialize vector neighbourhoods as Obsidian graph edges | offline pass (free) | `t_max`, `top_n`, `mutual`, `hysteresis` | **in progress** (#8) |
| Vector post-processing | Whitening / isotropy to sharpen closely-related topics | index-time (post) | `whiten` | candidate ([embedding-separation §3](embedding-separation.md)) |
| Chunking + multi-vector | Long notes / PDFs → many vectors per source | index-time | `chunking` | planned (#7) |
| Clustering-purpose embedding | A second embedding (`clustering:` prefix) for the graph only | index-time (analysis) | `graph_embedding` | candidate |
| Note-hygiene line-count guard | Nudge over-long notes at author time | author-time | `max_note_lines` | candidate |

## Feature detail (tutorial-ready)

### 1. Canonical substance view — *built (#8), index-time*
**Mechanism:** `note_view.canonical_body(text)` strips a leading `---`…`---` frontmatter block
and embeds the **body only** (`embed_staged` and `embed_vault` both use it). **Why:** the
embedding is a function of *substance*, not *metadata about* it — so writing machine-derived
`related_auto:` links can't feed back into the vector (the rich-get-richer loop).
**Before/after:** editing a note's frontmatter (adding a tag or an auto-link) *used to* move its
vector; now it doesn't — the vector only tracks the prose.
**Measured (#12 ablation, [benchmark-corpus §6](benchmark-corpus.md)):** on retrieval this is
**flat** (recall@1 0.900 both ways; canonical only a hair tighter, top-1 dist 0.238 vs 0.246) —
its payoff is graph legibility / feedback-loop prevention, *not* retrieval, exactly as intended.

### 2. Nomic task prefixes — *built (#3), index-time*
**Mechanism:** `embed(text, task="document"|"query")` maps to `search_document:` /
`search_query:` in the Ollama backend (the `test` backend ignores it, so fixtures stay
byte-stable). Search is **asymmetric** (query↔note); note↔note linking/clustering is
**symmetric** (`document` on both sides). **Before/after:** on the real brain, `"magic number"`
top-1 distance 0.238 → **0.124** with the #2 hit pushed out to ~0.49 — sharper and better-separated.

### 3. `content_hash` no-op gate — *built (#8), index-time (efficiency)*
**Mechanism:** `note_view.content_hash` (SHA-256 of the canonical body) is stored in each
`.embed.json` sidecar; `write_sidecar` **skips the re-embed** when the stored hash + backend are
unchanged (`force` bypasses it for `doctor --repair`). **Why:** re-embedding unchanged text on a
neural model yields byte-different floats every time — churn. **Before/after:** a frontmatter-only
edit (or an unchanged commit) no longer calls the model or rewrites the sidecar.

### 4. Embedder model / backend — *built abstraction; comparison is #12's job, index-time*
**Mechanism:** `config/embedder.toml` `backend` (`test` / `ollama`), read by `embedder.py`
(env override > config > `test`). The model choice is the biggest lever for pulling
closely-related topics apart ([embedding-separation §2](embedding-separation.md)). **Before/after:**
a stronger or code-aware embedder would separate `rust` vs `golang` notes that a general model
blends — measured on the #15 corpus via the ablation.
**Measured (#12 ablation, [benchmark-corpus §6](benchmark-corpus.md)):** `nomic-embed-text` vs
`mxbai-embed-large` (1024d) is a **wash** on the diverse corpus (recall@1 tie; nomic holds
recall@5 1.000, mxbai edges MRR) — the model lever needs *closely-related* topics to show its
value, so this belongs re-run on the adversarial IT corpus / real brain, not the far-apart #15.

### 5. Hybrid lexical + vector search — *planned (#3), query-time*
**Mechanism:** an **FTS5** (BM25) virtual table in the *same* `data/brain.db`, fused with the
vector ranking via **Reciprocal Rank Fusion** inside `search_vault.search()` — so the CLI, the
skill, and the MCP server all benefit. **Why:** dense vectors have a lexical blind spot (error
codes, identifiers, API/config names, rare acronyms). **Before/after:** a query for an exact
token like `goroutine` or a specific error code, which dense search buries, ranks #1 once BM25
is fused in. Highest-ROI lever for an IT-heavy brain.

### 6. Auto-linking `related_auto:` + stability rules — *in progress (#8), offline pass*
**Mechanism:** `autolink.py` computes each note's KNN over the existing vectors (no re-embed) and
writes a managed `related_auto:` frontmatter block of **quoted wikilinks** Obsidian renders as
graph edges. Stability = `select_links(neighbors, t_max, mutual)`: keep a neighbour only if it is
within **top-N**, closer than **`t_max`**, and **mutual** (reciprocal top-N — kills hub notes).
This is graph quality, **not** retrieval, and it's an on-demand pass (not per-query). **Before/after:**
at `t_max=0.45` a note had 4 neighbours under threshold but mutual-KNN kept only the 1 reciprocal
link — a legible graph instead of a hairball. *Still to do:* hysteresis (`t_hi`/`t_lo`) and the
real-corpus `t_max` calibration (the #15 corpus gave a confident `t_max ≈ 0.30`).

### 7. Vector post-processing (whitening) — *candidate, index-time*
**Mechanism:** apply whitening / PCA / "all-but-the-top" to the stored vectors to counter
anisotropy and spread closely-related notes apart ([embedding-separation §3](embedding-separation.md)).
**Before/after:** two adjacent IT topics whose clusters overlap get measurably more separation
with no model change. Cheap to try; not built.

### 8. Chunking + multi-vector — *planned (#7), index-time*
**Mechanism:** long notes / PDFs are segmented into passages, each embedded, breaking the
one-note-one-vector assumption (cache keyed `(source_file, chunk_id)`). **Before/after:** a query
that matches page 12 of a long PDF returns that passage, not a diluted whole-document vector.

### 9. Clustering-purpose embedding — *candidate, analysis-only*
**Mechanism:** a *second* embedding pass using nomic's `clustering:` prefix, used **only** for the
graph / topic map; search keeps `search_document:`/`search_query:` (same-scheme invariant).
**Before/after:** ~5pp higher topic purity in the graph (seen in #17) without touching retrieval.

### 10. Note-hygiene line-count guard — *candidate, author-time*
**Mechanism:** warn when a note exceeds a line budget, nudging the author to split it (better
one-note-one-vector granularity). Author-time only; no index or query effect.

## Config surface (for #12)

The intended home is a single `config/features.toml` `[features]` block, following
`embedder.py`'s **env-override > config > default** pattern, so the ablation harness can flip each
key. **Index-time** keys (`canonical_view`, `task_prefixes`, `content_hash_skip`, `backend`,
`whiten`, `chunking`, `graph_embedding`) force a re-embed when flipped; **query-time** keys
(`hybrid_search`, `rrf_k`, and the auto-link `t_max`/`top_n`/`mutual`/`hysteresis`) flip for free.
Building that config + the toggles is **task #12**, not this catalog.

**Update (#12 increment 2, 2026-07-11):** the ablation ran the three *built* index-time features
on the #15 corpus ([benchmark-corpus §6](benchmark-corpus.md)) and none is *situational* — the task
prefix and canonical view are always-on wins (the symmetric prefix hurts; canonical view is for the
graph), and the model swap shows no winner on far-apart domains. So shipping a per-brain
`config/features.toml` toggle for them would be **dead config**; it is **deferred** until a
genuinely optional feature exists to toggle — a query-time **`hybrid_search`** on/off (#3) or
**`chunking`** (#7) — which is where the config surface first earns its place.
