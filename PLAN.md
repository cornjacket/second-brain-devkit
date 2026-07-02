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

## Milestone G1 — Generator core (after the brain works)  ← IN PROGRESS
The brain (`../second-brain-test`) is complete through M2 + Task 0004, so G1 is
unblocked. Strategy + manifest are done; **next: rework the golden (prototype-first),
then templatize.**
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
- [~] **Golden rework (prototype-first, in `../second-brain-test`)** before
      templatizing ([OQ-4](open-questions.md#oq-4)):
  - [x] Relocate `SPEC.md`'s design internals into the devkit as the canonical
        `product-spec.md` (pulls [G4](#milestone-g4--lifecycle) forward); remove
        `SPEC.md` from the golden; scrub its `SPEC.md §X` pointers from the emitted
        files. Golden `self_test` green; devkit refs repointed. (devkit `dab1163`,
        golden `f675fe3`.)
  - [ ] **Expand `README.md`** into the brain's operational doc (record / query /
        setup) — the one doc a brain user (human or AI) needs. Include a
        **provenance back-reference to the devkit** (origin + canonical spec home).
        *Deferred — next, collaborative.* (Golden README is still framed as the
        golden reference; only its dangling `SPEC.md` links were fixed so far.)
- [ ] Templatize the reworked golden into a devkit-tracked template tree — this is
      where the `cleaned` files are scrubbed of `ai-project-status` (`CLAUDE.md`/
      `GEMINI.md` dev-block, `register.py` comment). Run
      `tools/check_no_forbidden_refs.py` over it → zero hits.
- [ ] Scaffold a brain repo from the template: PARA dirs, scripts, hook, config,
      the operational `README.md`, cleaned `CLAUDE.md` + `GEMINI.md` symlink.
- [ ] Sidecar policy ([OQ-3](open-questions.md#oq-3)): gitignore live-vault
      sidecars; emit committed `tests/fixtures/vault/` (`test` backend) + a `type`
      field pinned to `test`
- [ ] Emit `scripts/self_test.py` (structural self-test) into every generated brain

## Milestone G2 — Validation harness
Two complementary tiers (see [OQ-2](open-questions.md#oq-2)):
- **Structural tier** — the acceptance oracle. `test` embedder, byte-exact diff.
  - [ ] `sandbox/scratch/` wipe-and-regenerate runner (never test stale state)
  - [ ] Diff generated output vs the golden (`../second-brain-test`) → clean diff = acceptance test
  - [ ] Confirm determinism (the `test` embedder) makes the diff stable
  - [~] Forbidden-reference guard ([SPEC §5.3](SPEC.md)) — `tools/check_no_forbidden_refs.py`
        greps the generated tree against a denylist (`ai-project-status`) and
        fails on any hit. **Script written & verified against the golden;** wire
        it into the wipe-and-regenerate runner once generation emits a tree.
- **Semantic tier** — opt-in, local, real `ollama` embedder. Asserts *behavior*,
  not bytes (never byte-diff a neural model — brittle even same-machine).
  - [ ] Retrieval-quality check: known queries put expected notes in top-k / above a cosine threshold
  - [ ] Exercises the real production path (Ollama call, dims, L2-normalize) that `test` never touches
  - [ ] Gated on Ollama being available; not part of the portable/CI acceptance gate

## Milestone G3 — Production generation (Mode B)
The durable product path ([SPEC §5.1](SPEC.md)): generate a real, persistent brain
the end user owns — distinct from the throwaway `sandbox/scratch/` of G2.
- [ ] Generate to a **user-chosen path** (not `sandbox/`) — same generator core as G1/G2
- [ ] Refuse to overwrite a non-empty target unless explicitly forced (protect user data)
- [ ] Bootstrap the generated repo as its **own** git repo: `git init`,
      `core.hooksPath`, first commit — history starts at generation, owned by the user
- [ ] **Never** nest the generated repo inside the devkit's git (OQ-1 antipattern)
- [ ] Assert Mode A ≡ Mode B: the scaffold a user gets is byte-identical to what the
      harness diffs against the golden (so production is trusted without re-diffing)
- [ ] Document the end-user "generate your brain" flow (README / a `generate` entry point)

## Milestone G4 — Lifecycle
- [ ] Promote the canonical product spec into the devkit (`SPEC.md` §4 lifecycle).
      **Pulled forward by [OQ-4](open-questions.md#oq-4):** since brains don't ship
      `SPEC.md`, the design internals need their canonical devkit home during the
      G1 golden rework — not after mothballing.
- [ ] Mothball `second-brain-test` once generation + harness are trustworthy
- [ ] Resolve OQ-1 long-term (golden storage → Option A, tracked files in devkit) — `open-questions.md`
