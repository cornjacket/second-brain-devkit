# Hybrid lexical + vector search (FTS5 + RRF) — experiment record

**Date:** 2026-07-12 &middot; **Task:** [#3 — Retrieval quality](../PLAN.md#retrieval-quality-backlog-surfaced-2026-07-04) &middot; **Status:** ✅ COMPLETE (increments 1–3)

**Commits:** [`e30b713`](https://github.com/cornjacket/second-brain-devkit/commit/e30b713) inc 1 &middot; [`ff115e1`](https://github.com/cornjacket/second-brain-devkit/commit/ff115e1) inc 2 &middot; [`ba02994`](https://github.com/cornjacket/second-brain-devkit/commit/ba02994) inc 3

**Living docs (evergreen detail):** [retrieval-quality §2](../docs/retrieval-quality.md) &middot; [benchmark-corpus §6d](../docs/benchmark-corpus.md) &middot; [quality-features §4/§5](../docs/quality-features.md)

> A dated, point-in-time snapshot of what was done and found. The living docs above stay current as
> the design evolves; this file is the immutable record of the 2026-07-12 experiment. Pattern:
> [experiments/README.md](README.md). Brain lesson: `~/second-brain/.../resources/hybrid-search.md`.

## Summary

Dense-vector search retrieves by *meaning*, which gives it a **lexical blind spot**: it blurs exact
tokens (identifiers, error codes, config keys, API names) and can bury the note that literally
contains the query term. Over three increments we built **hybrid** search — a BM25/FTS5 lexical leg
fused with the vector leg via **Reciprocal Rank Fusion** — put it behind a per-brain toggle, and
ablated it on two labeled corpora.

**Headline finding: hybrid is *situational*, not a universal win.** It lifts every metric on a
topically-adjacent (all-IT) corpus — recall@5 to a perfect **1.0** — but *slightly hurts* on
far-apart domains (recall@1 0.90 → 0.83). That asymmetry is precisely why it ships as a
`config/features.toml` toggle (default on) rather than hardcoded: a default-everywhere win would have
quietly degraded the easy, well-separated case.

## Why this feature

A brain retrieved with dense vectors alone is great at paraphrase and concept but weak on *exact
tokens*. The hardened IT query set showed dense burying the right note at rank #2–#6 on lay-phrased,
low-overlap queries. FTS5 (SQLite's built-in BM25) is the exact complement; fusing the two rankings
with RRF is the standard robustness fix. RRF (`score = Σ 1/(K + rank)`, K=60) is scale-free — it uses
only each hit's *rank* in each list, sidestepping the incomparable cosine-vs-BM25 scores. A note
ranked high in *either* list scores; high in *both* scores best.

## The experiment

### Increment 1 — hybrid FTS5 + RRF fusion — `e30b713`

A `notes_fts` FTS5 virtual table now lives beside the vec0 `notes` table in the *same* `data/brain.db`
(built-in, no new dependency, no separate index), hydrated by the **same** flow — `hydrate_cache.py`
rebuilds both in one atomic transaction; `update_cache.py --upsert/--delete` maintains both. FTS text
= canonical body + folded frontmatter tags, read from the vault note at hydrate/upsert time (sidecar
schema unchanged). `search_vault.search()` fuses the vector KNN and the BM25 leg with RRF (K=60) and
returns `(source_file, score)` higher = better, so the CLI, the skill, and the MCP server all get
hybrid for free. The FTS `MATCH` is sanitized (tokenize → quote → OR-join) and degrades gracefully to
vector-only on a stale/absent `notes_fts`.

### Increment 2 — the config surface (per-brain toggle) — `ff115e1`

New `config/features.toml` (`hybrid_search = true`, `rrf_k = 60`) read by new `scripts/features.py`
with `embedder.py`'s precedence — **env > config > default** (`SECOND_BRAIN_HYBRID_SEARCH`,
`SECOND_BRAIN_RRF_K`), so a pre-config brain still searches (hybrid on, K=60). `search_vault.search()`
now runs the vector leg always and appends the lexical leg only when `hybrid_search()` (vector-only
still flows through RRF → same order, comparable score); the hardcoded `K_RRF` constant is gone in
favour of `rrf_k()`. `doctor.py` surfaces the active mode + K. Emitted **verbatim** (default is
identical for golden and brain, unlike `embedder.toml`). This is the deferred **#12 Half-B** config
surface, reopened because `hybrid_search` is the first genuinely *situational* toggle.

### Increment 3 — the ablation / payoff measurement — `ba02994`

`tools/ablation.py` §4 reproduces the shipped `search_vault.search()` path faithfully — the vector leg
plus a BM25 lexical leg over an in-memory `notes_fts` (same body + tags the emitted brain indexes,
built with `note_view.canonical_body`/`frontmatter_tags` and `search_vault`'s own `_fts_match_query`),
RRF-fused (K=60, pool=20) — and measures `hybrid_search` on/off on both corpora.

## Results

**Live spot-check (increments 1–2, real Ollama).** Query `sqlite-vec`: hybrid ranks
`sqlite-vec.md` **#1**; `SECOND_BRAIN_HYBRID_SEARCH=0` reproduces the pre-hybrid blind spot, burying
it at **#2** behind `embeddings.md`.

**Ablation (increment 3, `tools/ablation.py` §4 — RRF K=60, pool=20).**

| corpus | config | recall@1 | recall@5 | MRR | nDCG@5 |
|---|---|---|---|---|---|
| **IT (hardened, adjacent)** | vector-only | 0.675 | 0.975 | 0.797 | 0.838 |
| | **hybrid** | **0.725** | **1.000** | **0.838** | **0.879** |
| **bench (far-apart)** | vector-only | **0.900** | 1.000 | **0.926** | **0.944** |
| | hybrid | 0.833 | 1.000 | 0.906 | 0.930 |

- On the everything-adjacent IT corpus (the realistic case, where dense buries the right note behind
  a near-sibling) hybrid lifts **every** metric — recall@1 +5pp, recall@5 to a perfect **1.0**.
- On the far-apart bench corpus, where dense already ranks the answer #1, the lexical leg adds
  cross-domain term noise RRF can't fully suppress, nudging a couple of easy top-1s down (0.90→0.83).
- **Sanity check:** §4 vector-only reproduces the §1/§2/§3 nomic baseline exactly, confirming the
  reproduced vector leg is faithful.

## Decision

Ship hybrid as a per-brain **`config/features.toml` toggle** (`hybrid_search`, `rrf_k`), **default
on**. It is a net win exactly where a real IT-heavy brain lives and a slight drag only on
cleanly-separable domains — the textbook case for a situational toggle over a hardcoded default.
This also closes the **#12 Half-B** config-surface question: the surface earns its place the moment
the first genuinely optional feature exists.

## Provenance

- **Feature spec:** [PLAN.md → Retrieval quality, #3](../PLAN.md#retrieval-quality-backlog-surfaced-2026-07-04)
- **Commits:** `e30b713` (inc 1), `ff115e1` (inc 2), `ba02994` (inc 3)
- **Living docs:** [retrieval-quality §2](../docs/retrieval-quality.md), [benchmark-corpus §6d](../docs/benchmark-corpus.md), [quality-features §4/§5](../docs/quality-features.md)
- **Brain lesson (abstracted):** `resources/hybrid-search.md`, tag `create_second_brain`
- **Environment:** real Ollama (`nomic-embed-text`); devkit-side, Ollama-gated, out of the hermetic CI gate. CI 8/8 green throughout; nothing emitted into a generated brain.
