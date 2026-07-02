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

---

## OQ-4: Does a generated brain ship the product design spec (`SPEC.md`)?

**Status:** DECIDED (direction) — **no.** The devkit owns the design internals; the
brain ships an operational `README.md`. See [Decision](#decision-3).

### Context

The golden's `SPEC.md` is the product spec — sidecar schema, embedding contract,
cache DDL, search/`register` behavior. The emit manifest first classified it
`cleaned` (emit it after scrubbing `ai-project-status`). But `SPEC.md` is
*design-internal*: the definition of *how the pipeline is built*, not what a
brain's user (human or AI) needs to *operate* the brain. It is also deeply
cross-referenced — ~11 "see `SPEC.md §X`" pointers across the scripts, hook, and
memory — and was authored to build the reference implementation.

### The conflict

- **A brain must be self-documenting for its user** (human writing notes, AI
  querying) → that audience needs *operational* guidance (record / query / setup),
  which belongs in `README.md`.
- **Design internals have one true home.** Schema / DDL / embedding contract are
  *defined* in the devkit (the generator + system home, and the eventual canonical
  owner — [SPEC §4](SPEC.md) lifecycle). Shipping the full internal spec into every
  brain duplicates the definition, invites drift, and leaves cross-repo/dependency
  references inside a product that should stand alone.

### Decision

1. **`SPEC.md` is NOT emitted into a generated brain.** The golden **keeps** its
   `SPEC.md` as the build-time design reference (it is `exclude`d from emission,
   like `PLAN.md`/`tasks/`); canonical ownership moves into the **devkit** only at
   mothball (lifecycle §4). A brain never ships it.
2. **The brain's `README.md` carries everything the user (human or AI) needs to
   operate it** — record / query / setup — with **no** design internals and **no**
   dependency references.
3. **Emitted files are scrubbed of `SPEC.md §X` pointers** (they would dangle in a
   brain with no `SPEC.md`) and of any cross-repo reference (e.g. `tests/README.md`
   → "devkit `OQ-2`").
4. If a spec-like doc is ever shipped, it must first be stripped of dependency
   references and design internals — but the default is that it is not shipped.
5. **The brain's `README.md` carries a provenance back-reference to the devkit**
   (the repo that generated it, and the eventual home of the design internals).
   This is *not* a runtime dependency — the brain stands alone — but a documented
   path for the brain's local AI (or a curious user) to reach the internals if
   ever needed. It resolves the "where did the design spec go?" gap left by (1)
   without duplicating the spec into the brain. It is exempt from the forbidden-
   reference rule (which targets `ai-project-status`, unrelated meta-tooling); the
   devkit *is* the brain's legitimate origin, not a foreign dependency.

### Implications (G1 build + golden rework, prototype-first)

**Landed (golden `f675fe3`, `e934dcb`, `9ed9356`):**

- The `SPEC.md §X` pointers were scrubbed from the golden's **emitted** files
  (scripts, hook, `.gitattributes`, `tests/README.md`), so they stay plain
  `verbatim` copies and a brain (which has no `SPEC.md`) is coherent without them.
  Golden `self_test` stays green.
- `SPEC.md` itself **stays in the golden** as its build-time design reference and
  is `exclude`d from emission. An earlier commit (`f675fe3`) removed it — and
  briefly promoted it into the devkit as `product-spec.md` (`dab1163`) — but that
  conflated "don't ship it into a brain" with "don't keep it in the golden"; the
  golden is still the active prototype repo and needs the spec locally, so it was
  restored (`e934dcb`) and the premature promotion reverted.
- The remaining `cleaned` files differ from the golden only because the golden is
  a live `ai-project-status`-tracked dev repo — that scrub happens when the golden
  is templatized, not in the golden.
- The lifecycle §4 "promote the product spec into the devkit" step stays where it
  was — at mothball, not now (see PLAN G4).

- `README.md` was **rewritten** as the brain's operational guide (golden
  `9ed9356`). The golden keeps a "golden reference → local `SPEC.md`" top note;
  the emitted variant swaps it for the devkit provenance back-reference at
  templatize time. This was the last golden-rework item — only templatizing
  remains before scaffolding.

**Revisit when:** the README rework lands and we see whether any residual design
detail genuinely needs to live *inside* a brain.
