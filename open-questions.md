# Open Questions

Unresolved design decisions for the Second Brain Developer Kit. Each item should
be resolved before the affected feature is finalized, then moved to (or
referenced from) SPEC.md as a decided convention.

---

## OQ-1: How should the golden reference repo be stored inside the devkit?

**Status:** DECIDED (interim) — see [Decision](#decision).

### Context

`second-brain-test/` is intended to be a **golden reference** — the hand-built,
known-good output of a feature — used to validate that the devkit's code
generation produces the correct result. To prevent drift, the golden reference
should live inside `second-brain-devkit/` and be version-controlled alongside the
generator code that produces it.

The complication: the feature under test relies on a **generated git repo with a
pre-commit hook** (the hook produces `*.embed.json` sidecar vectors on commit).
So the golden reference must be able to behave as a real git repo when exercised.

### The conflict

These two requirements pull in opposite directions:

1. **Stay in sync / be tracked by devkit** → the golden's files must be tracked
   by the devkit's own git.
2. **Exercise the pre-commit hook** → the golden must be (or become) a real git
   repo with a live `.git`.

A literal "repo inside a repo" (a live nested `.git`) does **not** satisfy (1):
git will not track the contents of a nested repository from the parent — it
records at most a bare submodule pointer, or ignores the directory. The result
is that the nested golden would **drift**, which defeats the entire purpose.

### Options under consideration

- **A — Plain tracked files (no live `.git`).** Store the golden's working tree
  as normal tracked files; keep the hook as a regular file (e.g.
  `golden/.githooks/pre-commit`). The test harness runs `git init` on a copy at
  test time to fire the hook. Avoids the antipattern; golden is truly tracked by
  devkit and stays in sync. The stored golden contains the *expected output*
  (notes + sidecars + hook source), which needs no committed git history to
  exist at rest.

- **B — Git submodule.** Golden remains its own real repo; devkit tracks a
  commit pointer. Preserves a literal nested repo, but adds submodule ceremony
  and "sync" means bumping pointers on every change.

- **C — Nested live `.git`.** Literal repo-inside-a-repo. Matches the mental
  model but devkit will NOT track the golden's contents, so it WILL drift.
  (Listed for completeness; appears to defeat the stated goal.)

### Decision

**Interim (2026-06-29): Option B — standalone sibling repo.**

For now the golden lives at `../second-brain-test/` as its own real git repo
with its own GitHub remote (`cornjacket/second-brain-test`). It has a live
`.git`, so the pre-commit hook fires for real when notes are committed — which
is exactly what we want while hand-building and proving the pipeline.

This was chosen to **make progress now** rather than to settle the long-term
storage question. The accepted trade-off: the devkit does **not** track the
golden's contents, so the two can drift and must be kept in sync by hand.

**Revisit when:** drift becomes painful, or we wire up the automated
wipe-and-regenerate harness (`sandbox/scratch/` diff against golden). At that
point Option A (plain tracked files inside the devkit, `git init` a copy at test
time) becomes the likely target, since it makes the golden a non-drifting,
version-tracked baseline. The pipeline is being built embedder-agnostic and
path-agnostic specifically so this move stays cheap.

---

## OQ-2: How do we validate with the real (semantic) embedder, not just `test`?

**Status:** DECIDED (direction) — two tiers; see [Decision](#decision-1).

### Context

The G2 acceptance test regenerates a brain and **byte-diffs** it against the
golden. That diff uses the deterministic `test` embedder (pure SHA-256 math), so
the committed sidecars are **byte-identical on any machine**. Reasonable question:
the real embedder (`nomic-embed-text` via Ollama) is also deterministic on the
same machine — why not use it for the acceptance diff?

### The conflict

- **Same-machine deterministic ≠ reproducible everywhere.** Real neural
  embeddings drift in low-order float bits across CPU/GPU, BLAS, Ollama/model
  versions, and quantization. The golden's sidecars are **committed frozen bytes**;
  a byte-diff must reproduce them on CI and every contributor's machine, which a
  real model cannot guarantee. Any Ollama/model upgrade would also force a full
  re-baseline.
- **Dependency.** The acceptance gate must run anywhere with no Ollama server or
  model pull. `test` is stdlib-only.
- **But** the byte-diff proves *structure*, never *retrieval quality*, and never
  exercises the real Ollama path.

### Decision

**Two complementary tiers (do NOT extend the byte-diff to real embeddings):**

1. **Structural tier — the acceptance oracle.** `test` embedder, byte-exact diff
   vs golden. Portable, dependency-free, runs in CI. This is the generator
   correctness gate. (G2 as originally written.)
2. **Semantic tier — opt-in, local.** Real `ollama` embedder. Asserts **behavior,
   not bytes** — e.g. a known query ranks the expected note in top-k, or cosine ≥
   a threshold. Deliberately avoids float-exact assertions (brittle by nature even
   same-machine). This checks the one thing `test` can't (relevance) and exercises
   the real production path (Ollama call, dimension check, L2-normalize).

**Revisit when:** we formalize the semantic tier's assertions (exact top-k /
threshold values) and decide whether it runs in a nightly/local job vs. purely
on-demand. Tracked as a G2 sub-item in `PLAN.md`.

---

## OQ-3: What sidecars/vectors does a generated brain commit?

**Status:** DECIDED — see [Decision](#decision-2). Mirrors the golden
(`second-brain-test`, Task 0004).

### Context

The brain's embed pipeline writes a per-note `.embed.json` **sidecar**. Original
design committed them ("the expected output"). But (a) real semantic vectors are
machine/model-dependent (float drift across CPU/GPU/BLAS/model versions), bloaty,
and always regenerable, and (b) querying needs the model anyway (same-model
invariant), so committing them only adds churn. Meanwhile the generator needs a
**byte-stable** artifact to diff against — which only the deterministic `test`
backend provides.

### Decision

A generated brain (like the golden, Task 0004) must emit:

1. **`vault/` sidecars git-ignored** — semantic vectors are *derived*; regenerated
   locally, never committed. The generator does **not** emit committed vault
   vectors.
2. **`tests/fixtures/vault/` sidecars committed** — a tiny fixed note set embedded
   with the `test` backend; the *only* committed sidecars. These anchor both the
   brain's self-test and the devkit's G2 structural byte-diff.
3. **`scripts/self_test.py`** — ships in every generated brain; re-embeds the
   fixtures with `test` and byte-compares to the committed sidecars, so a user can
   confirm their pipeline is wired correctly on their machine with no model.
4. **Sidecar `type` field** (`test` | `ollama:<model>`) so a mixed index is
   detectable; the golden is pinned to `test`.

### Implications for the generator (G1) and harness (G2)

- G1 templates must gitignore vault sidecars and emit the fixture vault + self-test.
- G2's structural diff compares the generated scaffold + fixtures against the
  golden — both byte-stable because fixtures use `test`. The semantic tier
  (OQ-2) stays opt-in/local.

**Revisit when:** we decide whether generated brains also ship the semantic-tier
E2E harness, or only the structural self-test.
