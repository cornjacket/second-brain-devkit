# Tag hygiene — hygiene as a vault deliverable (task #32)

**Status:** **Stages 1–4 + 6 DONE 2026-07-16** (golden `3431858`) — the deterministic
detector, the backfill applier, both CLIs, and the write-time near-miss warning, with 12
fixture tests. Prototyped in the golden (`../second-brain-test`); **not yet emitted** — the
emission wiring (Stage 5) and the read-only MCP tool (Stage 7) are **deferred** (see §7).
**Scope:** frontmatter `tags:` only, in the PARA roots — the exact surface `list_tags`
enumerates. Never bodies, wikilinks, titles, the glossary, or the note template.

---

## 1. Motivation

Tag drift is a *runtime* property of a living vault, not a one-off cleanup. Near-misses
(`agents` vs `ai-agents`) silently split a group; a broad tag riding nearly every note (an
`ai` tag in an all-AI vault) partitions nothing; a title leaks into the tags
(`create_second_brain`). Left alone the tag vocabulary decays as a retrieval surface. This
task makes hygiene something *every emitted brain carries*, not a manual pass against one
vault. (It grows out of the same enumeration insight as `list_tags` — see
[docs/mcp-server.md](mcp-server.md) — and the "unfindable is not nonexistent" lesson: a
vocabulary you cannot see the shape of is one you cannot keep clean.)

## 2. The load-bearing idea — a deterministic sandwich

**Detection is deterministic; only policy needs a human.** Almost everything is string
statistics over the tag vocabulary, not LLM work — routing it through a model would make it
non-reproducible. The one genuine judgment is thin and in the middle (which near-miss form
is canonical; whether two overlapping-but-distinct tags merge). So the pipeline sandwiches
that judgment between two mechanical layers:

```
detector (read-only)  ->  human picks a {old: new} mapping  ->  applier (backfill)
```

## 3. What shipped (in the golden)

All in `../second-brain-test/scripts/` + `tests/`:

- **`tag_hygiene.py`** — the shared library, both mechanical layers:
  - **Detector** (`analyze`, read-only):
    - *near-miss* — `normalize` (case, `-`/`_`/space) then flag case/separator variants,
      typos (edit distance ≤ 1), and **affix-qualified** forms (`agents` → `ai-agents`).
    - *discrimination* — per-tag note frequency: flag the **near-universal** (≥ 0.8 of
      notes; partitions almost nothing) and **singletons** (one note; often a leaked title).
      The IDF intuition from BM25, applied to tags.
    - *overlap* — Jaccard co-occurrence over note sets; pairs above threshold are merge
      *candidates*, not decisions.
    - *format-lint* — an underscore in an otherwise kebab vocabulary reads as a leaked
      identifier.
  - **Applier** (`rewrite_tags` / `apply_mapping`, mutating) — rewrites frontmatter `tags:`
    only from an explicit mapping, preserves everything else, dedupes on a merge, idempotent,
    dry-run by default.
  - **`near_miss_of`** — the write-time hook, the *same rule* the detector uses.
- **`tag_lint.py`** — read-only CLI; prints the report (`--json` too). Always exits 0
  (informational posture) so it is safe to wire into pre-commit/CI without blocking.
- **`tag_apply.py`** — applier CLI; a mapping file (`old -> new` lines or a JSON object),
  `--dry-run` by default, `--apply` writes the edits and `git add`s **only** the edited
  notes (never commits — the human reviews the staged diff).
- **`mcp_server.py`** — write-time near-miss **warning** (non-blocking) folded into
  `add_note` (proposed tags vs the existing vocabulary) and `add_glossary_term` (see §5).
- **`tests/test_tag_hygiene.py`** — 12 tests; a fixture vault with a planted split, a
  near-universal tag, and a leaked-title singleton asserts **exactly** those flags and **no
  false positives**, plus applier correctness / idempotency / dry-run / merge-dedupe and the
  near-miss rule.

## 4. Execution surface (decided, with the reason)

The MCP server has **no tool to edit an existing note's frontmatter** (`add_note` refuses to
overwrite), so remediation is structurally impossible through the Desktop tool surface.
Therefore:

| Phase | Surface | Why |
|---|---|---|
| Detection | script (`tag_lint.py`), Claude Code, wireable into pre-commit/CI | pure algorithm, no LLM |
| Policy decision | either surface (read the report, choose a mapping) | the one judgment step |
| Application (backfill) | Claude Code only (`tag_apply.py`) | mechanical edits across many files + git |
| Awareness (deferred) | read-only `lint_tags` MCP tool → Desktop | same detector, second entry point (§7) |

## 5. Decisions made while building (beyond the spec)

- **`add_glossary_term` warns on term/alias, not tags.** The glossary has no `tags:` — it
  writes `aliases:` and already *refuses* exact collisions. So the near-miss layer there is a
  non-blocking warning when a proposed **term/alias** is close to an existing glossary term
  (`ablations` when `ablation` exists) — the controlled-vocabulary analogue of a tag split,
  reusing the existing `_near_misses` helper. Same intent as the spec ("stop drift at the
  source"), correct mechanism for that vocabulary.
- **Near-universal tags are excluded from the near-miss pass.** The affix rule that catches
  `agents` → `ai-agents` also matches a broad umbrella tag against every compound under it
  (`ai` → `ai-agents`), which is *not* a split. A near-universal tag already has its own,
  louder finding, so it is dropped from near-miss candidacy — in both the lint pass and the
  write-time warning, so they stay consistent. (The spec's own example — a universal `ai` tag
  *and* an `agents`/`ai-agents` split — only yields "exactly three findings" because of this.)
- **Overlap has a support floor (`min_support = 2`).** Jaccard over single-note sets is
  coincidence, not signal — two tags sharing one note score 100%. Requiring the combined note
  set to reach the floor suppresses that noise on a small vault (this is why the real 4-note
  seed vault reports clean overlap).
- **The near-miss rule is a single implementation.** `mcp_server` imports `tag_hygiene`, so
  the write-time warning and the lint finding cannot drift — the same class of "one rule, one
  home" guard the note-gate (#9) and the term-scaffold sharing already use.

## 6. Defaults (all overridable)

- Near-universal: a tag on ≥ **0.8** of notes.
- Singleton: a tag on exactly **1** note.
- Overlap: Jaccard ≥ **0.6**, once the combined note set is ≥ **2**.
- Near-miss: normalized case/separator collision, edit distance ≤ **1**, or one extra
  leading/trailing kebab token.
- Canonical-choice policy (for the human's mapping): higher note-count wins, tie-break the
  shorter form — advisory; `tag_apply.py` applies exactly the mapping it is given.
- `tag_apply.py`: dry-run unless `--apply`; nothing commits without human sign-off.

## 7. Deferred

- **Stage 5 — emission wiring.** Emit the detector, applier, and both CLIs into every brain:
  add the four `scripts/*.py` to `emit-manifest.toml [verbatim]`, re-run `vendor_golden.py`
  + `build_template.py`, and add an **informational** CI gate (`tools/check_tag_lint.py` +
  a `STEPS` entry in `tools/ci.py`) that runs the lint on the emitted seed corpus. The test
  fixtures stay emission-excluded (dev artifacts — they are built in a tempdir at run time,
  so there is nothing to exclude). Chosen posture: **informational, never fails** (drift is
  visible, not fatal). See [SPEC §5.2](../SPEC.md) and
  [emit-manifest.toml](../emit-manifest.toml).
- **Stage 7 — read-only `lint_tags` MCP tool.** Expose the detector as a read-only MCP tool
  so Desktop sees vault health during normal note-taking (`analyze` already returns a
  JSON-able `Report`). **Hold until a brain is large enough to feel drift** — at ~12 notes /
  25 tags this is speculative surface. Same lesson as the `ai`-tag decision: do not build
  against a distribution you do not have yet.

## 8. Honest scoping caveat

This vault is ~12 notes / 25 tags — too small to *need* full tooling. The justification is
not this vault today; it is that the devkit ships to brains that grow, and **write-time
prevention earns its place even now** by stopping the next split before it happens.
