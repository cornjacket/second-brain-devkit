# Separating closely-related topics — embedding levers

**Status:** research + roadmap notes (design-only). Surfaced 2026-07-10 from the task #15
acceptance result: a *topically-diverse* corpus separates cleanly (98% purity, a confident
`t_max ≈ 0.30`), while the *everything-adjacent* IT corpus (#16/#17) blends (79% purity, no
clean cut). A real personal brain that is **IT-heavy** will look more like the second case —
so this doc collects the levers for pulling closely-related topics apart, ordered by
practicality, and ties them to existing tasks.

See also: [retrieval-quality.md](retrieval-quality.md) (the retrieval design + the
`clustering:` prefix), [benchmark-corpus.md](benchmark-corpus.md) and
[tests/bench-corpus/RESULTS.md](../tests/bench-corpus/RESULTS.md) (the #15 results + what
`t_max` is), and [auto-linking.md §2.2/§2.3](auto-linking.md) (deriving `t_max`/topic count).

## 0. The honest reframe — you may not need to

Closely-located IT topics mostly hurt the **graph / topic map**, not everyday search:

- **Retrieval doesn't need clean clusters** — it needs the right note ranked #1 for a query,
  which works even when topics are adjacent (the IT corpus still retrieved well).
- **The graph doesn't strictly need a global `t_max`** — top-N + mutual-KNN carry it; `t_max`
  mainly fences off true outliers ([auto-linking.md §2.1](auto-linking.md)).
- **A real brain has weak labels** — PARA folders, tags, `[[links]]` — so you can operate
  *supervised* (the [task #18](test-corpus-clustering.md) reframe) instead of demanding clean
  unsupervised separation.

So treat the levers below as *graph-legibility / topic-analysis* improvements, adopted only
when the map is actually too tangled — not as a prerequisite for a working brain.

## 1. Hybrid lexical + vector search (FTS5 / BM25) — **task #3; highest ROI here**

IT topics differ by **exact tokens** — `goroutine` vs `borrow-checker`, error codes, API and
config names, rare acronyms. Dense vectors *blur* these; a lexical index *nails* them. Fusing
BM25 and vector rankings (Reciprocal Rank Fusion) is the lowest-risk, highest-return lever for
code/IT content specifically, and it is already planned as **task #3** (FTS5 in the same
`data/brain.db`, no new dependency). For an IT-heavy brain this is arguably *the* answer.

## 2. A stronger or code-aware embedding model — biggest dense-side lever

The model is what decides how far apart two topics land. Options:

- **Larger / newer general text models** — bge-large, gte-large, e5-large-v2, mxbai-embed-large,
  nomic-v1.5/v2, Stella, jina-v2/v3 — trained on more and harder data, they separate fine
  distinctions better than the current `nomic-embed-text`.
- **Code-specialized embedders** — models tuned on code / technical Q&A would pull `rust` vs
  `golang` apart better than a general text model, which is exactly the IT-brain failure mode.

**Cost / constraints:** switching the model is an **index-time** change — re-embed the whole
corpus — and the **same-model invariant** holds (query and stored notes must share the model +
prefix scheme, per [nomic-embedding-prefixes](retrieval-quality.md)). So it's a periodic
migration, not a per-query choice.

## 3. Post-processing the vectors — cheap, no model change

Embeddings are usually **anisotropic**: squished into a narrow cone, which compresses distances
and flattens separation. Lightweight transforms applied *after* embedding help:

- **Whitening / PCA / "all-but-the-top"** — remove the few dominant shared directions so the
  vectors spread out and distances mean more. No labels needed; cheap.
- **Supervised metric learning** — with the brain's weak labels (folders/tags), fit an LDA or a
  learned linear projection that *stretches* the space along the directions that distinguish
  your topics.

These reshape the existing vectors rather than re-embedding, so they're inexpensive to try.

## 4. Fine-tune / contrastive-adapt on your own corpus — heavy, last resort

Train (or LoRA-adapt) the embedder to pull *your* topics apart using **hard negatives** — e.g.
a rust note and a golang note as a "should be far apart" pair. Directly targets "my IT topics
blur," but it is real ML work (data prep, training, evaluation) and re-embeds everything.

## 5. A separate clustering-purpose embedding — two embeddings, two jobs

nomic's `clustering:` prefix added ~5pp purity in #17 ([retrieval-quality.md → the clustering
prefix](retrieval-quality.md)). You could run a **separate** embedding pass with it purely for
the graph / topic map, while search keeps `search_document:`/`search_query:` for retrieval
(the same-scheme invariant means the brain can't adopt it for search). More storage + a second
index, but it buys sharper clusters without touching retrieval.

## 6. Multiple embedders — compare, then choose (not per-query auto-switch)

Sensible, and half-built: `embedder.py` already abstracts the backend, so plugging in
alternative embedders is architecturally easy. Comparing them *objectively on your corpus* is
**exactly the [#12/#13 ablation](benchmark-corpus.md)** methodology — labeled queries →
score each embedder → pick the winner. Caveats:

- **Not per-query.** Switching embedders means re-embedding (index-time) and honoring the
  same-model invariant, so you can't choose per query. The realistic pattern is a **periodic
  evaluate-and-pick**, run as an ablation, with a human choosing from the numbers.
- **Auto-selection** would need a metric to optimize and a held-out labeled set — feasible as an
  offline routine, but it selects a model *for the whole corpus*, not per query.

## 7. Dimensionality — not a free lever

You **cannot** gain separation by padding the current model's 768 dims — no new information is
added. It is model *quality*, not dimension *count*, that separates topics. A better model
sometimes *also* has more native dims (1024 / 1536 / 3072) or Matryoshka (variable-length)
embeddings, but the **training** does the work, not the number. So: pick a better model (§2);
don't inflate dims.

## 8. This is an active AI research area

The underlying problem — making fine-grained, closely-related items separable in embedding
space — is a live field: **contrastive representation learning**, **hard-negative mining**
(literally "make near-duplicates separable"), embedding **anisotropy / isotropy** fixes,
**metric learning**, and **domain-adapted retrievers**. Worth tracking as the model landscape
moves fast; §2 and §4 are where new research lands first.

## 9. Recommended order for an IT-heavy brain

1. **Ship hybrid FTS5 (§1 / task #3)** — biggest, safest win for exact IT terms.
2. **Evaluate a stronger / code-aware embedder (§2) via the #12/#13 ablation** — now that the
   benchmark corpus + labeled query set + method exist, this is real-numbers driven.
3. **Try whitening (§3)** if the *graph* is still too tangled — cheap, no re-embed.
4. **Fine-tuning (§4)** only if the above are not enough.

## 10. Where it sits

Cross-cuts the retrieval roadmap: **#3** (hybrid FTS5) delivers §1; **#13/#12** (feature
catalog + ablation harness) is the vehicle for §6 and for measuring §2/§3; the corpus that
makes all of it measurable is **#15**. No new task is strictly required yet — these levers
attach to #3 and #12/#13 — but if separation becomes a felt problem on the real brain, §2
(embedder swap) and §3 (whitening) are the first concrete experiments to schedule.
