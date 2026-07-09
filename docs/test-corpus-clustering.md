# Test-corpus clustering analysis (task #16)

**Status:** analysis / decision-pending. Measures how well the task #16 seed corpus
(`tests/seed-corpus/`, 100 notes across 10 IT topics) forms topic clusters under real
embeddings, and enumerates the levers to improve separation. Follow-ups: **task #17**
(regenerate with longer, topic-anchored notes) and **task #18** (review + decide the
separation strategy).

## What was measured (2026-07-09 · nomic-embed-text via Ollama · `search_document:` prefix)

Embedded all 100 notes' canonical bodies, then measured topic cohesion — do notes group by
their topic folder?

- **Topic purity @k=1: 69%** — a note's single nearest neighbour is same-topic 69% of the
  time (random ≈ 10% across 10 topics; perfect ≈ 100%). So ~1 in 3 notes' closest match is in
  a *different* topic.
- **Topic purity @k=5: 55%** — over the 5 nearest, 55% are same-topic.
- **Mean intra-topic distance 0.329 < mean inter-topic 0.382** (separation **+0.053**). Cosine
  distance: 0 = identical meaning, ~1 = unrelated. Same-topic notes are closer than cross-topic
  ones — real clustering — but both sit in the 0.3s, i.e. *everything is IT-adjacent*.

Per-topic nearest-neighbour same-topic rate (@k=1):

| topic | @k=1 |
|---|---|
| ci-testing | 9/10 |
| git-automation | 9/10 |
| knowledge-management | 9/10 |
| web-architecture | 8/10 |
| typescript | 7/10 |
| ai-llm | 6/10 |
| ai-agent-harness | 6/10 |
| sqlite | 6/10 |
| golang | 5/10 |
| rust | 4/10 |

## Interpretation

Real but **moderate** structure. Strongly-distinct topics (CI, git, knowledge-management, web)
cohere well. The weak ones blend for **semantically correct** reasons:

- **rust ↔ golang** — adjacent systems languages sharing concepts (memory, concurrency, types,
  error handling).
- **ai-llm ↔ ai-agent-harness** — both about AI/LLMs (two adjacent AI topics, by design).

The blending is the model correctly seeing these topics are close in meaning — not a defect.
Contributing factors: the notes are **short** (2–4 sentences), so a few salient words dominate
and can bridge topics (e.g. "ownership/memory" ↔ "caching/storage"); and 10 notes/topic is a
sparse cluster.

**Why loose clustering is a useful test condition.** The auto-linker (#8) draws links from
vector distance. A trivially-separable corpus (cooking vs physics vs history) would let any
algorithm ace it and prove nothing. A corpus where everything is "somewhat related" — like a
real second-brain — forces the machinery to earn its keep: the `t_max` cutoff must separate
"related enough" from "merely adjacent", and mutual-KNN must suppress hubs. So this corpus is a
good stress test as-is.

## Levers to improve separation (strongest first)

1. **Longer, more topic-anchored notes** — rewrite each note 2–3× longer, packed with
   topic-specific vocabulary (Rust: cargo / borrow-checker / trait; Go: goroutine / channel /
   defer) and avoiding generic cross-topic words that bridge topics. Highest-leverage change
   that keeps the notes realistic. **→ task #17.**
2. **Use nomic's `clustering:` prefix for topic analysis** — distinct from the
   `search_document:` / `search_query:` retrieval prefixes; optimised for grouping. Re-run the
   cohesion check with it (keep `search_document:` for the brain itself). Cheap, no corpus change.
3. **More notes per topic** — 20–30 instead of 10 densifies clusters, so @k=1 purity rises
   mechanically. More authoring cost.
4. **Merge / replace adjacent topics** — collapse rust+golang or the two AI topics, or swap in a
   more distant domain. Biggest purity jump, but partly *games the metric* and drops chosen topics.
5. **A stronger embedding model** — separates fine distinctions better; a heavyweight change to
   the whole brain's embedder, not a corpus tweak.

## Reframe — you may not need higher purity

If the corpus is for the **benchmark** (#12/#13), the topic folders are **ground-truth labels**,
so you can measure how well the auto-linker/threshold recovers the *known* topics regardless of
embedding tightness. Crisp embedding clusters only matter for the *unsupervised* topic-count
analysis (§2.3 of [auto-linking.md](auto-linking.md)) rediscovering the topics on its own. For
supervised evaluation, the labels suffice.

## Recommendation

Do lever #1 (longer, topic-anchored notes) + #2 (`clustering:` prefix for the analysis) — both
preserve the chosen topics and realism. Reach for #4 only if a cleanly-separable benchmark is
specifically needed.
