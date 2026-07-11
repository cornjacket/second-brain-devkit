# Benchmark corpus (#15) — acceptance results & the `t_max` concept

A durable reference: the measured results of the task #15 acceptance check, plus a
plain-language explanation of `t_max` (the auto-link distance cutoff) and how it is chosen.
Full design of the corpus is in [../../docs/benchmark-corpus.md](../../docs/benchmark-corpus.md).

## Results (real Ollama, `nomic-embed-text`, 2026-07-10 — PASS)

Seeded a fresh Ollama-backed brain with the 200-note benchmark corpus, embedded it, then
measured cohesion (vectors from the sidecars, topic labels from the folders) and retrieval
(the brain's own `search_vault` over `queries.jsonl`).

| metric | benchmark corpus (#15) | IT corpus (#16/#17), for contrast |
|---|---|---|
| topic purity @k=1 | **98%** | 79% |
| topic purity @k=5 | **96%** | 75% |
| separation (inter − intra) | **+0.136** (intra 0.267, inter 0.403) | +0.072 |
| per-domain purity @k=1 | **18–20 / 20** (all 10 domains) | 4–9 / 10 |
| retrieval top-1 (`queries.jsonl`, 30 q) | **27 / 30 (90%)** | — |
| retrieval top-5 | **30 / 30 (100%)** | — |

- Clusters are clean and unambiguous; the performing-arts trio holds (acting 18, dancing 19,
  music-theory 20 out of 20), so the vocabulary-steering worked.
- All three retrieval top-1 misses resolve to a *same-domain sibling* (searing→roasting,
  consensus→eventual-consistency, cadences→tension-and-resolution) — reasonable, not wrong-topic.
- Single-linkage topic-count sweep hits ~11 components at d≈0.26 (≈ the 10 topics) then chains
  to 1 by d≈0.28 — single-linkage's bridge-edge fragility, not a corpus defect. A density
  method (HDBSCAN) would show a wider plateau.
- `autolink.py` writes clean within-cluster `related_auto:` graphs at `t_max ≈ 0.30`.

## Understanding `t_max` (the cutoff for "draw a link")

**Distance = how unrelated two notes are.** Each note is a vector; the distance between two
notes runs roughly 0 (identical meaning) → 1 (unrelated). Split all note-pairs into two buckets:

- **Intra-topic** — two notes in the *same* topic (two cooking notes): averaged **0.267** apart.
- **Inter-topic** — two notes in *different* topics (cooking vs law): averaged **0.403** apart.

Same-topic pairs sit closer than different-topic pairs, and here there is a **gap** between
0.267 and 0.403 with little overlap.

**`t_max` is the distance threshold at which the auto-linker draws a link:** two notes are
linked only when their distance is **below `t_max`**.

> **The circle-of-radius picture (keep this).** Imagine drawing a circle of radius `t_max`
> around each note. Every other note **inside** the circle gets linked; everything **outside**
> does not. A small radius links only the closest, most-related notes; a large radius sweeps
> in distant, unrelated ones. Choosing `t_max` = choosing that radius.

Placing the radius **in the gap** — **`t_max ≈ 0.30`** — works cleanly:

- 0.30 is *above* most same-topic distances (~0.267) → same-topic notes fall inside → **linked**.
- 0.30 is *below* most different-topic distances (~0.403) → cross-topic pairs fall outside → **not linked**.

That is what **"confident `t_max`"** means: the distance distribution has a clear gap
(valley) between "related" and "unrelated," so a cut placed in the valley is trustworthy.
**"The IT corpus had no clean cut"** means its two buckets *overlapped* — no gap — so no single
threshold could separate them, and the honest move there is to skip a global `t_max` and rely
on top-N + mutual-KNN instead. **"The default 0.45 is too loose for this corpus"**: 0.45 is
*larger* than even the average different-topic distance (0.403), so that radius swallows
unrelated notes and links across topics — a hairball. For this corpus ~0.30 is right. (`t_max`
is embedding-config-specific — model + prefix scheme — so it must be re-measured per corpus.)

## Picking `t_max` in a real brain — without labels (the key subtlety)

**The paradox:** if `t_max` depends on the corpus, and you can't know how notes relate without
embedding, then you don't know what's in-topic vs out-of-topic, so how can you pick `t_max`?

**Resolution — two different activities:**

1. **What we did here was *supervised evaluation*.** We authored the corpus, so we had the
   topic labels (the folders) and used them to compute the intra/inter means and *verify* that a
   clean cut exists at ~0.30. This is only possible because it's a test set with a known answer key.

2. **In a real brain you pick `t_max` *unsupervised* — from the shape of the distance
   distribution itself, no labels needed.** When a corpus has real topic structure, the
   note-to-note distances are **bimodal**: a hump of small "related" distances and a hump of
   large "unrelated" distances, with a **valley** between them. That valley *is* `t_max`, and
   how deep/clear it is *is* the confidence. You find it with, e.g.:
   - **largest gap / elbow** in the sorted distances,
   - a **background/null model** (`t_max = mean − k·σ` of all pairwise distances),
   - a **2-component mixture** fit (crossover = `t_max`, overlap = confidence score).

   If the distribution is **unimodal** (no valley — the IT-corpus case), the deriver honestly
   reports **"no confident `t_max`"** and the system falls back to top-N + mutual-KNN. So the
   real gate is *distributional separability, computed from the vectors* — not labels.

**So the labels were used to *check* our unsupervised method lands in the right place, not to
*run* it.** `autolink.py --calibrate` is meant to do the unsupervised derivation on any brain.
Two more escape hatches for a real brain: it *does* have weak labels (PARA folders, tags,
`[[links]]`) you can use as supervision; and you often don't need `t_max` at all — top-N +
mutual-KNN carry the graph, and *retrieval* (ranking the right note for a query) works fine
even when topics are adjacent (the IT corpus still retrieved well). A blurry `t_max` degrades
*graph legibility*, not search.
