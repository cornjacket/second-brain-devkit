# Open Questions

Unresolved design decisions for the Second Brain Developer Kit. Each item should
be resolved before the affected feature is finalized, then moved to (or
referenced from) SPEC.md as a decided convention.

---

## OQ-1: How should the golden reference repo be stored inside the devkit?

**Status:** RESOLVED → **Option A** (2026-07-02). The golden is vendored into the
devkit at `tests/golden/` (`tools/vendor_golden.py`) and the whole harness reads it
there, so the devkit is self-contained and CI needs no external repo. See
[Final decision](#final-decision-option-a).

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

### Final decision (Option A)

**2026-07-02: adopt Option A** — a devkit-tracked `golden/` snapshot — driven by
the requirement that **the devkit be self-sustaining for CI** (CI checks out only
this repo and never reaches the external golden). The harness (G1/G2) has landed,
so the "revisit when" trigger is met.

- The golden's *expected output* (tracked files: notes, committed `test`-backend
  fixture sidecars, hook source, scripts) is vendored into `tests/golden/` as plain
  tracked files — no live `.git`. `tools/vendor_golden.py` refreshes it from the
  live `../second-brain-test/` by hand (a dev-machine step; CI never runs it).
- **The "exercise the pre-commit hook" requirement is met elsewhere.** Firing the
  hook needs a live `.git`, which `golden/` deliberately lacks — but Mode-B
  generation (`tools/create_second_brain.py`) already `git init`s a brain and fires the hook
  on a note commit for real. So the vendored golden needs no history at rest; it
  is purely the diff baseline. This retires the original conflict between "tracked"
  and "fires the hook" — the two requirements are now satisfied by two different
  artifacts (static `golden/` for the diff; a generated Mode-B repo for the hook).
- The live `../second-brain-test/` becomes a hand-prototyping surface only; its
  mothball (PLAN G4) is now unblocked.

Tracked as the **CI milestone** in [PLAN.md](PLAN.md); this OQ closes when the
vendored `tests/golden/` + repointed harness land.

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

---

## OQ-5: How do we make cache access concurrency-safe (reader vs. rebuild)?

**Status:** OPEN — direction agreed (three layers), sequenced behind the MCP
server. Surfaced 2026-07-03 while building `doctor.py`.

### Context

Multiple processes can touch `data/brain.db` at once: **readers**
(`search_vault.py`, and soon the long-lived **MCP server**, [G6](PLAN.md)) and
**writers** (`update_cache.py` / the post-commit hook, `hydrate_cache.py`, and
`doctor.py --repair`, which calls hydrate). Today's CLI reality makes collisions
rare (a `search_vault` process lives milliseconds), but the MCP server — a
persistent process holding a connection open while post-commit rebuilds fire —
turns this from theoretical into real.

### What SQLite gives us intrinsically (so we don't hand-roll a mutex)

- **ACID transactions** — a reader never sees a half-written transaction. The
  incremental `update_cache.py` DELETE+INSERT-per-row already rides on this and is
  safe against concurrent readers *today*.
- **File-level locking** — serializes access; returns `SQLITE_BUSY` on contention.
- **WAL mode** (`PRAGMA journal_mode=WAL`) — many readers + one writer run
  concurrently; readers don't block the writer or vice-versa.

### Where SQLite does NOT help — the actual exposure

`hydrate_cache.py` does `DB_PATH.unlink()` then rebuilds — a **filesystem delete
of the whole DB file**, not a SQL transaction. **No SQLite lock covers
`os.unlink()`.** A reader opening between the unlink and the rebuild sees a
missing/half-populated DB. This is the same failure class the incremental
`update_cache` fixed for single-note edits — but the bulk path still tears down.
`doctor.py --repair` inherits it (repair calls hydrate).

### Decision (direction) — three layers, in priority order

1. **Turn on two PRAGMAs in `db.connect()`** (cheap, one place, both `sqlite3` and
   `apsw`): `journal_mode=WAL` (reader/writer concurrency) + `busy_timeout=<few s>`
   (the default is **0** — contention errors immediately instead of waiting; this
   is why naive concurrent SQLite feels flaky). **Highest value-per-line; do first.**
2. **Rebuild hydrate *in place*** — `DELETE FROM notes` inside one transaction (or
   temp-table swap) instead of `unlink()`+recreate, so SQLite's transaction
   isolation fully covers the rebuild (readers see old rows until commit, then new,
   atomically). Kills the one operation locking can't protect; aligns with the
   non-teardown direction `update_cache` already set. `doctor --repair` benefits
   directly. (A cruder `build tmp + os.replace()` is atomic for *new* readers but
   leaves long-lived connections — the MCP server — pinned to the old inode until
   they reconnect; in-place DELETE is better for that reason.)
3. **App-level writer lock (`flock` on `data/.brain.lock`) — only if needed.**
   SQLite serializes *statements*, not multi-statement cross-connection critical
   sections like "re-embed all sidecars **and** rebuild the cache as one exclusive
   op." A `flock` around the whole repair/hydrate section serializes **writers**
   against each other while WAL handles reader-vs-writer. Add when the MCP server
   makes overlapping writes realistic — not before.

### Sequencing

Layer 1 **landed** (golden `0520c0f`) as a cheap general robustness win. **Layers 2
and 3 are scoped to the MCP server ([G6](PLAN.md))** — the long-lived reader is what
makes the `hydrate` teardown a real hazard, so both are built alongside the server,
not before it. `doctor --repair` inherits layer 2's benefit when it lands.

**Revisit when:** the MCP server is designed — re-evaluate whether layer 3 is
needed and whether WAL's `-wal`/`-shm` sidecars need any `.gitignore` handling.
Tracked in [PLAN.md G5](PLAN.md#milestone-g5--runtime-setup-ollama--embedder).

---

## OQ-6: MCP server — build-time decisions

**Status:** RESOLVED → **server v1 built** (2026-07-04, golden `4867eec`). Scope was
decided at design time (`stdio` + Claude Desktop only; claude.ai web out of scope;
read-only; thin wrapper over the brain's own `embedder`/`db`/`search_vault`; MCP SDK
an isolated optional dependency; [OQ-5](#oq-5) layer 2 lands with it). The build-time
sub-decisions are now settled:

1. **MCP Python SDK / version — DECIDED: the official `mcp` package, `mcp>=1.2`**
   (FastMCP lives in the SDK from 1.2 on). Needs Python ≥3.10, so it pins cleanly on
   the 3.11+ floor. Kept in an **isolated** `requirements-mcp.txt` — never in base
   `requirements.txt`, so core plumbing + CI stay stdlib + `sqlite-vec` + `apsw`.
2. **`get_note` in v1 — DECIDED: yes.** Small, avoids a second round-trip after a
   search hit, and path-validated to resolve **inside** `vault/` (arbitrary reads
   refused). Both tools are read-only.
3. **One server per brain — DECIDED: per-brain.** Root resolved relative to the
   server file (`parents[1]`, like `query.py`), so it works through any install
   symlink with no hardcoded path. A user with several brains registers one stanza
   each.
4. **Registration — DECIDED (v1): print-and-instruct.** The README documents the
   `claude_desktop_config.json` stanza (absolute path, restart). Auto-inserting it
   via `install_skill.py` (opt-in, marker-guarded, `--uninstall`-able, `--apply`-gated)
   is **deferred to a follow-up** — not needed to prove the server works.
5. **claude.ai web — CONFIRMED out of scope.** A browser can't reach a local `stdio`
   server and a remote one would break local-first; a hosted variant would be a
   separate track with its own security model. Documented as a limitation, not papered
   over.

**Outcome:** live-verified against a real stdio MCP client (initialize + list_tools +
`search_second_brain` returning absolute paths + `get_note` + out-of-vault read
refused; hydrate-on-start keeps the JSON-RPC handshake clean). CI green (45 emitted).
Layer 3 (`flock` writer lock) remains reactive under [OQ-5](#oq-5).
