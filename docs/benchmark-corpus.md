# Benchmark corpus (task #15) — the topically-diverse dataset

**Status:** authored 2026-07-10 (200 notes + 30-query eval set + tooling). The real-Ollama
**acceptance measurement** (cluster plateau + `t_max`) is the remaining step — see §5.

The benchmark corpus is the **complement** to the #16/#17 IT seed-corpus. Per the
[task #18 decision](test-corpus-clustering.md), the IT corpus is deliberately
*everything-adjacent* (the supervised + adversarial stress test); this corpus is
deliberately **far-apart domains** so the embedding space forms clean, separable
clusters — the *unsupervised* topic-count / `t_max`-plateau case, and the first corpus on
which auto-link `--apply` (task #8) is actually illuminating.

Devkit-side and **never emitted** into a generated brain (like #16); invisible to CI (the
partition check only walks `tests/golden/`).

## 1. Layout

```
tests/bench-corpus/
  <domain>/bench_<domain>_<desc>.md    # 10 domains × 20 notes = 200
  queries.jsonl                        # 30 labeled queries (ground-truth for retrieval)
```

Each note mirrors the #16 convention: frontmatter `tags: [bench, <domain>]`, an H1 title,
and **one dense ~120–160-word paragraph** packed with the domain's own vocabulary and
steered off cross-topic terms (the #17 lesson), so distances mean something.

## 2. The 10 domains

Deliberately mutually distant: **cooking, personal-finance, distributed-systems, history,
biology, music-theory, astronomy, acting, law, dancing**. Acting and dancing are framed as
*how to teach the art* (pedagogy). The topic folder is the note's **ground-truth label**.

**Adjacency to watch:** music-theory / acting / dancing are performing-arts-adjacent. They
are steered apart by vocabulary — dancing on the body (turnout, barre, spotting, weight),
acting on craft (objectives, beats, subtext, status), music-theory on notation/harmony
(scales, chords, cadences). A standing **authoring rule** keeps music-theory terms
(`metronome`, `staccato`, `legato`, `downbeat`, `phrase`) out of the dancing notes — a
dancing note describes the *physical reaction* to music instead. That trio is the group to
verify in §5.

## 3. The labeled query set (`queries.jsonl`)

One JSON object per line, mapping a distinctly-phrased query to the note(s) that should be
retrieved — the retrieval ground truth #12 consumes:

```json
{"query": "how do I keep a mayonnaise from splitting", "domain": "cooking", "expected": ["bench_cooking_emulsions.md"]}
```

30 queries, ~3 per domain, each phrased differently from its target note's title so the
match tests semantics, not lexical overlap. The topic **folders** give the supervised
topic labels; the **query set** gives per-query retrieval relevance.

## 4. Installing it into a brain

Devkit tool (`tools/test_corpus.py`), corpus-driven:

```
python3 tools/test_corpus.py install <brain> --corpus bench   # copy 200 notes → vault/resources/, commit
python3 tools/test_corpus.py remove  <brain> --corpus bench   # remove notes + sidecars + cache rows
```

Or born pre-seeded: `create_second_brain <path> --seed-bench-corpus`. Needs a working
embedder (real Ollama, or `SECOND_BRAIN_EMBEDDER=test`). The `bench_` prefix is independent
of the seed corpus's `seed_`, so the two never collide.

## 5. Acceptance results (real Ollama, 2026-07-10 — PASS)

Seeded a fresh Ollama-backed brain (`create_second_brain --seed-bench-corpus`,
`nomic-embed-text`, 200 notes embedded), then measured cohesion (vectors read from the
sidecars, domain labels from the topic folders) and retrieval (the brain's own
`search_vault`). Opt-in / local (needs Ollama), out of the hermetic CI gate.

| metric | benchmark corpus (#15) | IT corpus (#16/#17), for contrast |
|---|---|---|
| topic purity @k=1 | **98%** | 79% |
| topic purity @k=5 | **96%** | 75% |
| separation (inter − intra) | **+0.136** (intra 0.267, inter 0.403) | +0.072 |
| per-domain purity @k=1 | **18–20 / 20** (all 10 domains) | 4–9 / 10 |

1. **Clusters are clean and unambiguous.** Every domain scores 18–20/20 nearest-neighbour
   purity. **The performing-arts trio holds** — acting 18/20, dancing 19/20, music-theory
   20/20 — so the vocabulary-steering (and the "physical reaction, not music-theory terms"
   rule) worked.
2. **Confident `t_max`.** Intra-cluster distances (mean 0.267) sit well below inter-cluster
   (0.403) — a real gap the IT corpus lacked — so a global **`t_max ≈ 0.30`** cleanly
   separates within-topic from cross-topic. (Note: the shipped default `t_max=0.45` is too
   loose *for this corpus* and would link across topics; ~0.30 is right here. The distance
   scale is embedding-config-specific, as auto-linking §2.2 warns.)
3. **Topic count.** A single-linkage / union-find sweep passes through ~11 components at
   d≈0.26 (≈ the 10 intended topics), then chains to 1 by d≈0.28 — single-linkage's known
   bridge-edge fragility, *not* a corpus defect (the purity metrics confirm the 10 clusters).
   A density method (HDBSCAN) would show a wider plateau; recorded as a limitation of the
   stdlib-first sweep.
4. **Retrieval (`queries.jsonl`, 30 queries): top-1 27/30 (90%), top-5 30/30 (100%).** All
   three top-1 misses resolve to a *same-domain sibling* (searing→roasting,
   consensus→eventual-consistency, cadences→tension-and-resolution) — reasonable, not
   wrong-topic.
5. **Auto-link `--apply`.** At `t_max≈0.30–0.32` with mutual-KNN, `autolink.py` writes clean
   **within-cluster** `related_auto:` graphs (189/200 notes linked; e.g. a finance note links
   only to other finance notes), with the occasional *legitimate* cross-edge (acting↔dance
   *improvisation*). This is the illuminating graph the homogeneous corpora couldn't produce —
   the first meaningful exercise of the deferred #8 write path.

**Verdict: PASS.** The corpus separates cleanly, yields a confident `t_max`, and retrieves
its labeled queries — ready for the #12/#13 ablation work and the auto-link calibration.

## 6. Ablation results (task #12, increment 2 — real Ollama, 2026-07-11)

`tools/ablation.py` runs this corpus + `queries.jsonl` through real embeddings and reports IR
metrics per feature configuration. Increment 1 covered the **query-time** task prefix; increment 2
adds the two **index-time** ablations (each re-embeds the notes).

**§1 — nomic task prefix (query-time; notes stored `search_document:`)**

| query config | recall@1 | recall@5 | MRR | nDCG@5 | top-1 dist | margin |
|---|---|---|---|---|---|---|
| `search_query:` (correct asymmetric) | 0.900 | **1.000** | 0.926 | 0.944 | **0.238** | 0.067 |
| no prefix | 0.900 | 1.000 | 0.939 | 0.954 | 0.263 | 0.067 |
| `search_document:` (symmetric) | **0.867** | 0.967 | 0.907 | 0.917 | 0.237 | 0.055 |

The **symmetric** scheme measurably hurts (recall@1 0.867); the correct asymmetric prefix and
no-prefix tie on recall@1, with the prefix giving **tighter distances** (0.238 vs 0.263). On a
cleanly-separable corpus prefixes pay in *separation*, not raw recall — matching the real-brain
finding.

**§2 — canonical substance view (index-time; nomic, correct prefixes)**

| body config | recall@1 | recall@5 | MRR | nDCG@5 | top-1 dist | margin |
|---|---|---|---|---|---|---|
| canonical ON (body only) | 0.900 | 1.000 | 0.926 | 0.944 | 0.238 | 0.067 |
| canonical OFF (full text) | 0.900 | 1.000 | 0.924 | 0.942 | 0.246 | 0.066 |

**Retrieval-flat** (Δ negligible; canonical is a hair tighter). This is the expected null result:
these notes carry only `tags:` in frontmatter, so stripping it barely moves the vector. Canonical
view earns its keep in **graph legibility** (breaking the auto-link feedback loop, §1 of
[quality-features](quality-features.md)), **not** retrieval.

**§3 — embedder model swap (index-time; canonical body, each model's native scheme)**

| model | recall@1 | recall@5 | MRR | nDCG@5 | top-1 dist | margin |
|---|---|---|---|---|---|---|
| `nomic-embed-text` (768d) | 0.900 | **1.000** | 0.926 | 0.944 | 0.238 | 0.067 |
| `mxbai-embed-large` (1024d) | 0.900 | 0.967 | **0.939** | 0.942 | 0.257 | **0.089** |

A **wash** on far-apart domains: tie on recall@1, nomic holds recall@5=perfect, mxbai edges MRR + a
wider margin. The heavier 1024-dim model does **not** clearly separate better here — because this
corpus is deliberately *far-apart* domains, the model lever (which matters for *closely-related*
topics) has nothing to pull apart. *(But see the IT-corpus re-run below — the picture reverses.)*
(recall/MRR/nDCG are rank-based → comparable across models; top-1 dist / margin are model-relative
and not.)

## 6b. The adversarial IT corpus (task #22, `--corpus it` — real Ollama, 2026-07-11)

The §6 read was limited by the corpus: #15's far-apart domains **saturate** the metrics (recall@5 ≈
1.0), leaving no headroom to differentiate features. So §1–§3 were re-run on the **everything-adjacent
IT corpus** (#16/#17, `tests/seed-corpus/` — 100 notes, 10 blurry topics incl. rust↔golang and the two
AI topics) via a labeled `tests/seed-corpus/queries.jsonl` and the `ablation.py --corpus it` flag.
*(This first pass used a 30-query concept-named set; the shipped set is now the harder 40-query v2
below — §6c.)* Here a lever has something to pull apart, and the baseline is non-degenerate.

| ablation (IT corpus) | config | recall@1 | recall@5 | MRR | nDCG@5 |
|---|---|---|---|---|---|
| §1 prefix | correct `search_query:` | 0.833 | 1.000 | 0.901 | 0.926 |
| §1 prefix | symmetric `search_document:` | **0.800** | 0.967 | 0.878 | 0.896 |
| §2 canonical | ON (body only) | 0.833 | **1.000** | **0.901** | **0.926** |
| §2 canonical | OFF (full text) | 0.833 | 0.967 | 0.894 | 0.909 |
| §3 model | `nomic-embed-text` (768d) | 0.833 | 1.000 | 0.901 | 0.926 |
| §3 model | **`mxbai-embed-large`** (1024d) | **0.967** | 1.000 | **0.983** | **0.988** |

On this **original** (concept-named) query set, mxbai beat nomic recall@1 0.833 → 0.967 — which
looked like "the model swap is the big separation lever." **That conclusion did not survive
hardening (§6c) — treat it as provisional.**

## 6c. Hardened query set + the phrasing-dependence correction (task #22 follow-up, 2026-07-11)

The original IT set still left recall@5 at 1.0 and recall@1 at 0.833 — not much headroom. Two
rewrites of the 40-query set (now 4/topic) probed how *robust* the §6b model result was, and the
answer is sobering:

| query set (same 100-note IT corpus) | style | nomic recall@1 | mxbai recall@1 | "winner" |
|---|---|---|---|---|
| original | concept-named paraphrase | 0.833 | **0.967** | mxbai +13pp |
| v1 hardening | hyper-detailed, note's own vocab | **0.975** | 0.900 | nomic +7pp |
| **v2 hardening (shipped)** | plain-language symptom/goal, low overlap | **0.675** | **0.675** | **tie** |

**The embedder ranking flips with query phrasing.** v1 backfired — packing each query with the target
note's signature vocabulary made it a *fingerprint* of one note, raising the ceiling to 0.975 and
handing the win to nomic. v2 (the shipped set) uses lay symptom phrasing with minimal signature
tokens, which finally creates headroom (**recall@1 0.675**, recall@5 still 0.975 — the answer stays
retrievable, the difficulty is now ranking it *first*). At that honest difficulty nomic and mxbai
**tie** (0.675 = 0.675; nomic edges recall@5/MRR).

**Correction to §6b:** mxbai's "decisive win" **did not replicate** under either rewrite (nomic won
one, tie the other). So the nomic-vs-mxbai delta is **within the variance introduced by query
phrasing** at this corpus/scale — *not* a robust embedder win. Robustly ranking embedders would need
a larger/held-out labeled set than is worth hand-authoring here (or the real brain at scale). The
findings that **are** stable across all three sets: the **symmetric prefix consistently hurts**, and
**canonical view is consistently ~flat** on retrieval.

**The shipped v2 set is a genuinely hard, honest bed.** Per-query diagnosis: 12 of the 13 rank-1
misses keep the expected note in top-5, and they cluster exactly on the *designed* adjacencies — the
knowledge-management / git / sqlite intra-clusters and the deliberate golang↔rust cross-topic bleeds
(`slices→borrowing`, `result-error→defer`) — i.e. hard-but-fair, not mislabeled.

**Decision (gates task-#12 Half B).** Unchanged: none of the three *built* index-time features is a
*situational* per-brain toggle — the prefix and canonical view are always-on wins, and the model
choice is a `config/embedder.toml` decision (and not even a robust one here), not an on/off toggle a
user flips per query. So a `config/features.toml` for them stays **dead config**, deferred until a
genuinely optional feature exists (#3 hybrid FTS5 on/off, #7 chunking). The hardened set is now the
reusable bed for #3, where these lay/exact-token queries are exactly dense search's blind spot.
