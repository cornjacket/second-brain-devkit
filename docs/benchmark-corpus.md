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
