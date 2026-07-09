# Test-corpus clustering analysis (task #16)

**Status:** task #17 applied (lever #1 + #2). Measures how well the task #16 seed corpus
(`tests/seed-corpus/`, 100 notes across 10 IT topics) forms topic clusters under real
embeddings, and enumerates the levers to improve separation. The **post-#17 re-measurement**
is in [§ After task #17](#after-task-17--longer-topic-anchored-notes-2026-07-09). Remaining
follow-up: **task #18** (review + decide whether the separation is enough for the #12/#13
benchmark, or lean on the ground-truth topic labels).

## Baseline — task #16 corpus (2026-07-09 · nomic-embed-text via Ollama · `search_document:` prefix)

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

## After task #17 — longer, topic-anchored notes (2026-07-09)

Applied **lever #1**: rewrote all 100 note bodies ~3× longer (45 → 148 words avg), each packed
with topic-specific vocabulary and steered away from generic cross-topic words; the two adjacent
pairs (rust↔golang, ai-llm↔ai-agent-harness) got explicit "stay in your own jargon" guidance.
Only the bodies changed — same 10 topics, same filenames, same frontmatter/titles. Re-measured
with the same cohesion check.

| metric | baseline (#16) | after #17 (`search_document:`) | after #17 (`clustering:` — lever #2) |
|---|---|---|---|
| topic purity @k=1 | 69% | **79%** | **84%** |
| topic purity @k=5 | 55% | **75%** | **77%** |
| mean intra-topic distance | 0.329 | 0.276 | 0.255 |
| mean inter-topic distance | 0.382 | 0.348 | 0.341 |
| separation (inter − intra) | +0.053 | **+0.072** | **+0.086** |

The clusters tightened across the board — the biggest jump is purity **@k=5** (55% → 75–77%),
i.e. a note's whole neighbourhood is now mostly same-topic, not just its single nearest match.
The two adjacent AI topics rose from 6/10 to 8–9/10 and rust from 4/10 to 8–9/10.

**Lever #2 (nomic's `clustering:` prefix) helps the analysis, not the brain.** Re-embedding the
same notes with the `clustering:` prefix instead of `search_document:` adds ~5pp of purity — it is
tuned for grouping. Use it only for *this cohesion analysis*; the brain itself keeps
`search_document:`/`search_query:` for retrieval (the same-prefix invariant). What the prefix is,
why it helps grouping, and why the brain must never adopt it is written up in
[retrieval-quality.md §1 → The `clustering:` prefix](retrieval-quality.md#the-clustering-prefix--a-measurement-lens-never-the-brain).

**Residual — the golang laggard (5/10, unchanged) is concept-name collision, not weak jargon.**
Its misses land on the *same subtopic in a sibling language/topic*, which is semantically correct:
`generics`→`typescript_generics`, `interfaces`→`typescript_interfaces`, `error-handling`→
`rust_result-error`, `context`→`ai-llm_context-window`. Notes that share a concept name across
topics will co-locate no matter how much language-specific vocabulary they carry — pushing harder
would only make them unrealistic. This is a floor set by the topic design, and the [reframe](#reframe--you-may-not-need-higher-purity)
(ground-truth labels) absorbs it.

## Levers to improve separation (strongest first)

1. **Longer, more topic-anchored notes** — rewrite each note 2–3× longer, packed with
   topic-specific vocabulary (Rust: cargo / borrow-checker / trait; Go: goroutine / channel /
   defer) and avoiding generic cross-topic words that bridge topics. Highest-leverage change
   that keeps the notes realistic. **→ task #17.**
2. **Use nomic's `clustering:` prefix for topic analysis** — distinct from the
   `search_document:` / `search_query:` retrieval prefixes; optimised for grouping. Re-run the
   cohesion check with it (keep `search_document:` for the brain itself). Cheap, no corpus change.
   Details: [retrieval-quality.md §1 → The `clustering:` prefix](retrieval-quality.md#the-clustering-prefix--a-measurement-lens-never-the-brain).
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

Levers #1 (longer, topic-anchored notes) + #2 (`clustering:` prefix for the analysis) were
applied in **task #17** — see [§ After task #17](#after-task-17--longer-topic-anchored-notes-2026-07-09).
Purity@1 rose 69% → 79% (84% under `clustering:`) and the neighbourhood purity@5 55% → 75–77%,
with both levers preserving the chosen topics and realism. The residual blend is concept-name
collision across sibling topics (see above), a floor set by topic design, not a note-quality
problem. For **task #18**: this is likely good enough for a *supervised* benchmark (the topic
folders are ground-truth labels — the [reframe](#reframe--you-may-not-need-higher-purity)); reach
for lever #4 (merge/replace adjacent topics) only if a cleanly-separable *unsupervised* benchmark
is specifically needed.
