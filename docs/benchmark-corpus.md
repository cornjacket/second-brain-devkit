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

## 5. Acceptance check (real Ollama — remaining step)

Seed a real (Ollama-backed) brain with `--corpus bench`, then verify:

1. **Cluster plateau** — the single-linkage / union-find sweep (auto-linking §2.3) shows a
   **clear plateau at ~10 topics** — the separability the IT corpus lacks.
2. **Confident global `t_max`** — `autolink.py --calibrate` reports a real distance gap /
   high separation score, vs the IT corpus's no-clean-cut.
3. **Retrieval** — each `queries.jsonl` query ranks its `expected` note in top-k under
   threshold (an `check_semantic_retrieval`-style pass over the eval set).
4. **The performing-arts trio** — confirm acting / dancing / music-theory land as three
   distinct clusters despite adjacency.
5. **Auto-link `--apply`** — on the seeded brain, `autolink.py --apply` draws an
   illuminating graph (distinct clusters, sparse cross-topic edges) — the first meaningful
   run of the deferred #8 write path.

This measurement is opt-in / local (needs Ollama) and out of the hermetic CI gate, like the
other semantic checks. Results get recorded back here when run.
