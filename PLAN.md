# Second Brain Devkit — Build Plan

The durable milestone tracker for **this repo** (the generator + system home).

Distinct from:
- `daily-plan.md` — single-day, forward-looking, `ai-project-status`-managed.
- `SPEC.md` — the spec (what the system *is*), not a progress tracker.

Status: `[x]` done & committed · `[~]` in progress · `[ ]` not started

> **Sequencing — read first.** Do **not** start the generator milestones (G1+)
> until the brain (`../second-brain-test/`) is working and committed. The brain is
> built prototype-first; this devkit then *productizes* it. Use the brain's
> `PLAN.md` + git history as the spec for what to generate. Working all repos at
> once is intentionally avoided.

## Milestone 0 — System docs ✅
- [x] `SPEC.md` — system & generator spec (three-repo workflow, roles, knowledge flow, lifecycle, validation loop, non-goals)
- [x] `CLAUDE.md` — trimmed to devkit scope; product detail moved to the product docs; pointers added
- [x] `README.md` — authoritative-specs callout; removed the duplicated sidecar schema
- [x] `open-questions.md` — OQ-1 decided (interim: golden = standalone sibling repo)

## Milestone G1 — Generator core (after the brain works)  ✅
The brain (`../second-brain-test`) is complete through M2 + Task 0004, so G1 was
unblocked. **Done:** strategy → manifest → golden rework → templatize → `generate()`
+ Mode-A runner. A generated brain is emitted from the tracked `template/` tree and
the seed-vault post-step, and validated by the Mode-A harness (guard + self-test +
structural diff, all green). **Next: G2's semantic tier and/or G3 (Mode B).**
The generator is a **pure function** `generate(target, params)` that writes a
brain scaffold into `target` — the shared core both generation modes call
([SPEC §5.1](SPEC.md); validation = Mode A, production = Mode B).
- [x] Choose template strategy — DECIDED (2026-07-01): **copy a tracked template
      tree** (no engine); the template is a *curated, cleaned subset* of the
      golden ([SPEC §5.2](SPEC.md)). No parameterization exists yet, so a copy
      suffices; revisit if a real per-brain variable appears.
- [x] Author the emit **manifest** — `emit-manifest.toml`: every golden file
      classified into `verbatim`/`cleaned`/`generated`/`exclude` (24/4/5/8).
      Source of truth for "what a brain contains" (G1) + the G2 diff's include
      list. `tools/check_manifest_partition.py` proves it partitions the golden's
      41 tracked files exactly (no missing/extra/dup) — verified passing.
- [x] **Golden rework (prototype-first, in `../second-brain-test`)** before
      templatizing ([OQ-4](open-questions.md#oq-4)):
  - [x] `SPEC.md` is `exclude`d from emission but **kept in the golden** as its
        build-time design reference (promotion to the devkit stays at
        [G4](#milestone-g4--lifecycle)/mothball, not now). Scrubbed its `SPEC.md §X`
        pointers from the golden's *emitted* files (scripts, hook, `.gitattributes`,
        `tests/README.md`) so a brain is coherent without it. Golden `self_test`
        green. (golden `f675fe3` + `e934dcb`.)
  - [x] **Rewrote `README.md`** as the brain's operational guide (Setup → Everyday
        use → Layout → How it works → Registering). The golden keeps its
        "golden reference" top note → local `SPEC.md`; the emitted variant swaps
        that for a **provenance back-reference to the devkit** at templatize time.
        (golden `9ed9356`.)
- [x] Templatize the reworked golden into the devkit-tracked `template/` tree —
      `tools/build_template.py` copies the 24 `verbatim` files byte-for-byte and
      transforms the 4 `cleaned` ones (strip the `ai-project-status` block +
      North-star + golden-isms from `CLAUDE.md`; drop `register.py`'s
      ai-project-status note; swap `README.md`'s top note for the devkit provenance
      line; `GEMINI.md` → `CLAUDE.md` symlink). Fail-loud anchors; runs the
      forbidden-ref guard (zero hits) and the 24 verbatim files are byte-identical
      to the golden. 28 files emitted.
- [x] Scaffold: `generate(target, params)` (`tools/generate.py`) — copies
      `template/` → target (symlinks + modes preserved) then runs the seed-vault
      post-step (the emitted `scripts/seed_vault.py`, `seeds/** → vault/**`). No
      embed step: the `test` fixtures ship pre-embedded in the template and
      live-vault sidecars are git-ignored/not emitted (OQ-3). Emits exactly the
      manifest's 33-file set (28 emitted + 5 `vault/**`); the 5 vault files are
      byte-identical to the golden. Refuses a non-empty target unless `force`
      (protects Mode-B user data, G3). The Mode-A runner (`tools/run_sandbox.py`)
      wipe-and-regenerates `sandbox/scratch/` every run, then gates on the
      forbidden-ref guard + the brain's own `self_test.py` + the structural diff —
      all green.
- [x] Sidecar policy ([OQ-3](open-questions.md#oq-3)): gitignore live-vault
      sidecars; emit committed `tests/fixtures/vault/` (`test` backend) + a `type`
      field pinned to `test`. Carried into the template (verbatim `.gitignore` +
      committed fixtures) and verified end-to-end: the generated brain's
      `self_test.py` reproduces the fixtures byte-for-byte and the G2 diff confirms
      no live sidecar is emitted.
- [x] Emit `scripts/self_test.py` (structural self-test) into every generated brain
      — ships verbatim in the template; runs green *inside* the generated scaffold
      as Mode-A gate 2/3.

## Milestone G2 — Validation harness
Two complementary tiers (see [OQ-2](open-questions.md#oq-2)):
- **Structural tier** — the acceptance oracle. `test` embedder, byte-exact diff.
  - [x] `sandbox/scratch/` wipe-and-regenerate runner (never test stale state) —
        `tools/run_sandbox.py` (Mode A). Gates on the forbidden-ref guard +
        the in-scaffold `self_test.py` + the structural diff (3/3), all green.
  - [x] Diff generated output vs the golden (`../second-brain-test`) → clean diff =
        acceptance test. `tools/check_structural_diff.py` — manifest-driven: the
        generated tree must be **exactly** the emitted set, byte-for-byte
        (`verbatim` + `vault/**` vs the golden, `cleaned` vs their `template/`
        variant since the golden holds the *un*cleaned original), with no stray
        files. 33/33 match. Negative-tested: catches DIFF / MISSING / SYMLINK-DIFF
        / EXTRA and exits non-zero. Wired as Mode-A gate 3/3.
  - [x] Confirm determinism (the `test` embedder) makes the diff stable — the diff
        is byte-exact and repeatable: the vault notes are plain copies and the only
        committed vectors are `test`-backend fixtures (no neural float drift, OQ-3).
        Two consecutive wipe-and-regenerate runs produce an identical clean diff.
  - [x] Forbidden-reference guard ([SPEC §5.3](SPEC.md)) — `tools/check_no_forbidden_refs.py`
        greps the generated tree against a denylist (`ai-project-status`) and
        fails on any hit. Now wired into `tools/run_sandbox.py` as gate 1/3 over
        the freshly-generated `sandbox/scratch/` tree — green.
- **Semantic tier** — opt-in, local, real `ollama` embedder. Asserts *behavior*,
  not bytes (never byte-diff a neural model — brittle even same-machine).
  - [ ] Retrieval-quality check: known queries put expected notes in top-k / above a cosine threshold
  - [ ] Exercises the real production path (Ollama call, dims, L2-normalize) that `test` never touches
  - [ ] Gated on Ollama being available; not part of the portable/CI acceptance gate

## Milestone G3 — Production generation (Mode B)  ✅
The durable product path ([SPEC §5.1](SPEC.md)): generate a real, persistent brain
the end user owns — distinct from the throwaway `sandbox/scratch/` of G2.
`tools/new_brain.py` is the end-user entry point (`python3 tools/new_brain.py ~/my-brain`).
- [x] Generate to a **user-chosen path** (not `sandbox/`) — calls the same
      `generate()` core as Mode A, so nothing about the output is mode-specific.
- [x] Refuse to overwrite a non-empty target unless `--force` — `generate()`'s
      guard fires before any git work; verified it declines and leaves no dir.
- [x] Bootstrap the generated repo as its **own** git repo: `git init` +
      `core.hooksPath .githooks` + first commit. History starts at generation,
      owned by the user. First commit is `--no-verify` so it never depends on a
      working embedder (fixtures ship pre-embedded; live vault sidecars are
      git-ignored); the wired hook then embeds the user's *subsequent* note commits
      — verified end-to-end (a note commit fires the hook, writes a gitignored
      sidecar, commits only the note).
- [x] **Never** nest the generated repo inside the devkit's git (OQ-1 antipattern)
      — refuses if the target's location is already under any git repo (checks the
      parent's toplevel); verified it rejects a path inside the devkit and creates
      no dir. The brain's own toplevel == itself, not the devkit.
- [x] Assert Mode A ≡ Mode B — the Mode-B tree passes the *same*
      `check_structural_diff.py` oracle (33/33 vs the golden), because both modes
      call the identical `generate()` core. So production is trusted without
      re-diffing.
- [x] Document the end-user "generate your brain" flow — `README.md` "Generate a
      brain" section + `new_brain.py`'s own `--help`/docstring.

## Milestone G4 — Lifecycle
- [ ] Promote the canonical product spec into the devkit (`SPEC.md` §4 lifecycle).
      The golden keeps its `SPEC.md` as the build-time reference until then
      ([OQ-4](open-questions.md#oq-4)); this promotion happens at mothball, when the
      golden's `SPEC.md` is removed and the devkit becomes its sole home.
- [ ] Mothball `second-brain-test` once generation + harness are trustworthy
- [ ] Resolve OQ-1 long-term (golden storage → Option A, tracked files in devkit) — `open-questions.md`
