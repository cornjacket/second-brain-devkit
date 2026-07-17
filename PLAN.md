# Second Brain Devkit — Build Plan

The durable milestone tracker for **this repo** (the generator + system home).

Distinct from:
- `daily-plan.md` — single-day, forward-looking, `ai-project-status`-managed.
- `SPEC.md` — the spec (what the system *is*), not a progress tracker.

Status: `[x]` done & committed · `[~]` in progress · `[ ]` not started

## ▶ Next up (2026-07-13)
- **Done 2026-07-16 — #32, tag hygiene as a vault deliverable (Stages 1–6, emitted).** Deterministic
  tooling for tag drift in a living vault: a detector (near-miss / discrimination / overlap /
  format-lint), a backfill applier (dry-run default, idempotent), `tag_lint.py` + `tag_apply.py`
  CLIs, and a **non-blocking** near-miss warning on `add_note` and `add_glossary_term` — the
  near-miss rule shared so lint and the write path cannot drift. Detection is deterministic string
  statistics; only the canonical-form choice needs a human, sandwiched between two mechanical layers.
  Prototyped in the golden (`3431858`), 12 fixture tests assert exactly the planted flags and no
  false positives. **Now emitted into every brain** (manifest `[verbatim]`, **CI gate 13**): the
  detector suite runs against the emitted bytes and the lint CLI is smoke-tested. The lint tool is
  informational (exit 0 on findings); the gate fails on a detector regression. **Deferred:** Stage 7
  (read-only `lint_tags` MCP tool — hold until a brain is big enough to feel drift).
  → **[docs/tag-hygiene.md](docs/tag-hygiene.md)**.
- **Done 2026-07-16 — #33, Claude Desktop e2e (canned prompts + side-effect verifiers).** Closes the
  gap G6 (`check_mcp_server.py`) cannot: it drives a *Python* MCP client, so it is blind to
  Desktop-client bugs (the `outputSchema` drop, §11). No API drives Desktop's GUI, so the driver is
  a **human** pasting ready-made prompts stored in the devkit (`desktop-e2e/`), but the **oracle is a
  script** — 5 verifiers assert deterministic **side effects** (a note created + committed, a
  glossary term defined), never the model's prose; the near-miss/traversal/search bits stay
  human-observed. Validated against a simulated fixture (passes on a correct brain, fails when the
  side effect is absent). Human-in-the-loop **release acceptance, not a CI gate** — same pattern as
  the Obsidian hand-tests. → **[docs/desktop-e2e.md](docs/desktop-e2e.md)**.
- **Done 2026-07-14 — #28, a live content-corruption bug, FIXED.** `add_note`'s pathspec commit left
  the **real index holding the pre-hook blob** when `glossary_autolink` edited the note, so **the
  next commit by anyone silently reverted the link** — observed in the real brain. Fixed + regression
  test under the non-default config, negative-tested.
  → **[docs/partial-commit-index-poisoning.md](docs/partial-commit-index-poisoning.md)**;
  **@david still to review §6** (the judgement calls, not the code).
  It spawned **#29**: CI ran only the *default* config, so the toggle that triggers the bug was
  never on. **A matrix that only exercises defaults does not test the product.**
- **Done 2026-07-14 — #29, CI gate 10: non-default config is now tested.** #28 shipped through a
  green suite because the toggle that triggers it is off by default. Every `features.toml` toggle is
  now flipped off its default at least once — and **the gate reads the toggle space from the config
  file, so a new toggle with no coverage fails the build.** Forgetting is a build error now.
- **Done 2026-07-14 — #26: a link insertion no longer re-embeds a note.** The canonical view strips
  wikilink markup before hashing/embedding, so auto-linking a term across the vault now costs
  **zero** re-embeds — while a real prose edit still re-embeds. It also closes the feedback loop the
  design only half-shut: the loop was barred for frontmatter but the body (where `glossary_scan`
  writes its links) was still being embedded verbatim, round-tripping the system's own output into
  its own vectors.
- **Done 2026-07-14 — #25 `add_glossary_term`: the glossary is now writable from Claude Desktop.**
  Define a term, and it link-cascades across the whole vault in one commit (the cascade is the
  feature) — #26 made that nearly free. Eighth tool; refuses slug/alias collisions; never embedded;
  the "what earns a term" bar is in the description. → [mcp-server.md §3.3](docs/mcp-server.md).
- **Done 2026-07-15 — #30: doctor now detects a stale embedding** (a vector that predates the note's
  current canonical view) and `--repair`s it; `update_brain` warns on a view-defining change. CI gate
  11. The silent-staleness #26 could leave in an upgraded brain is now loud.
- **Done 2026-07-15 — #24: nothing the server does can hang.** The embedder's HTTP call is bounded
  (a stalled Ollama errors, not hangs), and git subprocesses spawn non-interactively with DEVNULL
  stdin, ssh BatchMode, and a caught timeout. CI gate 12, negative-tested.
- **Done 2026-07-15 — #27: list tools are bounded + filterable, and `list_tags` exposes the tag
  vocabulary** (filter/rank not pagination; a silent cap fails CI). Nine-tool surface.
- **▶▶ NEXT — #23** (investigate shipping the brain as a Claude Code plugin — docs/research, no code).
  Still human-blocked: the #28 review + the glossary flashcard/graph Obsidian hand-test. Still human-blocked: the #28 review + the glossary
  flashcard/graph Obsidian hand-test.
- **Also open, from #26 — [#30] stale vectors after an embed-view change.** `update_brain` ships a
  new canonical view but never re-embeds, so an upgraded brain silently holds vectors built by the
  *old* view. The real brain is correct only because the migration was run **by hand** — and a
  migration that depends on remembering is not a migration. `doctor.py` should detect the stale
  hash and `--repair` it.
  *Recorded dissent on ordering:* **#24 arguably belongs first.** #25 is a feature; #24 is a live
  defect in shipped code — the embedder's `urlopen()` has **no timeout**, so a cold Ollama model
  load can hang the server **forever**, reachable from both `search_second_brain` and `git commit`.
  A new write tool sits on top of that same substrate. The user's call stands; noting it so the
  order is a decision, not an oversight.
- **Then — the glossary tail (needs a human at an Obsidian window).** Both remaining glossary
  items are docs-only but **cannot be verified from CI** (it never opens Obsidian), so each now
  carries a hand-test as its acceptance criterion: install the *Spaced Repetition* plugin and see a
  term render as a card, and add the graph colour group — settling which query actually works
  (`path:glossary/` vs `tag:#glossary`; the docs currently contradict each other, which is proof
  nobody has run it). Blocked on a human, not on code.
- **Then:** **#23** (investigate shipping the brain as a Claude Code *plugin* — one installable unit
  instead of the skill install + print-and-instruct MCP registration), or **#8** auto-link `--apply`
  calibration on the real brain (cheap; the threshold is already known).
- **Done 2026-07-13 — the note-quality gate reaches Claude Desktop (follow-on to #5).** `add_note`
  made notes cheap to add, which is exactly how a brain fills with things nobody will ever search
  for — and the rules for *what earns a note* lived only in `CLAUDE.md`, which is unembedded **and**
  never read by Desktop. The gate is now **deliberately duplicated** into the note template (what
  `get_note_template()` returns), justified because **the audiences are disjoint** — an in-repo
  agent can't call an MCP tool, a Desktop assistant can't see `CLAUDE.md`; one rule, two pipes that
  don't connect. A pointer was rejected: it trades an always-loaded rule for one the model must
  remember to fetch, and forgetting is **silent** (the note still gets written, just unfiltered).
  Drift is made impossible rather than promised — **CI gate 9** (`tools/check_note_gate.py`, CI is
  now 9 gates) fails the build if the copies disagree, and the MCP tier asserts the gate actually
  *arrives* in `get_note_template()`'s text. Both negative-tested.
- **Done 2026-07-13 — #5 `add_note`, the write path.** You can now add a note to the brain **from
  Claude Desktop**: it creates the note, commits it (which is what *embeds* it — so it is searchable
  immediately) and pushes it, so the note reaches the brain's other clients rather than living on
  one laptop. The MCP arc is closed: seven tools, happy path + failure modes, every assertion
  negative-tested. See #5 below.
- **Also unblocked:** the real-brain auto-link `--apply` calibration (task #8 — the bench corpus
  proved a confident `t_max ≈ 0.30`).
- **Done 2026-07-13 — #21 MCP negative / security suite.** The MCP tier now tests what the server
  must **refuse** (path traversal on `get_note` — the one untrusted-input surface) and **survive**
  (its vector cache destroyed), not just what it does when used correctly. Headline lesson, learned
  the hard way: **a test whose setup the system silently repairs proves nothing** — deleting
  `brain.db` to prove the glossary never reads it is vacuous, because the server re-hydrates a
  missing cache on startup. Poison it instead, and pin the invariant statically too. See #21 below.
- **Done 2026-07-11 — #22 IT-corpus ablation bed (+ hardened).** Authored
  `tests/seed-corpus/queries.jsonl` + a `--corpus {bench,it}` flag on `tools/ablation.py`, then
  **hardened** the query set (lay/symptom phrasing) to restore headroom (recall@1 0.675, recall@5
  0.975). **Methodology finding:** the nomic-vs-mxbai ranking **flips with query phrasing** (mxbai
  won the first set +13pp, nomic the second +7pp, the hardened set a tie) — so the earlier "mxbai
  decisively wins" was a phrasing artifact, **not** a robust embedder win. Stable across all sets:
  symmetric prefix hurts, canonical view flat. The hardened set is now the honest bed for #3.
- **Done 2026-07-12 — #20 glossary over MCP.** Exposed `vault/glossary/` through two exact-match,
  no-embedding MCP tools (`list_glossary_terms` / `lookup_glossary_term`) so an assistant can
  *discover and use* the glossary — definitions stay out of `search_second_brain` on purpose (hub
  avoidance), enforced in the tool text. mtime-cached index, alias + normalized matching, near-miss
  suggestions; `check_mcp_server.py` at the four-tool surface + six acceptance checks, MCP tier + CI
  green. Built on #19's namespace. Its negative/security depth lands in **#21**.
- **Done 2026-07-11:** **#12 increment 2** — extended `tools/ablation.py` with the two index-time
  ablations (canonical view ON/OFF, embedder model swap nomic vs mxbai-embed-large) + a memoized,
  model-parametrized embedder. Results ([benchmark-corpus §6](docs/benchmark-corpus.md)): canonical
  view is retrieval-**flat** (its value is graph legibility, not search); the model swap is a
  **wash** on far-apart domains (the lever needs closely-related topics); the symmetric task prefix
  measurably hurts. **Decision:** defer `config/features.toml` (Half B) — no built feature is
  situational; the config surface waits for #3/#7. Devkit-side only, CI 8/8 green, nothing emitted.
  **Half B now BUILT 2026-07-12** as **#3 increment 2** — `config/features.toml` shipped with the
  first genuinely situational toggle (`hybrid_search` on/off + `rrf_k`), the query-time lever the
  index-time features never gave it. See #3 in [Retrieval quality](#retrieval-quality-backlog-surfaced-2026-07-04).
- **Done 2026-07-10:** **#15 COMPLETE** — 200-note diverse corpus + 30-query eval set + corpus-driven
  tooling; **acceptance passed on real Ollama** (purity@1 98%, separation +0.136, retrieval top-5
  30/30, the performing-arts trio separates). #18 (corpus-separation decision — grade the #16/#17
  corpus *supervised*; IT = supervised + adversarial, #15 = unsupervised); scoped #19 (glossary
  layer) + seeded a PARA(G) glossary in the real brain.
- **Then queued:** #12/#13 (feature
  catalog + ablation harness), #3 (hybrid FTS5 retrieval), #5 (`add_note` write tool), #19 (glossary
  controlled-vocabulary layer — local-first brain feature, alongside #3/#8), #20 (glossary over MCP
  — exact-match lookup/list tools, depends on #19), #21 (MCP negative/security tests — path-traversal
  now, glossary-isolation with #20), #22 (IT-corpus query set + `--corpus` flag — the hard-topic
  ablation bed, DONE + hardened — embedder ranking flips with query phrasing, no robust winner).
- **Done recently:** #9 README managed block (2026-07-09: markers around the golden/template README
  body + `update_brain.py` splices the devkit block into a brain's existing markers, preserving the
  user's preamble/appendix; hermetic CI gate 8/8 — closes the #10→#8→#9 thread);
  #17 test-corpus clustering improvement (2026-07-09: rewrote all 100 notes
  ~3× longer + topic-anchored; purity@1 69%→79%, purity@5 55%→75%, separation +0.053→+0.072 —
  84%/+0.086 under the `clustering:` prefix; only bodies changed, tooling untouched);
  #16 test-corpus seed/teardown utility (2026-07-09); #8 auto-linking
  (2026-07-08: canonical view + nomic prefixes + KNN calibration + `related_auto:` write path +
  Obsidian-format CI gate + `content_hash` skip-gate; `--apply` deferred to #15). Bigger roadmap:
  big-brain Approach A (sync loop on task #6), then Approach B (Postgres, capability-gated).
- [x] **Remote-backed brains — connect a new brain to a git remote at creation
      (task #6; BUILT 2026-07-07).** `create_second_brain.py --remote <URL>` (+ `--no-autosync`):
      after `git init` + first commit + hooks, `git remote add origin` + `git push -u
      origin HEAD`. **Preflight (detect + instruct, never configure creds), run BEFORE
      generating so a failure creates nothing:** git identity set, `git ls-remote <URL>`
      authenticates + reaches, remote **empty** — each fails early with the exact fix.
      The push runs **after** the local brain is complete, so a mid-push failure still
      leaves a usable local brain (prints how to push by hand). **State:** a per-machine,
      uncommitted `secondbrain.autosync` git config — **auto-sync ON by default** whenever
      a remote exists (absent/`true` → on); `--no-autosync` writes `false`; cloned peers
      auto-sync by default. This task *sets* it; big-brain Approach A *consumes* it (the
      sync loop is out of scope here — connect-at-creation only). README gained a "Back it
      up / share it (git remote)" prerequisites section; the devkit **CLAUDE.md** pointer
      updated. **Hermetic CI coverage** (`tools/check_remote_sync.py`, wired as `ci.py`
      gate 6/6): connect → push → clone-as-peer → autosync default/`--no-autosync` → both
      preflight rejections (non-empty + unreachable, non-destructive), all against a local
      **bare repo** (`file://`) — git + stdlib only, no network/creds, so it lives in the
      gate (unlike the Ollama/`mcp` opt-in checks). Emitted brain unchanged (Mode A ≡ B,
      45/45). Full design in [docs/remote-backed-brains.md](docs/remote-backed-brains.md).
- [x] **Author two devkit docs (done).** (task #4)
  - [x] **`docs/source-map.md`** — inventory of every source file (emitted brain
        `scripts/`+`skill/`, devkit `tools/`, hooks/config) with a one-line purpose,
        grouped by role, cross-checked against `emit-manifest.toml`. Referenced from
        `README.md` (Project Layout) + `CLAUDE.md` (Where things are specified).
  - [x] **`docs/claude-desktop-workflow.md`** — the consolidated end-to-end Claude
        Desktop journey (own/generate a brain → deps + Ollama → embed → register with
        the absolute-interpreter gotcha → enable connector → use → verify → the
        `outputSchema` lesson), linking the README steps + `mcp-server.md` §10/§11.
- Then the previously-queued work: MCP CI coverage (tasks #1 py_compile, #2 behavioral),
  `tools/update_brain.py` (G4), hybrid FTS5 retrieval (task #3, backlog).

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

## Milestone G2 — Validation harness  ✅
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
  **Unblocked (2026-07-02):** Ollama + `nomic-embed-text` available; the real
  embed→hydrate→search path is validated (correct top-1 retrieval with clear
  separation). Depends on the runtime setup in [G5](#milestone-g5--runtime-setup-ollama--embedder).
  - [x] Retrieval-quality check: known queries put expected notes in top-k / above
        a cosine threshold. `tools/check_semantic_retrieval.py` — generates a brain,
        `embed_vault.py` (ollama) → `hydrate_cache.py` → `search_vault.py`, asserts
        each distinct-phrasing query ranks the expected note #1 under a distance
        threshold. **4/4 pass** (top-1 distances ~0.25–0.41). Embedding primitive:
        `scripts/embed_vault.py` (golden `135bcfb`, now emitted).
  - [x] Exercises the real production path (Ollama call, 768-dim check, L2-normalize,
        sqlite-vec KNN) that `test` never touches.
  - [x] Gated on Ollama being available; **not** part of the portable/CI acceptance
        gate — prints SKIP + exits 0 when Ollama/model absent (verified), so CI
        stays stdlib-only. Run on demand: `python3 tools/check_semantic_retrieval.py`.

## Milestone G3 — Production generation (Mode B)  ✅
The durable product path ([SPEC §5.1](SPEC.md)): generate a real, persistent brain
the end user owns — distinct from the throwaway `sandbox/scratch/` of G2.
`tools/create_second_brain.py` is the end-user entry point (`python3 tools/create_second_brain.py ~/my-brain`).
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
      brain" section + `create_second_brain.py`'s own `--help`/docstring.

## Milestone CI — Self-sustaining automation  ✅
Robust, hands-off regression checking on every push/PR. **Hard requirement: the
devkit is self-contained — CI checks out only this repo and never reaches the
external golden.** That forces the long-deferred [OQ-1](open-questions.md#oq-1)
resolution: vendor the golden's *expected output* **into** the devkit as a tracked
regression baseline (Option A). The live `../second-brain-test/` reverts to a
hand-prototyping surface only, and its mothball ([G4](#milestone-g4--lifecycle))
gets closer. Vendoring loses no coverage: the pre-commit hook is still exercised
**for real** via Mode-B generation (`create_second_brain.py` git-inits and the hook fires on
a note commit), so the vendored golden only needs to be static expected output.
- [x] **Vendor the golden (resolve [OQ-1](open-questions.md#oq-1) → Option A).**
      `tools/vendor_golden.py` snapshots the live golden's 42 *tracked* files
      (`git ls-files`; symlinks + exec bits preserved, no `.git`/git-ignored
      artifacts) into the devkit-tracked `tests/golden/`. A **dev-machine** step,
      run by hand when the live golden changes; **CI never runs it** — the committed
      snapshot is what CI diffs against. The sync self-gates: it runs the partition
      check over the fresh snapshot and fails loudly if the golden no longer
      matches the manifest. All 42 files track cleanly (the vendored `.gitignore`
      ignores none of them; fixture sidecars included).
- [x] **Repoint the harness at the in-repo golden.** `check_structural_diff.py`,
      `check_manifest_partition.py`, `build_template.py`: `GOLDEN` → `REPO_ROOT/tests/golden`.
      Partition now enumerates `tests/golden/` via a filesystem walk (no external
      `git ls-files`), fully self-contained. Verified: partition green,
      `template/` rebuilds byte-identical from the snapshot, Mode-A diff 33/33.
- [x] **`.github/workflows/ci.yml`** — on push + PR to `main`, Python 3.11+
      (stdlib only), runs `python3 tools/ci.py`. No external repo, network, or pip.
- [x] **Local ≡ CI parity.** `tools/ci.py` is the single entry point CI invokes,
      running the full gate: partition → template-in-sync (rebuild + `git diff`
      guard) → Mode-A harness → Mode-B smoke (`create_second_brain.py` + the same diff
      oracle). Passes locally end-to-end; a self-contained git identity lets the
      Mode-B commit run on a bare CI runner.

### MCP coverage (follow-on, surfaced 2026-07-04)
The `outputSchema`/Claude-Desktop regression proved a real gap: CI **byte-diffs**
`mcp_server.py` but never **runs** it (and `mcp` isn't installed), so a syntax error
or a behavior regression ships green. Two layers, only the first in the hermetic gate:
- [x] **Layer 1 — compile every emitted script in `tools/ci.py`** (incl.
      `mcp_server.py`). Done: new gate `3/5 emitted scripts compile` uses builtin
      `compile()` over `template/**/*.py` (post-clean emitted tree) — no import, no
      `.pyc` written, zero new deps, stays stdlib-only. Verified it catches an injected
      `SyntaxError` (exact file+line) and passes on the 15 real scripts. (task #1)
- [x] **Layer 2 — opt-in behavioral MCP test** — DONE: `tools/check_mcp_server.py`
      (modeled on `check_semantic_retrieval.py`). Spawns the emitted stdio server on a
      generated `test`-backend brain via a real MCP client and asserts (1) exactly the
      two tools listed, (2) **no `outputSchema`** on either (locks in the Desktop fix),
      (3) `get_note` refuses a path outside `vault/`, (4) `search_second_brain` returns
      absolute vault paths + `get_note` reads one back. **SKIP + exit 0** when `mcp`
      absent (stays out of the portable gate); needs `mcp`+`sqlite-vec`, **not** Ollama.
      Verified: passes green, and a negative test (reverting `structured_output=False`)
      is caught on both tools. (task #2)
- [x] **Layer 2b — MCP negative / security cases (task #21).** DONE (2026-07-13):
      `check_mcp_server.py` now drives the failure modes as well as the happy path —
      traversal refusals (each asserted to fail *on the vault guard*, not on an
      incidental `FileNotFoundError`), an in-vault `..` still served (proving escape
      detection, not a naive `..` reject), substrate disjointness both ways, and the
      glossary's embedding-free contract. **Every assertion was negative-tested** by
      deliberately breaking the invariant it guards (5 regressions, all caught).
      That pass earned the task's real lesson: the first embedding-free check was
      **vacuous** — it deleted `data/brain.db`, but the server *re-hydrates a missing
      cache on startup*, so a glossary wired straight into the vector store passed
      it clean. The fix is to **poison** the db with garbage bytes (exists, so no
      re-hydrate; corrupt, so any read raises) and to add a **static AST check** that
      the glossary functions never even name `DB_PATH`/`brain.db`/`search_vault` —
      catching the coupling the behavioral test cannot see (`DB_PATH.exists()` gating
      changes behavior without opening the file). Generalizes: *a green test that
      cannot be made to go red is decoration* — and a test whose setup the system
      silently repairs is the sneakiest kind. Also hardened the harness to report a
      broken tool as a legible FAIL rather than a `JSONDecodeError` traceback.
      Original scope, all shipped:
      - **Path traversal on `get_note`.** The guard is resolve-based (`p.resolve()` then
        `vault not in p.parents`), so `..` is collapsed *before* the check — assert that
        explicitly: refuse an absolute path outside the vault (`/etc/passwd`), refuse a
        `..`-escape that leaves the vault (`vault/../<file outside>`, `../../etc/passwd`,
        and a relative hop to a real sibling like `../config/embedder.toml`), **and**
        confirm the block is escape-detection not a naive `..`-string reject — a `..` that
        stays *inside* (`vault/resources/../resources/<note>`) is still **allowed**. (Note
        symlink-escape as a known gap, out of scope unless cheap.)
      **Gated on #20 (needs the glossary tools):**
      - **Search excludes the glossary.** `search_second_brain("ablation")` returns
        **zero** `glossary/` paths — the embedding-exclusion holds end-to-end at the tool,
        not just structurally (regression guard for #20 acceptance #5).
      - **The glossary tool is embedding-free.** `list_glossary_terms` /
        `lookup_glossary_term` never read `data/brain.db` and never return a PARA/vector
        note — assert they still work with the **cache removed** (proving no vector
        dependency) and that their results are drawn only from `glossary/*.md`.
      - **Substrate disjointness.** Glossary tools return only glossary notes; search
        returns only PARA notes — the two retrieval substrates are provably disjoint.
      - **Tool-count update.** #20 makes the existing `tools/list ==
        {search_second_brain, get_note}` assertion grow to the four-tool set — this task
        owns that change so the tier stays green when #20 lands.
      Stays `mcp`-gated (SKIP + exit 0 when `mcp` absent), `test` backend, no Ollama —
      same envelope as Layer 2. The traversal half can land immediately; the glossary half
      lands with #20.

## Milestone G5 — Runtime setup (Ollama + embedder)
Make a generated brain **runnable for real semantic search**, not just structurally
valid. The `test` backend proves plumbing; real relevance needs Ollama +
`nomic-embed-text`. This milestone is the documented + scripted path from a
freshly-generated brain to a working semantic index.
- [x] **Usable out of the box — no env var.** The embedder backend is a per-brain
      config (`config/embedder.toml`), read by `embedder.py` (env override > config
      > `test` fallback). A generated brain ships `backend = "ollama"` (cleaned from
      the golden's `test`), so embed + search both default to Ollama and agree —
      real semantic search works with zero `SECOND_BRAIN_EMBEDDER` fiddling. The
      golden/CI stay `test` (fixtures + self-test pin it explicitly). Verified: a
      fresh brain embeds→hydrates→searches correctly with the env var unset.
- [x] **Auto-hydrate on commit (write→queryable in one step).** BUG: the pre-commit
      hook writes a note's `.embed.json` sidecar but never rebuilds the cache
      (`data/brain.db`), so a committed note is invisible to search until a manual
      `hydrate_cache.py` — the brain isn't useful without it. Fix: a **`post-commit`**
      hook that runs `hydrate_cache.py` (after the commit, so it never blocks/undoes
      it; warns on failure; needs sqlite-vec, not Ollama). Standard flow becomes
      write note → commit → searchable. `create_second_brain.py` must commit the scaffold
      **before** wiring `core.hooksPath` so generation fires neither hook (no
      embedder / no derived `brain.db` in the diffed tree).
- [x] **Incremental cache updates (no teardown → no downtime).** BUG: the only
      cache op was `hydrate_cache.py`, which **deletes and rebuilds** `data/brain.db`
      wholesale — during that window a concurrent query hits a missing/empty DB, and
      it's O(all notes) for a one-note change. Fix: `scripts/update_cache.py` with
      **`--upsert <note>`** (DELETE+INSERT one row from its sidecar) and
      **`--delete <note>`** (drop one row + its orphan sidecar), operating on the
      **existing** table (`CREATE … IF NOT EXISTS`, never torn down). The post-commit
      hook uses `--from-commit HEAD` (upsert added/modified PARA notes, delete
      removed) so the brain stays query-able throughout. `hydrate_cache.py` stays for
      full/bulk rebuilds.
- [x] Document the Ollama runtime in the brain's **first-time setup** (README):
      install Ollama (`brew install ollama` / download), start it (`ollama serve`),
      pull the model (`ollama pull nomic-embed-text`), then verify with `doctor.py`.
      A fresh brain defaults to `backend = "ollama"`, so no env var is needed. Golden
      `c08be09`; Setup gains a "Turn on semantic search (Ollama)" block, the
      self-check pairs `self_test.py` (plumbing) with `doctor.py` (runtime). Emitted
      (README cleaned), CI green.
- [x] Ship `scripts/embed_vault.py` into every brain (bulk-embed) — landed in the
      golden (`135bcfb`) and propagated: `emit-manifest.toml` (verbatim 24→25),
      re-vendored `tests/golden/` (43 files), rebuilt `template/` (29 files), CI
      green (34 emitted). First-run flow: `pip install` → Ollama ready →
      `embed_vault.py` → `hydrate_cache.py` → `search_vault.py`.
- [x] A **`scripts/doctor.py`** preflight: checks Python deps (sqlite-vec/apsw),
      Ollama reachable + model pulled, and full vault↔sidecar↔db consistency
      (missing/orphan sidecar, note-missing-from-cache drift, stale row, wrong-backend
      stamp, wrong dim) with `--repair` — a single "is my brain ready?" command with
      actionable fixes. Golden `c3f15da`, emitted verbatim (`e180069`). **Live-verified
      against a real Ollama server** (`c08be09` session): reachable/model-pulled → ok,
      unreachable + model-missing → actionable FAILs, `--repair` embeds all notes via
      real Ollama and rebuilds the cache to green, and semantic search then ranks the
      expected note #1. All six consistency classes exercised. Documented in the README.
- [x] **Cache concurrency-safety, layer 1 ([OQ-5](open-questions.md#oq-5)).**
      `db.connect()` PRAGMAs: `journal_mode=WAL` + `busy_timeout=5000` (default 0 →
      errors on contention), both `sqlite3`/`apsw`, re-applied per open. A cheap,
      general robustness win shipped now. Golden `0520c0f`; WAL `-wal`/`-shm` already
      covered by the `data/*` gitignore. Verified hydrate→search→doctor green under
      WAL; vendored + template rebuilt, CI green (db.py stays verbatim, never run in
      CI). **Layers 2 + 3 moved to the MCP server ([G6](#milestone-g6--the-ai-interface-reach-the-brain-from-any-project))**
      — they only matter once a long-lived reader exists.
- [x] **Install automation vs guidance — DECIDED: detect + instruct, never
      auto-install.** Consistent with the whole devkit stance (`install_skill.py`
      never mutates config silently; `--apply`-gated). Auto-running `brew install
      ollama` is invasive, platform-specific (brew = macOS only; Linux/Windows
      differ), sometimes needs sudo, and can clash with an existing setup — high
      risk for no gain when `doctor.py` already prints the exact command
      (`ollama pull nomic-embed-text`, "is `ollama serve` running?",
      `pip install -r requirements.txt`). **`doctor.py` already implements this
      policy** — no code needed. An opt-in guided installer stays a possible future
      nicety, not built now. Ollama remains a runtime dependency of a *brain*, never
      of the devkit's CI (which is `test`-only).

## Milestone G6 — The AI interface: reach the brain from any project
**Default usage (decided):** the AI is **not** working inside the brain — it is
building system X in *X's own repo* and must **reach out to the brain as a
preliminary step** to discover existing conventions / decisions / tribal knowledge
before designing. So the capability must be **global** (callable from any working
directory), not scoped to the brain repo. This rules out a brain-local project
skill as the primary mechanism (it only activates when cwd is inside the brain).

Two orthogonal needs: a **global query mechanism** and a **behavioral trigger** so
the consult is reflexive. **Mechanism decided: a user-level skill that shells out
to the brain's Python scripts — NOT MCP.** A skill is far lower standing token cost
(progressive disclosure: only its name+description preload; the body loads on
invoke) and, by shelling out via the already-present **Bash** tool, adds **zero new
tool schema** — whereas an MCP server loads every tool's JSON schema into context
each session. MCP is reserved for the one case a skill can't serve (below).
- [x] **Second-brain skill — PRIMARY mechanism.** Emitted `skill/second-brain/`
      (SKILL.md + query.py) — a **neutral dir, not under `.claude/`**, so it needs
      no `.claude` manifest split (emits as ordinary `verbatim`). `query.py`
      resolves the brain root relative to itself (`parents[2]`), so it works through
      the install symlink with no hardcoded path; it ensures the cache, forwards to
      `search_vault.py`, and prints **absolute** note paths (the agent is in another
      project's cwd). SKILL.md's `description` drives proactive "consult before
      designing" use. No new dependency, no server. Golden `c9b8838`; CI green
      (38 emitted). Verified real Ollama retrieval via `query.py` in the golden.
- [x] **Behavioral trigger — productized.** The skill `description` is sharp
      ("consult before designing / making convention decisions"); the reinforcement
      is now a formal, opt-in feature rather than a manual per-user edit.
      `install_skill.py --nudge` appends a marked, idempotent "consult the
      second-brain before designing" block to each tool's global memory
      (`~/.claude/CLAUDE.md`, `~/.gemini/GEMINI.md`) — detect+instruct, `--apply`
      required, never silent. README documents it + a hand-install snippet. Golden
      `b73aaca`; emitted (install_skill.py verbatim, README cleaned), CI green.
- [x] **Installer/uninstaller (detect + instruct).** `scripts/install_skill.py`
      **symlinks** the skill into a chosen repo's `.claude/skills/` (`--project`, the
      default per-repo stance) or `~/.claude/skills` + `~/.gemini/skills` (`--global`),
      and (opt-in) installs the `--nudge` reflexive trigger. Dry-run unless `--apply`;
      skips a tool whose config dir is absent (instructs); never mutates global config
      silently. **`--uninstall`** reverses whichever parts you name — removes only this
      brain's symlinks and only the marked nudge block, leaving the rest of your config
      intact (so a user can cleanly drop the brain). Verified full install→idempotent→
      uninstall round-trip against a throwaway HOME (golden `b73aaca`).
- [x] **Gemini parity** — `install_skill.py --global` covers `~/.gemini/skills/`
      (same SKILL.md standard); `GEMINI.md` already symlinks `CLAUDE.md` for memory.
- [x] **MCP server — SECONDARY, Claude Desktop only. BUILT (v1).** For clients that
      **cannot shell out to local Python**. `scripts/mcp_server.py` (FastMCP, stdio)
      exposes read-only `search_second_brain(query, k)` + `get_note(source_file)` over
      the same Ollama+sqlite-vec index, as a thin wrapper over the brain's own
      `embedder`/`db`/`search_vault` — so there is exactly one retrieval impl. Scoped
      in [docs/mcp-server.md](docs/mcp-server.md); target **`stdio` + Claude Desktop**,
      **claude.ai web out of scope** (a browser can't reach a local `stdio` server, a
      remote one would break local-first). Refactored `search_vault.py` to expose a
      reusable `search()` the CLI + server share (no self-shelling); `get_note` is
      path-validated to `vault/`; hydrate-on-start redirects to stderr so stdout stays
      a clean JSON-RPC channel. MCP SDK is an **isolated optional dep**
      (`requirements-mcp.txt`, `mcp>=1.2`) — never in base `requirements.txt`/CI; the
      server is emitted **verbatim** (byte-diffed + forbidden-ref-scanned, never run in
      CI). OQ-5 layer 2 (in-place hydrate) landed first as its prereq. **Live-verified**
      against a real stdio MCP client AND end-to-end in **Claude Desktop** itself
      (2026-07-04): tools appear under Customize → Connectors and answer a real chat
      query. Golden `4867eec`; CI green (45 emitted). [OQ-6](open-questions.md#oq-6)
      settled. **Deferred to a follow-up:** auto-inserting the Claude Desktop config
      stanza (v1 is print-and-instruct in the README).
  - [x] **Claude Desktop compatibility — disable `outputSchema` (found live 2026-07-04).**
        FastMCP auto-advertises an `outputSchema` for typed-return tools (structured
        output, protocol `2025-11-25`); Claude Desktop's older MCP client silently
        **dropped** both tools → "no tools available." Fix: `@mcp.tool(structured_output=False)`
        on each tool (classic text-output; return still reaches the model as JSON text).
        Verified in Desktop after restart. Full write-up in
        [docs/mcp-server.md §11](docs/mcp-server.md); lesson also saved to `~/notes`.
  - [ ] **Write path for the glossary — `add_glossary_term` MCP tool (task #25).** The glossary is
        readable from Claude Desktop (`list_glossary_terms` / `lookup_glossary_term`, #20) but not
        **writable**: `add_note` is PARA-only by allowlist, and `glossary_new.py` is CLI-only. So an
        assistant can *use* the controlled vocabulary but never *extend* it — the same asymmetry
        #5 just closed for notes. Naming: **`add_glossary_term`**, not `insert_`, to match
        `add_note` (one verb for one concept).
        **The sweep — DECIDED 2026-07-14 (user): run it. Option (b).** `glossary_new.py` scaffolds
        the term note **and** sweeps the whole vault linking the term's first occurrence in every
        PARA note; the tool does both and commits everything it touched. The cascade **is the
        feature** — "the system does the work for me" — not a blast radius to be minimized. This
        deliberately relaxes `add_note`'s one-file-per-commit rule, and the relaxation is
        principled: `add_note` stages one file because it must never sweep up work the *user* was
        doing; the glossary sweep's multi-file edit is **its own intended output**, not somebody
        else's changes swept in by accident. Still required: only ever stage the files the sweep
        *itself* linked (never `git add -A`), so a user's unrelated in-progress edits still cannot
        ride along in an agent-authored commit. **#26 makes this cheap** — with a
        wikilink-invariant canonical view, a link-only edit does not re-embed at all.
        Also needed: an `aliases` param (lookup depends on frontmatter `aliases:`); refusal on a
        key **or alias** collision with an existing term (today it is first-writer-wins with a
        stderr warning — invisible over MCP); reuse `glossary_new.scaffold()` rather than
        duplicating the term shape (single source, per the 2026-07-12 decision); and a **"what
        earns a term"** bar in the tool description — a *controlled* vocabulary that an LLM can mint
        into freely stops being controlled, the same failure `get_note_template`'s gate prevents for
        notes. Cost to weigh: an **8th** tool schema, loaded into every Desktop session whether used
        or not. Tests extend the #5 write suite (create → commit → push → listable/lookup-able
        without restart; collision refusal; still **never embedded** — the glossary must stay out of
        the vector index, which is the whole reason it exists).
  - [x] **Wikilink-invariant canonical view — a link insertion must not re-embed (task #26).**
        DONE 2026-07-14 (golden `bb525e4`). `note_view.canonical_body` now strips wikilink markup
        (`[[term]]` → `term`, `[[slug|surface]]` → `surface`, `![[embed]]` too) before the body is
        hashed and embedded — so a **link-only edit is byte-identical in the canonical view**, the
        existing `content_hash` no-op gate fires, and the note is **not re-embedded at all**, while a
        genuine prose edit still changes the hash and still re-embeds. Verified end-to-end through
        the real commit hook: inserting a link prints `skip (substance unchanged)` and leaves the
        vector sidecar **byte-identical**; editing the prose re-embeds. The emitted `self_test.py`
        now asserts the invariant in **every brain** (and it is negative-tested — removing the strip
        turns CI red). **Migration was far cheaper than feared:** the committed `test` fixtures carry
        no wikilinks, so they reproduce byte-for-byte and needed **no** regeneration; only live
        vaults re-embed once (the real brain: 12 notes, done, doctor green).
        Enables #25's cascade, and closes a feedback loop the design already declared closed.
        **The mechanism, and why it is the right shape:** the embed input is a note's *canonical
        substance view* (`note_view.canonical_body` — body only, frontmatter stripped, whitespace
        pinned) and `embed_staged` **already** gates on its `content_hash`: an unchanged note does
        not re-embed. The gate works; the **view is too literal**. `canonical_body` does not strip
        wikilink markup, so `An ablation shows…` and `An [[ablation]] shows…` hash differently
        (verified: `b0e29cda3` vs `2ef73b957`) and the note re-embeds for a change that carries
        **no meaning**. Fix: normalize `[[slug|surface]]` → `surface` and `[[term]]` → `term`
        *before* hashing/embedding. Then a link-only edit leaves the embed input **byte-identical**,
        the existing hash gate fires, and the glossary cascade costs **zero** re-embeddings — while
        a genuine edit to the prose still changes the hash and still re-embeds. **The hash
        comparison over the markup-stripped view is precisely what distinguishes "the content
        changed" from "a link was inserted", which is the distinction the whole design needs.**
        **This is a correctness fix, not just an optimization.** `note_view.py`'s own stated
        invariant is that the embedding is computed over substance, *never* over metadata, so that
        **the system's own output cannot feed back into the vector**. A wikilink written by
        `glossary_scan` is exactly the system's own output — the loop was closed for frontmatter
        and left open through the body. And `[[ablation]]` vs `ablation` is pure markup noise
        perturbing a vector for no semantic reason.
        **Cost, honestly:** changing the view changes **every** note's `content_hash` → a one-time
        full re-embed of every vault, and the committed `test`-backend fixtures that `self_test.py`
        byte-diffs must be regenerated. A real migration, but a one-off. Tests: a link-only edit
        produces an identical hash and **skips** the embed; a prose edit still re-embeds; a piped
        `[[slug|surface]]` normalizes to its surface text; fixtures regenerate byte-stably.
        **The generalised lesson is written up in the real brain** (a project-independent note, this
        repo is only its evidence): *"Embed the substance, not the file"* —
        `vault/resources/embed-the-substance-not-the-file.md`.
  - [x] **BUG — `add_note` leaves a poisoned index when a hook edits the note (task #28).** FIXED
        2026-07-14 (golden `9a36850`); **full write-up → [docs/partial-commit-index-poisoning.md]
        (docs/partial-commit-index-poisoning.md)**. Found in the wild in the user's real brain:
        a commit adding a *new* note silently **reverted a `[[wikilink]]` in a different note it
        never touched**. Fix: re-sync the real index for the path immediately after the pathspec
        commit (`git add -- <rel>`); the pathspec stays — it is doing its job. Regression test runs
        the write suite with **`glossary_autolink = true`** (non-default), asserts `git diff
        --cached` is empty after the call, and carries an anti-vacuity check that the hook really
        did edit the note; negative-tested (removing the fix turns the tier red).
        - [ ] **@david — REVIEW this failure mode + the fix** (§6 of the doc). Four load-bearing
              judgements to confirm, not code: that the pathspec commit **stays** (the alternative —
              committing the whole index — has no such bug, but lets an agent's commit contain your
              unrelated staged work; the bug was worth having); that the fix is a post-commit index
              refresh; that the blast radius is bounded to file-modifying hooks under a non-default
              toggle; and whether to skim `git log -p vault/` for other reverted links (signature:
              a commit that removes `[[…]]` from a note it otherwise does not touch).
        **The original report, kept for the mechanism:**
        **Mechanism.** `add_note` commits with a **pathspec** (`git commit -- <file>`) so it can
        never sweep up the user's staged work — the safety property #5 was built around. But a
        pathspec commit is a **partial commit**: git builds a **temporary index** and hands *that*
        to the hooks. With `glossary_autolink = true`, the pre-commit hook edits the note (links a
        glossary term) and re-stages it — **into the temp index**. So `add_note`'s own commit is
        correct. But the **real index is never updated**: it keeps the pre-hook blob. That leaves a
        phantom staged change — a staged *revert* of the hook's edit — lying in wait. The next
        commit by anyone (a human, or Claude Code) silently includes it and **un-links the term**.
        Observed exactly this: an unrelated commit reverted `[[ablation]]` → `ablation` in a note it
        never touched.
        **Fix.** After the pathspec commit, re-sync the real index for that path (`git add -- <rel>`)
        so it matches the committed tree. Keep the pathspec — it is doing its job; the missing step
        is the index refresh. Any tool doing a partial commit alongside file-modifying hooks needs
        this.
        **Why CI missed it, which is the lesson.** `glossary_autolink` defaults to **false**, so the
        golden and the whole harness run with the hook that triggers it **switched off**. The write
        suite passed because it never exercised the configuration the user actually runs. *A test
        matrix that only covers the default config does not cover the product.* Test: run the
        `add_note` suite with `glossary_autolink = true` and assert **the index is clean after the
        call** (`git diff --cached` empty) — and negative-test it, since without the fix it must go
        red.
  - [x] **CI must exercise NON-DEFAULT config, not just the defaults (task #29).** DONE 2026-07-14 —
        **CI gate 10** (`tools/check_config_matrix.py`; CI is now **10** gates). Generalised straight
        from **#28**, which shipped, passed every gate, and then corrupted note content in a real
        brain — because the toggle that triggers it (`glossary_autolink`) **defaults to `false`**, so
        the golden, the template and every harness run executed with the only file-modifying hook
        **switched off**. The write suite that explicitly asserts "never touch the user's staged
        work" passed precisely because the triggering condition never occurred. *A test matrix that
        only exercises defaults does not test the product.*
        **Built:** every `features.toml` toggle is flipped **off its default** at least once —
        `hybrid_search` false (the vector-only baseline), `rrf_k` 10, `glossary_autolink` true (a
        pre-commit hook that *rewrites the file being committed*: it must link the term, embed the
        linked note, and leave a **clean index** — the #28 signature, now asserted in the plain-git
        flow too, not just over MCP). **n+1 runs, not 2^n** — deliberately.
        **The anti-recurrence mechanism is the real deliverable:** the gate **derives the toggle
        space from `config/features.toml` itself**, so shipping a new toggle without coverage — or
        letting a default drift out of step with the matrix — **fails the build**. Forgetting is now
        a build error, not a bug found in production. Negative-tested four ways: a new uncovered
        toggle, a drifted default, a broken hook path, and (the subtle one) **a toggle that is
        silently ignored**.
        **Names its gaps instead of implying coverage:** toggle *interactions* are untested (one
        flip at a time) and the `ollama` backend is not exercised (all gates run `test`; Ollama is
        opt-in via `check_semantic_retrieval.py`). Printed on every run — a silent gap reads as
        coverage.
  - [x] **Bounded, filterable list tools — and the missing tag vocabulary (task #27).** DONE
        2026-07-15 (golden `2646676`). `list_vault`/`list_glossary_terms` gained a `match` filter and
        a shared **honest cap** (`SECOND_BRAIN_LIST_CAP`, default 50) whose overflow appends a
        `{_truncated}` marker saying how many were omitted and how to narrow — a **silent cap fails
        the mcp tier** (negative-tested). New **`list_tags`** returns the frontmatter tag vocabulary
        as `{tag,count}` sorted by count (the only tool that exposes it, so a Desktop assistant stops
        inventing near-miss tags). Nine-tool surface. **Filter/rank, not pagination** — the model
        primitive. → [mcp-server.md §3.4](docs/mcp-server.md). ORIGINAL: The listing
        tools (`list_vault`, `list_glossary_terms`, and the `list_tags` this task adds) return
        *everything*. At a few hundred notes that is a wall of context; at a few thousand it is
        unusable. **Pagination is the wrong fix** — cursors/offsets are for a human scrolling a UI;
        an agent handed "page 1 of 12" either treats it as the whole truth or burns twelve
        round-trips. For a model-facing tool the primitives are **filter** and **rank**, not
        **page**.
        **The real hazard is silent truncation.** A capped list that doesn't say it was capped reads
        to the model as *"this is everything"* — it fails to find `ml`, invents `machine-learning`,
        and the vocabulary quietly forks. **Every bounded response must state what it omitted and
        how to narrow** ("showing 30 of 214; pass `match=`"). Same disease as a green test that
        can't go red: a silent cap reads as complete coverage.
        Per tool, because the purpose differs:
        - **`list_vault`** — keep it *structural* (counts per root; notes for one root, `match`
          filter, capped + self-describing). The reason a model calls it before writing is *"does
          something like this already exist?"* — that is a **semantic** question `search_second_brain`
          already answers better. Point the tool description at search; don't rebuild retrieval
          inside a lister.
        - **`list_glossary_terms`** — bounded *by design*: a **controlled** vocabulary that grows big
          enough to need paging is a **smell, not a requirement** (it means terms are being minted
          that shouldn't be — see #25). Return it whole, add a `prefix`/`match` filter, cap honestly.
          "Nearest similar" already exists on the lookup side (difflib near-miss).
        - **`list_tags` (NEW — a real gap).** The vault has an evolved tag vocabulary
          (`second-brain` ×9, `retrieval` ×9, `ml` ×7 …) and **no tool exposes it**: `list_vault`
          returns only title/path, `add_note` takes freeform `tags`. So an assistant in Claude
          Desktop is **blind to the vocabulary and invents near-misses** — every Desktop-written
          note is a coin-flip on tag drift. Return tags **sorted by count** with the total (frequency
          ordering is what makes truncation meaningful — the ones worth reusing are the common ones)
          plus a `match` filter. `note_view.frontmatter_tags` already exists to read them.
  - [x] **Stale vectors after an embed-view change — detect it, don't rely on memory (task #30).**
        DONE 2026-07-15 (golden `1a10689`). Both halves built: `doctor.py` recomputes each note's
        `content_hash`, compares it to the sidecar's stored hash, reports a mismatch as a **stale
        embedding**, and `--repair` re-embeds it (catches a prose edit not re-embedded AND the #26
        view-change case; a missing stored hash counts as stale so an old brain re-embeds).
        `update_brain.py` prints a **migration notice** when it changes a view-defining file
        (`note_view.py`/`embedder.py`) — "your vectors are now stale, run doctor --repair". New CI
        **gate 11** (`check_doctor_stale.py`, negative-tested — a neutered check goes red) proves a
        clean brain reports none, an edited-but-unembedded note is flagged + exits non-zero, repair
        clears it, and a stored-hash mismatch is caught. → [source-map](docs/source-map.md).
        ORIGINAL:
        The honest completion of **#26**. Changing `note_view.canonical_body` changes what every
        note *would* embed to — but `update_brain.py` ships the new code and **never re-embeds**
        (it deliberately never touches `vault/` or `data/`). So any brain upgraded to a version with
        a new canonical view is left holding vectors computed under the **old** view: not broken —
        search still works — but **silently stale**, and they thaw one note at a time, whenever each
        note happens to be committed next. The user's own brain is correct only because the
        migration was run **by hand**. *A migration that depends on someone remembering is not a
        migration.*
        **Build (either, or both):**
        - **`doctor.py` detects it.** It already walks vault ↔ sidecar ↔ cache for consistency; add
          the one check it is missing — recompute `content_hash(note)` and compare it to the hash
          **stored in the sidecar**. A mismatch means the sidecar's vector was produced by a
          *different view of the same unchanged text* — i.e. the embed input definition moved under
          it. Report it as stale-and-repairable, and let `--repair` run the `embed_vault` +
          `hydrate_cache` pass. This is the natural home: `doctor` is already the "is my brain
          ready?" preflight.
        - **`update_brain.py` warns.** When an upgrade rewrites a file that defines the embed input
          (`note_view.py`, `embedder.py`), print a **migration notice** — "your vectors were built
          with the previous view; run `embed_vault.py && hydrate_cache.py` once" — rather than
          leaving the brain quietly stale.
        **Test:** build a brain, embed, mutate the canonical view, and assert `doctor` reports stale
        (and `--repair` fixes it). Negative-test it — without the check, `doctor` must currently say
        *"healthy & consistent"* while holding vectors from a view that no longer exists, which is
        exactly the false-green this task exists to kill.
  - [x] **The search score is not a distance — label it (task #31).** DONE 2026-07-14 (golden
        `9f42626`); write-up → [docs/search-score-labeling.md](docs/search-score-labeling.md).
        **Surfaced by a false alarm it caused:** a reviewer read the brain's search output, saw every
        score at ~0.03, concluded it was running a **stub embedder**, and told the user their config
        was broken. It wasn't — the brain is on Ollama, 768-dim. The 0.03 is **RRF**: scores are
        computed from **ranks**, so a hit ranked #1 in both lists scores exactly `2/(60+1)` =
        **0.0328** and every score lands near `1/k` **by construction**. Clustered small scores are
        the algorithm working. **But the brain had told them to read it that way** — when #3 shipped
        hybrid search, the MCP tool's description was updated ("hybrid relevance `score`, larger =
        more relevant") and **the skill's was not**: it still said *"distance … lower = closer"*,
        false in both halves, on the interface every CLI agent actually uses. Fixed: the skill calls
        it a **score**, says **higher = better**, and explains that RRF scores are rank-derived and
        carry **no similarity magnitude** — so a small clustered score says nothing about embedding
        quality or which backend is live. `query.py` prints a legend instead of a bare number.
        `autolink.py` deliberately untouched (it reports *genuine* cosine distances).
        **The lesson:** *when a quantity's meaning changes, its label is part of the change.* #3
        reversed the polarity (lower-is-better → higher-is-better) and changed the units, and shipped
        the number under the old name. Nothing broke — which is why it survived. **A mislabelled
        value fails silently, and it fails in the *reader*, not the code**: it cost a competent
        reviewer a confident, wrong diagnosis. When changing a metric, grep for every place its
        *name or interpretation* is written down, not just every place it is computed.
  - [x] **MCP hardening — nothing may hang the server (task #24).** DONE 2026-07-15 (golden
        `e4cc545`; CI **gate 12** `check_hang_safety.py`, negative-tested). All four vectors closed:
        the embedder's `urlopen` is now timeout-bounded (a wedged Ollama raises a clear error
        instead of hanging — tested behaviorally against a local black-hole socket); `_git` spawns
        with `stdin=DEVNULL` (the stdio JSON-RPC channel is no longer reachable by a child), an ssh
        `BatchMode=yes` command (ssh can't prompt), the git prompt off, and a caught `TimeoutExpired`
        (a timeout is a clean failed-op, not a traceback). The gate bounds its own wait so it can't
        hang CI. → [docs/mcp-hardening.md](docs/mcp-hardening.md). ORIGINAL REPORT: surfaced 2026-07-14 from a
        Desktop bug report of `add_note` hanging (4-min timeout) on a `para_root` with a path
        separator. **The reported bug was not in the server, and needs no server change.**
        **Root cause: an unanswered tool-approval dialog in Claude Desktop — the server was never
        asked.** `add_note` is the only *write* tool; Desktop gates dispatch on approval, approval
        is sticky per tool, and nobody clicked the dialog, so the call was never dispatched. Desktop
        then told the model *"the local MCP server may be unresponsive, crashed, or not running"* —
        false in every clause (it was idle, healthy, and never asked), and that message is what sent
        an hour of debugging into the wrong subsystem. *Two lessons, both cheap:* (1) **a hang at
        the client is not evidence of a hang at the server** — `~/Library/Logs/Claude/mcp.log` pairs
        every request with its response and timing, so read it *first*; it exonerated the server in
        one look. (2) **That log does NOT record the tool name or params** — so two calls seen at
        04:01 were *assumed* to be `add_note` from their response shape alone, and weren't, which
        manufactured a phantom "the client auto-retried" clue. **Three parties in this investigation
        each asserted a mechanism from a symptom without checking the premise under it.** Before
        reasoning *from* a fact, ask whether it was recorded or merely inferred.
        **Scope of #24 is now exactly the four hang vectors the investigation surfaced** — none
        caused the symptom; each is a genuine way the server could hang or corrupt itself:
        - [ ] **`embedder.py` `urlopen()` has no timeout** → a stalled Ollama (typically a **cold
              model load**) blocks **forever**. Exposed: `search_second_brain` *and* `git commit`
              (the pre-commit hook embeds). The one genuinely unbounded hang in the system.
        - [ ] **`_git` inherits stdin — which IS the JSON-RPC channel.** `capture_output=True`
              redirects stdout/stderr but not stdin, so a git/ssh child could read Desktop's
              protocol bytes and corrupt the session. Needs `stdin=DEVNULL` everywhere.
        - [ ] **`GIT_TERMINAL_PROMPT=0` doesn't cover ssh** (passphrase/host-key) — and this
              brain's remote is SSH. Needs `GIT_SSH_COMMAND="ssh -o BatchMode=yes"`.
        - [ ] **`TimeoutExpired` uncaught** → traceback instead of a clean failed-push report.
        Tests: reject every non-PARA `para_root` (`resources/test`, `resources/`, `../escape`,
        absolute) **immediately and side-effect-free**; git steps non-interactive + timeout-bounded;
        a stalled embed errors rather than hangs. **Does not touch the indexer's walk** —
        exclusion-by-placement (glossary/templates are excluded purely by not being PARA roots)
        must hold. → [docs/mcp-hardening.md](docs/mcp-hardening.md)
  - [ ] **INVESTIGATE — ship the brain as a Claude Code *plugin* (task #23).** Today a brain's
        AI surface is installed by hand in two unrelated ways: `install_skill.py` copies the
        `second-brain` skill into `~/.claude/skills/`, and the MCP server is **print-and-instruct**
        (we print a config stanza and ask the user to paste it into Claude Desktop — the deferred
        auto-insert above). Claude Code's plugin system looks like the packaging format that
        collapses both into one installable unit, so this is worth a real look before we build more
        install plumbing (and before #5 `add_note` adds another thing to register).
        **What we believe (unverified — web research 2026-07-13, via a subagent, not run locally):**
        an official Anthropic plugin marketplace is registered automatically, plus a community one;
        users browse/install via the `/plugin` command (Discover tab) and add marketplaces with
        `/plugin marketplace add`; a plugin can bundle **skills/slash commands, subagents, hooks,
        MCP servers, LSP servers, `bin/` executables on PATH, and default settings**. If that holds,
        one plugin could carry the skill *and* the MCP server *and* the pre/post-commit hooks.
        **Investigate, in this order — each answer gates the next:**
        - [ ] **Verify the mechanics first-hand.** Read the current plugin docs and actually install
              a plugin; confirm the bundle list above (especially: can a plugin ship an MCP server
              that Claude *Desktop* picks up, or only Claude Code? Desktop is the whole reason the
              MCP server exists — if plugins are Code-only, this replaces the *skill* install, not
              the Desktop registration, which is a much smaller win).
        - [ ] **Settle the impedance mismatch.** A plugin is a *shared, static* artifact; a brain is
              *per-user data at an arbitrary path*. The skill/server must be pointed at **this
              user's brain** (`install_skill.py` bakes the path in today). Can a plugin be
              parameterized per-user, or would we ship a plugin that reads a config/env var naming
              the brain root? This is the crux — if it can't find the brain, it can't work.
        - [ ] **Decide distribution.** Publish to a marketplace (a *generator* shipping one plugin
              that works against any generated brain) vs. have `create_second_brain.py` emit a
              **local** plugin directory the user installs from disk. The generator stance so far is
              detect-and-instruct, never silent auto-install — a marketplace listing is a bigger
              commitment (public artifact, versioning, support) and should not be assumed.
        - [ ] **Then decide whether to build it at all.** Acceptable outcome: *"not worth it, the
              two-step install is fine"* — write that down with the reason. This task is an
              investigation, not a commitment to ship a plugin.
        Constraint that does not bend: whatever we emit stays **local-first** and must not smuggle a
        devkit-internal dependency into a brain (the forbidden-refs invariant).
  - [x] **Write path — add a note to the brain from Claude Desktop (`add_note`).** DONE
        (2026-07-13, task #5). The design tension dissolved once it was stated properly: the
        alternative to committing was *writing the file and embedding it inline*, and **that**
        would have been the real bypass — a second ingestion path forked from the hooks, to be
        kept in step with them forever. `add_note` instead **commits**, because in this brain the
        commit *is* the embed (pre-commit embeds, post-commit hydrates), so the note is searchable
        at once through the one path that already exists. It also **pushes**: a note that lives
        only on the laptop that wrote it is invisible to every other client of the brain, so
        "searchable" would be a lie everywhere else — decisive once the brain is shared or served
        ([big-brain.md](docs/big-brain.md)). Everything hard about it came from writing to a repo
        a **human also uses**: it stages only its own file and commits by pathspec (an agent must
        never author a commit containing the user's in-progress work); on a non-fast-forward
        rejection — *expected* in the multi-client story — it rebases and retries, refuses to
        rebase over a dirty tree, and on any push failure reports honestly rather than rolling
        back (**the note is committed and searchable locally regardless — a failed push is not a
        lost note**); it pushes non-interactively (`GIT_TERMINAL_PROMPT=0`, or a credential prompt
        would hang a headless server forever instead of failing); the filename comes from a strict
        allow-list slug so a traversal payload in the title cannot escape, backed by a
        resolve-guard. **Create-only** — editing/deleting a note stays a human job. Shipped with
        two supporting read tools: `list_vault(para_root)` (browse the PARA structure, so the
        model files a note where it belongs instead of guessing) and `get_note_template()` (the
        vault's live template, so notes follow the house style the *user* set). Seven-tool surface;
        `check_mcp_server.py` grew a write suite (commit + push to a bare remote, searchable at
        once, duplicate/non-PARA refusal, title-traversal, dirty-tree non-interference, and the
        multi-client rebase via a peer clone), each assertion negative-tested. Prototype-first in
        the golden → vendored → template; CI 8/8 + MCP tier green.
        [docs/mcp-server.md §3.1](docs/mcp-server.md).
  - [x] **Concurrency layer 2 — in-place hydrate ([OQ-5](open-questions.md#oq-5)).**
        The MCP server is a **long-lived reader** holding a connection open while
        post-commit rebuilds fire — this is what made `hydrate`'s `unlink()`+rebuild
        a real hazard. Fixed: `hydrate_cache.py` keeps the existing table and rebuilds
        inside one explicit `BEGIN`/`DELETE FROM notes`/re-INSERT/`COMMIT` transaction
        (explicit BEGIN/COMMIT because `apsw` autocommits per-statement otherwise), so
        a WAL reader sees the old rows until commit, then the new set atomically — no
        teardown window. On any error it `ROLLBACK`s, so the previous good rows survive
        (the old `unlink()` destroyed the DB *before* validating dims). `doctor --repair`
        inherits it (same rebuild path). Golden `5604fb4`; verbatim → propagated, CI
        green (inode unchanged across runs; search+doctor green; bad-dim sidecar rolls
        back leaving all rows).
  - [ ] **Concurrency layer 3 — `flock` writer lock ([OQ-5](open-questions.md#oq-5)).**
        Serialize the *writers* (repair/hydrate/update_cache) against each other for
        the multi-statement critical sections SQLite transactions can't span, while
        WAL handles reader-vs-writer. Only if overlapping writes prove real once the
        server lands.
  - [x] **Expose the glossary via dedicated MCP tools — exact-match, no embeddings (task #20). BUILT 2026-07-12.**
        `list_glossary_terms` + `lookup_glossary_term` added to the emitted `mcp_server.py` (both
        `structured_output=False`): a mtime-cached `glossary/*.md` index (normalized slug + frontmatter
        `aliases:`), lookup returns the whole note with a lead-in-strip miss-fallback + `difflib`
        near-miss; no embedding, never touches `data/brain.db`. `check_mcp_server.py` extended to the
        four-tool surface + all six acceptance checks (list/exact/alias/normalized/near-miss/
        search-excludes-glossary/hot-add); MCP tier green, CI 8/8. Negative/security depth (embedding-free
        without `brain.db`, substrate disjointness) is #21.
        The vault's `glossary/` (a non-PARA sibling; [docs/glossary.md](docs/glossary.md)) holds
        short definitions of terms that recur across the whole vault. They are **deliberately kept
        out of semantic search**: a definition sits adjacent to *every* note that mentions the term,
        so its vector becomes a **hub** — it out-ranks the notes that actually reason about the topic
        (retrieval pollution) and bridges unrelated clusters in the mutual-kNN graph (graph
        pollution; see [glossary §3](docs/glossary.md), `resources/mutual-knn.md`,
        [embedding-separation](docs/embedding-separation.md)) — for ~zero payoff, because **semantic
        search is for when you can't name the thing and glossary lookup is the opposite** (the key is
        known — a dictionary op, not nearest-neighbour). Today a glossary note is reachable only via
        `get_note` with a full absolute path — i.e. undiscoverable. Add **two read-only tools** to
        the emitted `mcp_server.py`, beside `search_second_brain`/`get_note`:
        - **`list_glossary_terms()`** — every defined term name **+ declared aliases**, no
          definitions; cheap. **Load-bearing, not a nicety:** an exact-match tool is useless if the
          caller must guess the key — without a listing an assistant blind-guesses a filename, misses,
          and wrongly concludes the term is undefined. Description: call it **first** whenever unsure
          a term exists or of its exact name.
        - **`lookup_glossary_term(term)`** — exact match on the term's slug **and** its frontmatter
          `aliases:`, then return the **whole** (short) note — no snippeting. **Normalize before
          matching**: lowercase, strip punctuation (so `what is ablation?` works), collapse
          spaces/underscores → hyphens (`Ablation Study` ≡ `ablation_study`). **Aliases live in
          frontmatter** (`aliases: [ablation study, ablations]`), *not* code stemming — explicit
          beats clever. **On a miss, return near-miss suggestions** (prefix/substring hits first, then
          `difflib` fuzzy), never a bare not-found — forgives typos without making the match itself
          fuzzy. Description: **explicit lookup intent only** (`what is X` / `define X` / `what does X
          mean`); must **not** be called to add background colour to a conceptual question — point
          those at `search_second_brain`.
        - **Both descriptions** must state the glossary is *intentionally absent from
          `search_second_brain`* and reachable only via these tools. **This is where hub-prevention
          actually happens:** moving the notes out of vector space is undone if a model looks up every
          concept it meets, so the scope guard lives in the tool text.
        **Index:** scan `glossary/*.md` at call time, cache keyed on the directory `mtime` (a new
        term appears without a server restart); a few dozen tiny files — don't over-engineer.
        Canonical key = normalized filename stem; display name = the `# ` H1 (fallback: stem). Alias
        collisions: first-writer-wins, but surface them (a real collision is a vault bug worth
        knowing). **Verified (this task's verify-first, 2026-07-11):** the indexer is **already
        PARA-scoped on both write paths** — `embed_vault.py` (bulk) and the pre-commit
        `embed_staged.py` share `PARA_ROOTS = (projects, areas, resources, archive)` (the hook gates
        `parts[1] in PARA_ROOTS`), so `glossary/` is **not embedded** and the separation is structural
        — **no exclusion step needed**. The server object is `mcp = FastMCP("second-brain")`; both new
        tools register `@mcp.tool(structured_output=False)` (the same Claude-Desktop `outputSchema`
        fix the existing two carry — [mcp-server.md §11](docs/mcp-server.md)). **Non-goals:** no
        embedding / vector / BM25 of glossary notes; no change to `search_second_brain` or the
        sqlite-vec index; no snippeting (verbatim). **Acceptance:** (1) `list_glossary_terms()`
        includes `ablation`; (2) `lookup_glossary_term("ablation")` returns `glossary/ablation.md`;
        (3) `"Ablation Study?"` resolves (normalize + alias) to the same note; (4) `"ablasion"`
        returns a near-miss suggestion, not a bare fail; (5) `search_second_brain("ablation")` still
        returns **no** glossary notes; (6) a newly-added `glossary/*.md` is listable without a
        restart. **Emitted** into every brain (touches `mcp_server.py` → golden/template/manifest;
        behavioral coverage extends `check_mcp_server.py`, `mcp`-gated). **Depends on #19** emitting
        the `vault/glossary/` namespace; build defensively (missing/empty glossary → empty list /
        near-miss). A **G6 MCP** read-tool sibling of the deferred #5 write path. **Its
        negative/security coverage — search-excludes-glossary, glossary-tool-is-embedding-free,
        substrate disjointness, and the four-tool `tools/list` update — lands in task #21** (MCP
        coverage, Layer 2b).
- **Usage note:** the brain's value as a conventions oracle grows as it is
  populated with decision/convention notes — today it holds only the 4 system seed
  notes.

## Retrieval quality (backlog, surfaced 2026-07-04)
Dense-only search has a lexical blind spot — real at **scale** and for **exact-match**
queries (error codes, identifiers, API/function names, config keys, rare acronyms),
not at today's 5-note corpus. **Trigger to build: real recall failures observed on a
populated brain**, not a single example. (The prompting example that raised this —
"magic number" — was a **false alarm**: the actual brain ranks `magic-number.md` #1 at
0.26; Claude Desktop's "not in top 5" analysis was hallucinated. Verify claims against
`search_vault.py` before acting.)
- [x] **Hybrid lexical + vector search (SQLite FTS5) — task #3. COMPLETE — increments 1, 2, 3 (2026-07-11/12).**
      A `notes_fts` **FTS5** virtual table now lives beside the vec0 `notes` table in the *same*
      `data/brain.db` (built-in to SQLite, no new dep, no separate index file), hydrated by the
      **same** flow — `hydrate_cache.py` rebuilds both in its one atomic transaction; the
      incremental `update_cache.py --upsert/--delete` maintains both; FTS text (body + folded
      `tags:`) is read from the vault note at hydrate/upsert time via `note_view.canonical_body` +
      the new `note_view.frontmatter_tags` (**sidecar schema unchanged** — it stays a pure
      derived-embedding artifact). `search_vault.search()` fuses the vector KNN and the BM25
      (`ORDER BY rank`) leg with **Reciprocal Rank Fusion** (`K_RRF=60`) and returns
      `(source_file, score)` (higher = better) — so the CLI, the skill (`query.py`, print-shape
      preserved), and the MCP server (`score` key) all get hybrid for free. The FTS query is
      sanitized (tokenize → quote → OR-join) and the lexical leg degrades gracefully to
      vector-only on a stale/absent `notes_fts`. **Verified** in the golden (real Ollama: paraphrase
      + exact-token both rank #1; incremental upsert/delete; graceful fallback); CI 8/8; opt-in
      semantic tier 5/5 (rank-based, incl. an exact-token case) + MCP tier green.
      **INCREMENT 2 BUILT 2026-07-12** — the deferred **#12 Half-B config surface**, now justified by
      a genuinely *situational* query-time toggle. New `config/features.toml` (`hybrid_search = true`,
      `rrf_k = 60`) read by new `scripts/features.py` with `embedder.py`'s precedence — env
      (`SECOND_BRAIN_HYBRID_SEARCH=1|0`, `SECOND_BRAIN_RRF_K=<int>`) > config > default, so a
      pre-config brain still searches (hybrid on, K=60). `search_vault.search()` now runs the vector
      leg always and adds the lexical leg only when `hybrid_search()` (vector-only still flows through
      RRF → same order, comparable score); `K_RRF` module constant removed in favour of `rrf_k()`.
      `doctor.py` surfaces the active mode + K. Emitted **verbatim** (default is identical for golden
      and brain — unlike `embedder.toml`) → manifest/vendor/template/CI. **Verified** live on real
      Ollama: default hybrid ranks `sqlite-vec.md` #1, `SECOND_BRAIN_HYBRID_SEARCH=0` reproduces the
      pre-hybrid blind spot (buries it at #2), `rrf_k` reshapes scores; features precedence unit-checked;
      CI 8/8, semantic tier 5/5, MCP tier green.
      **INCREMENT 3 BUILT 2026-07-12 — the payoff, and a situational finding.** `tools/ablation.py`
      §4 reproduces the shipped `search_vault.search()` path (vector leg + BM25 lexical leg over an
      in-memory `notes_fts` — same body+tags the brain indexes, reusing `_fts_match_query` — RRF-fused
      K=60, pool=20) and measures `hybrid_search` on/off on both corpora. **IT (hardened, adjacent):**
      hybrid lifts every metric — recall@1 0.675→0.725, recall@5 0.975→**1.0**, MRR/nDCG +0.04.
      **bench (far-apart):** hybrid slightly *hurts* (recall@1 0.90→0.83) — dense already wins, the
      lexical leg adds cross-domain noise. So hybrid is genuinely **situational** (net win for an
      IT-heavy brain, a drag on cleanly-separable domains) — the textbook justification for the #12
      Half-B **toggle** (default on) over hardcoding. Sanity: §4 vector-only reproduces §1/§2/§3's
      nomic baseline exactly. Recorded in [benchmark-corpus §6d](docs/benchmark-corpus.md) +
      quality-features §4/§5. Devkit-side only (ablation.py not emitted), Ollama-gated, out of the
      hermetic gate; CI 8/8 green, nothing emitted. Fold-`tags` done; **no** manual
      `keywords:` section (declined — real authoring cost, marginal gain). Highest-ROI lever for
      exact-token IT queries — see [docs/retrieval-quality.md §2](docs/retrieval-quality.md).
- [x] **Use nomic task prefixes — PREREQUISITE for #8, DONE 2026-07-08.** Threaded a
      `task` arg through `embed(text, task="document"|"query")`, mapped to
      `search_document:`/`search_query:` **only in the Ollama backend** (`test` backend
      ignores it → committed fixtures/CI byte-unaffected, no manifest change). Callers:
      `embed_staged`/`embed_vault` → document, `search_vault.search()` → query. Two
      comparison modes, and the prefix pair is **not** always query-vs-document:
      **asymmetric** query↔note (search — `search_vault`, skill, MCP); **symmetric**
      note↔note = `search_document:` on **both** sides (auto-linking KNN #8, clustering).
      Verified on real Ollama (document vs query vectors differ, bad task raises); golden
      `44ea6f6`, CI 6/6 green. **Real brain (`~/second-brain`) upgraded + re-embedded**
      (`update_brain` → `embed_vault` → `hydrate`): retrieval improved and *separation*
      widened — `"magic number"` top-1 0.238 → **0.124** with #2 at 0.49. That separation
      is exactly what #8's `t_max`/hysteresis calibrate on, so the distance scale is now
      final. Full design in [docs/retrieval-quality.md §1](docs/retrieval-quality.md);
      decision captured as a brain note (`resources/nomic-embedding-prefixes.md`).

## Test corpus (task #16, BUILT 2026-07-09): seed + tear down a large multi-topic note set
- [x] **A devkit testing utility: populate a target brain with a large, realistic note corpus,
      and cleanly remove it (notes + every derived remnant). (task #16; BUILT 2026-07-09.)** For exercising a brain
      at realistic scale — auto-link thresholds, retrieval quality, benchmarking, CI, dogfooding
      — without hand-authoring notes each time. **Separate from #15** (the ablation-benchmark
      corpus); #15 may reuse this corpus if the topic spread suits. Everything here is
      **devkit-side** — the corpus and scripts live in the devkit and are **never emitted** into
      a generated brain.
      - **Source corpus — authored, tracked, NOT emitted.** ~100 realistic Markdown notes under a
        **new non-emitted** dir `tests/seed-corpus/{topic}/` — **10 IT topics × 10 notes** — named
        `seed_{topic}_{short-description}.md` so every test artifact is identifiable by the `seed_`
        prefix. Deliberately **outside** the emitted `seeds/` tree (which `seed_vault` copies into
        every real brain) so it can never pollute a generated brain; add the dir to
        `emit-manifest.toml`'s exclude set and keep the partition + structural-diff green.
        **Topics — 10 deliberately distinct clusters (ones the user has shown interest in):**
        AI / LLMs (condensed: embeddings, semantic search, RAG, prompting) · AI agent harnesses
        (agent orchestration, tool-use loops, subagents, MCP) · Go (golang) · Rust · TypeScript ·
        SQLite / embedded & vector databases · knowledge-management (PARA/Obsidian) · git
        automation & commit telemetry · CI & testing · web-app architecture. Chosen for **topical
        distance** (three separate languages + an AI-vs-agent split + distinct infra topics) so the
        corpus forms real, separable clusters — the earlier draft was too AI-adjacent and would
        collapse into one blob. **Real substance** per note (a few coherent paragraphs) so
        embeddings cluster genuinely.
      - **Install script (`tools/`, copy → commit).** Copies the corpus into a **target brain's**
        `vault/resources/` — the target is a **path argument**, so one tool serves CI, the internal
        `sandbox/`, or an external/real brain — then commits the added notes (the brain's hooks
        embed + hydrate them). Idempotent.
      - **`create_second_brain.py --seed-test-corpus` switch.** Generating a brain with this flag
        *also* copies the 100 notes into the new brain's `vault/resources/` at creation — a one-shot
        "give me a populated test brain."
      - **Teardown script (`tools/`, remove → commit, no remnants).** Removes **all** corpus
        artifacts from a target brain: the `vault/resources/seed_*.md` notes (committed removal),
        their derived `.embed.json` sidecars, and their `data/brain.db` cache rows (`update_cache
        --delete` or re-hydrate) — then commits the removal, leaving the brain byte-clean of the
        corpus. Identify artifacts by the `seed_` prefix (no manifest needed). Idempotent.
      **Built:** corpus committed (`tests/seed-corpus/`, 100 notes, `119f7d6`); `tools/test_corpus.py`
      (install/remove, target-path driven) + `create_second_brain --seed-test-corpus` (`9de9a8c`).
      Verified end-to-end on a throwaway `test`-backend brain: create+seed embeds 100 notes and
      searches; remove leaves **zero remnants** (notes, sidecars, cache rows) and is idempotent; CI
      7/7 green (default `create_second_brain` unchanged). **Cluster check (real Ollama):** real but
      *moderate* topic structure — 69% nearest-neighbour topic purity, intra 0.329 < inter 0.382;
      distinct topics (CI/git/KM/web) cohere strongly, adjacent ones blend (rust↔golang, the two AI
      topics) — a realistic "everything's somewhat related" corpus, good for stressing the auto-link
      thresholds. Crisper separation would need less-adjacent topics or longer/more-anchored notes.

## Test-corpus clustering — improve separation (task #17, DONE 2026-07-09)
- [x] **Regenerated the #16 corpus with longer, more topic-anchored notes to raise topic
      separation, then re-measured.** (task #17) The #16 corpus formed only *moderate* clusters
      (69% nearest-neighbour purity; rust↔golang + the two AI topics blended). Applied **lever #1**:
      rewrote all 100 notes ~3× longer (45→148 words avg), packed with topic-specific vocabulary and
      steered away from generic cross-topic terms (the two adjacent pairs got explicit
      "stay-in-your-own-jargon" guidance). Same 10 topics + `seed_{topic}_{desc}.md` names + the
      install/remove tooling — **only the note bodies changed** (titles + frontmatter byte-untouched;
      `git diff` shows zero changes to `# ` / `tags:` lines). Re-ran the Ollama cohesion check:
      **purity@1 69%→79%, purity@5 55%→75%, separation +0.053→+0.072** (`search_document:`); with
      **lever #2** (nomic's `clustering:` prefix, for the analysis only — the brain keeps
      `search_document:`) **84% / +0.086**. rust jumped 4/10→8–9/10 and the two AI topics 6→8–9.
      The lone laggard (golang, 5/10) is **concept-name collision** across sibling topics
      (`generics`→`typescript_generics`, `interfaces`→`typescript_interfaces`, etc.), semantically
      correct and a floor set by topic design — the ground-truth-label reframe absorbs it. Full
      before/after table + interpretation in [docs/test-corpus-clustering.md](docs/test-corpus-clustering.md).
      Raises the corpus's value for #15/#12/#13. **These are devkit-side seed files, not emitted —
      CI unaffected.**

## Review test-corpus clustering (task #18, DECIDED 2026-07-10)
- [x] **Reviewed the post-#17 cohesion and chose the separation strategy.** (task #18) **Decision:
      grade the corpus *supervised* — the 10 topic folders are ground-truth labels, so #12/#13
      measure how well retrieval/auto-linking recovers the *known* topics; do NOT chase higher
      purity.** Levers #3/#4 (more notes per topic, merging adjacent rust↔golang / AI topics) were
      rejected: they game the purity metric and make the corpus *less* realistic, and the residual
      blend is semantically-correct concept-name collision (a floor set by topic design), not a
      note-quality defect. The moderate, everything-adjacent separation is the honest stress test
      for the auto-linker's `t_max` + mutual-KNN. **Division of labor with #15:** the #16/#17 IT
      corpus carries the *supervised* benchmark + the *adversarial* (everything-adjacent) stress
      test; the #15 topically-diverse corpus (far-apart domains) carries the *unsupervised*
      topic-count / plateau analysis where clean self-sorting matters. Unsupervised separation of the
      *IT* topics (levers #3/#4) is deferred to only-if-a-plateau-demo-on-IT-topics is specifically
      needed. No code — see [docs/test-corpus-clustering.md](docs/test-corpus-clustering.md).

## Benchmarking & feature toggles (backlog): quantify each quality enhancement
Goal: measure the **relative** retrieval/graph-quality payoff of each enhancement by
turning it on/off and benchmarking — an ablation study — so we know which features
actually earn their keep. Both tasks below are exploratory (**may not become a shipped
requirement**); they also produce the material for a future GitHub tutorial.

- [x] **Build a large, topically-diverse benchmark corpus — the unsupervised / calibration
      dataset.** (task #15; the shared dataset prerequisite for the ablation + calibration work.)
      **BUILT 2026-07-10:** 200 notes (10 domains × 20, `tests/bench-corpus/`), a 30-query labeled
      eval set (`tests/bench-corpus/queries.jsonl`, all 10 domains, every reference resolves), and
      corpus-driven `test_corpus.py` (`--corpus bench`) + `create_second_brain --seed-bench-corpus`
      (verified end-to-end on a `test`-backend brain: 200 install → clean remove; default seed corpus
      still installs 100; CI 8/8). **ACCEPTANCE PASSED (real Ollama, 2026-07-10):** purity@1 **98%**
      / @5 96%, separation **+0.136** (intra 0.267 vs inter 0.403 — the confident `t_max ≈ 0.30` the
      IT corpus lacked); every domain 18–20/20 incl. the acting/dancing/music-theory trio (18/19/20);
      retrieval **top-1 27/30, top-5 30/30** (misses are same-domain siblings); `autolink.py` writes
      clean within-cluster graphs at `t_max≈0.30`. Full results in
      [docs/benchmark-corpus.md §5](docs/benchmark-corpus.md). Unblocks #12/#13 and the real-brain
      auto-link `--apply` calibration (below).
      Per the [[task #18]] decision, this is the **complement** to the #16/#17 IT corpus: where the
      IT corpus is deliberately *everything-adjacent* (the supervised + adversarial stress test),
      #15 is deliberately **far-apart domains** so the embedding space has clean, separable
      **cluster structure** — the *unsupervised* topic-count / `t_max`-plateau case, and the first
      corpus on which auto-link `--apply` is actually illuminating. Devkit-side and **never emitted**
      (like #16). Design / subtasks (**decisions locked 2026-07-10**: size 10×20, query set authored
      in #15, generalize `test_corpus.py`):
      - **Topics & size.** ~**10 deliberately distant domains**: cooking, personal finance,
        distributed systems, history, biology, music theory, astronomy, **acting — framed as *how to
        teach acting***, law, **dancing — framed as *how to teach dancing***. Minimal shared
        vocabulary across domains, unlike the IT corpus. **Heads-up:** music-theory / acting /
        dancing are all performing-arts-adjacent — steer each with its own pedagogy/jargon (the #17
        lesson) and watch that group in the cluster check, like rust↔golang in #16. ~**20
        notes/topic (~200 total)**: denser clusters than #16's 10/topic (clustering-doc lever #3) so
        a single-linkage sweep shows a **clear plateau** at the intended topic count.
      - **Note bodies.** Apply the #17 lesson — ~120–150 words each, packed with topic-specific
        vocabulary, steered off generic cross-topic terms. **Committed static files** (not a random
        generator) so embeddings + measurements are byte-repeatable. **Authoring rule (from the
        template review, 2026-07-10):** when a performing-arts note must touch music, describe the
        *performer's physical reaction* — weight, suspension, rebound, attack, syncopation of steps —
        **not** music-theory vocabulary (`metronome`, `staccato`, `legato`, `downbeat`, `phrase`),
        which pulls the dancing cluster toward music-theory. (Caught + fixed in the dancing
        `musicality` template note.)
      - **Layout & tooling (reuse #16).** A new non-emitted dir `tests/bench-corpus/{domain}/` with
        `bench_{domain}_{desc}.md` names (a distinct `bench_` prefix so teardown targets it
        independently of #16's `seed_`). **Generalize `tools/test_corpus.py`** to be corpus-dir +
        prefix driven so one tool installs/removes either corpus into a target brain's
        `vault/resources/` (idempotent, commit-through-hooks). **No manifest change needed** —
        confirmed like `tests/seed-corpus`, the partition check only walks `tests/golden/`, so
        `tests/bench-corpus/` is invisible to CI; committing the notes keeps every gate green.
      - **Labeled query set (the benchmark ground truth).** Author a small committed
        `tests/bench-corpus/queries.jsonl` (or similar) mapping each query → its expected note(s),
        alongside the folder/topic labels ([[ground-truth-labels]]). This is the piece #12 consumes:
        the topic folders give the supervised labels, the query set gives retrieval relevance.
        **(Decided 2026-07-10 — authored here in #15, since #15 *is* the dataset; #12 consumes it.)**
      - **`create_second_brain` flag.** Generalize `--seed-test-corpus` (or add `--seed-bench-corpus`)
        so a brain can be born pre-seeded with this corpus.
      - **Acceptance (real Ollama, opt-in, out of the hermetic CI gate).** (1) Embeds; the §2.3
        single-linkage / union-find sweep shows a **clear plateau** at ~10 topics (the separability
        the IT corpus lacks). (2) `autolink.py --calibrate` reports a **confident global `t_max`** (a
        real distance gap / high separation score) — vs the IT corpus's no-clean-cut. (3) Each
        labeled query ranks its expected note(s) in top-k under threshold. (4) `autolink.py --apply`
        on a seeded brain draws an **illuminating** graph (distinct clusters, sparse cross-topic
        edges) — the first meaningful run of the deferred #8 write path.
      - **Docs.** Author `docs/benchmark-corpus.md` at build time (design + calibration results),
        cross-linked from [docs/auto-linking.md §2.2/§2.3](docs/auto-linking.md) and the
        [test-corpus clustering doc](docs/test-corpus-clustering.md).
      **Unblocks:** #12/#13 (the ablation dataset), #8 final `t_max`/hysteresis calibration **and the
      deferred `autolink.py --apply`** (below), #14 tutorial screenshots. Not started.
  - **Reminder — run the deferred auto-link `--apply` here.** #8's write path is built and
    dry-run-verified, but **deliberately not applied** to any brain: on the ~7 homogeneous real-brain
    notes it draws a near-complete graph (nothing to discriminate) and churns every committed note.
    This diverse corpus is the first place `t_max` calibration (§2.2) then `autolink.py --apply`
    produces an illuminating, sparse cross-topic graph worth committing / viewing in Obsidian's
    graph view.
- [x] **Catalog every second-brain quality-enhancement feature.** (task #13; DONE 2026-07-10.)
      Produced [docs/quality-features.md](docs/quality-features.md): 10 features, each with
      what/why, mechanism, **cost class** (index-time = re-embed on flip vs query-time = free),
      intended `config/features.toml` toggle key, status, and a tutorial-ready before/after —
      grounded in the real code (`note_view.canonical_body`/`content_hash`, `embedder.py` task
      prefixes, `autolink.select_links` top-N∩mutual∩`t_max`). Built: canonical view, task
      prefixes, `content_hash` gate, embedder backend; in progress: auto-linking; planned: hybrid
      FTS5 (#3), chunking (#7); candidates: vector whitening, clustering-embedding, line-count
      guard. Feeds the #12 ablation (the toggles) and the #14 tutorial (the worked examples).
      Original starting set (the catalog completed / corrected it):
      - **Canonical substance view** — embed the body, not metadata; index-time. *(built, #8)*
      - **Nomic task prefixes** — `search_document:`/`search_query:`, asymmetric for search
        & symmetric for linking; index-time (re-embed on flip). *(built, #3)*
      - **Hybrid lexical+vector search** — FTS5/BM25 + Reciprocal Rank Fusion; query-time.
        *(planned, #3)*
      - **Auto-linking `related_auto:`** — vector-KNN graph edges; offline pass, graph
        quality (not retrieval). *(in progress, #8)*
      - **`content_hash` no-op gate** — skip re-embed of unchanged substance; index-time
        efficiency. *(planned, #8)*
      - **Candidates:** long-note / PDF chunking + multi-vector (#7); note-hygiene
        line-count guard. Each entry should be tutorial-ready (a made-up before/after
        example illustrating the enhancement). Local-first, docs-only task.
- [~] **Global feature toggles + ablation benchmark harness.** (task #12)
      **INCREMENT 2 BUILT 2026-07-11 — the index-time ablations + a model-parametrized, memoized
      embedder.** `tools/ablation.py` now runs three sections on the #15 corpus: §1 task prefix
      (query-time, increment 1), §2 canonical view ON/OFF, §3 embedder model swap
      (`nomic-embed-text` vs `mxbai-embed-large`, each with its native retrieval scheme). Each
      index-time config re-embeds; a process-wide `(model, text)` memo dedupes shared passes.
      **Results ([benchmark-corpus §6](docs/benchmark-corpus.md)):** canonical view is
      retrieval-**flat** (Δ negligible — its payoff is graph legibility, not search); the model
      swap is a **wash** on far-apart domains (recall@1 tie; on the IT corpus it *looked* like a win
      but **#22 later showed that ranking flips with query phrasing — no robust winner**); the symmetric
      prefix measurably hurts (recall@1 0.867). **Meta-finding:** #15
      *saturates* the metrics (recall@5 ≈ 1.0) — feature-separation ablations want the adversarial
      IT corpus (#16/#17) or the real brain, so a follow-on is to author a `queries.jsonl` for the
      IT corpus and re-run. **DECISION — Half B deferred:** no built index-time feature is
      *situational* (all are always-on wins or immeasurable here), so a per-brain
      `config/features.toml` toggle for them would be **dead config**; the config surface waits for
      the first genuinely optional feature — #3 hybrid FTS5 (`hybrid_search` on/off) or #7 chunking.
      Devkit-side only (Ollama-gated, out of the hermetic gate); `sys.dont_write_bytecode` keeps the
      harness from dropping a `__pycache__` into the tracked `template/` tree; CI 8/8 green.
      **INCREMENT 1 (2026-07-10) — the harness + metrics engine (`tools/ablation.py`).** Runs the
      #15 corpus + `queries.jsonl` through real Ollama and reports **recall@1/@5, MRR, nDCG@5, mean
      top-1 distance, mean rank-1 margin** per feature config; Ollama-gated (SKIP + exit 0 when
      absent, out of the hermetic CI gate, like `check_semantic_retrieval`). First ablation — the
      **nomic task prefix** (query side, no note re-embed): on this cleanly-separable corpus the
      prefix barely moves *ranking* (both correct schemes recall@1 0.90) but the **symmetric scheme
      measurably hurts** (recall@1 0.867) and the correct `search_query:` gives **tighter distances**
      (0.238 vs 0.263) — separation, not recall, is where prefixes pay, matching the real-brain
      finding. **Follow-ons (rest of #12):** a per-brain `config/features.toml` wiring the toggles
      into the emitted scripts, and the **index-time** ablations that force a re-embed (canonical
      view, embedder/model swap — the [embedding-separation §6](docs/embedding-separation.md)
      comparison, chunking) — matrixed/cached because each re-embeds the corpus. Original spec:
      Make each feature
      in the #13 catalog a **global feature toggle** (config-driven, following
      `embedder.py`'s env-override > `config/…` > default pattern — e.g. a `[features]`
      block or `config/features.toml`), then build an **ablation harness** that runs a
      **labeled eval set** (queries → expected relevant notes) against the brain under each
      toggle configuration and reports IR metrics (recall@k, MRR, nDCG, top-1 distance +
      **margin/separation**) so each feature's contribution is quantified. **Also the vehicle
      for comparing embedding models** (swap the `embedder.py` backend, re-score on the #15
      corpus, pick the winner) — the practical way to pull closely-related IT topics apart, see
      [docs/embedding-separation.md §6](docs/embedding-separation.md).
      **Key design nuance — two toggle classes:** **index-time** toggles (prefixes,
      canonical view, chunking, `content_hash`) change the *stored* vectors, so flipping one
      forces a **full re-embed** of the corpus (expensive — matrix/cache the runs);
      **query-time** toggles (RRF fusion, `k`, link thresholds) flip for free per query. The
      harness must re-embed per index-time config but sweep query-time configs cheaply.
      **Hard dependency — a real dataset.** Meaningful ablation needs a **large, well-designed
      note corpus** + a labeled query set; today's ~7 notes make every metric noise (the same
      "thresholds are meaningless at this scale" caveat as #8). So this task **includes
      authoring a substantial made-but-realistic evaluation corpus** across the PARA roots —
      which **doubles as the GitHub-tutorial material** (each enhancement illustrated with a
      worked example). Opt-in / local-first (needs Ollama + the corpus), **not** in the
      hermetic CI gate; emits nothing that perturbs the byte-exact `test`-backend diff.
      Depends on #13 (the catalog) and benefits from #3/#8 being built so there are real
      toggles to compare.
- [x] **IT-corpus query set + `--corpus` flag — the hard-topic ablation bed (task #22; DONE +
      hardened 2026-07-11).** Built `tests/seed-corpus/queries.jsonl` + a `--corpus {bench,it}` flag
      on `tools/ablation.py`, then hardened the query set to 40 lay-phrased queries (4/topic, each a
      single defensible expected note; per-query diagnosis confirms the misses land on *designed*
      adjacencies — KM/git/sqlite intra-clusters + golang↔rust cross-topic bleeds — not mislabels).
      **The hardening exposed a methodology finding that corrects the first read:** across three
      wordings of the *same* corpus the nomic-vs-mxbai ranking **flips** — mxbai won the concept-named
      set (recall@1 0.833→0.967, +13pp), nomic won a hyper-detailed set (0.975 vs 0.900), and the
      shipped lay-phrased set (recall@1 **0.675**, recall@5 0.975 — real headroom) is a **tie**. So
      the embedder delta is **within query-phrasing variance** at this scale — the earlier "mxbai is
      the biggest separation lever" was a phrasing artifact, **not** a robust win; ranking embedders
      would need a larger/held-out set or the real brain. Stable across all three sets: **symmetric
      prefix hurts, canonical view flat.** Full write-up [benchmark-corpus §6b/§6c](docs/benchmark-corpus.md).
      Devkit-side only, nothing emitted, CI 8/8 green. Completes the #12 follow-on; the hardened set
      is the honest bed for **#3 hybrid FTS5** (these lay/exact-token queries are dense search's blind
      spot).

## Outreach (backlog): a Medium post on creating a second-brain
- [ ] **Write a Medium post: "How to create your own second-brain."** (task #14) A public,
      end-to-end walkthrough of standing up a working brain with the devkit for a general
      developer audience: `create_second_brain.py <path>` → the README install checklist
      (`pip install`, Ollama + `ollama pull nomic-embed-text`, `self_test.py` /
      `doctor.py`) → everyday loop (write a note under a PARA root → commit → the hook
      embeds + hydrates → semantic search) → reaching it from any project via the
      `second-brain` skill (and the Claude Desktop MCP option) → optionally the
      `--remote` git-backed variant. **Respect the hard invariant:** describe the product
      and the public generator only — **zero devkit-internal references** (no
      `ai-project-status`, etc.). Distinct from the GitHub *tutorial* in #12/#13 (which
      illustrates individual quality enhancements with worked examples); the Medium post is
      the "get started from scratch" narrative and can reuse that made-up corpus for
      screenshots. Not a code task — a writing deliverable. Not started.

## Ingestion (backlog): PDF segmentation + embedding
- [ ] **Segment & embed a PDF into the brain.** (task #7) Support ingesting a PDF as a
      searchable source, not just Markdown notes. The hard part: a PDF is long, so it must
      be **segmented into passages** (chunks) and **each chunk embedded** — this breaks the
      brain's core **"one note = one vector"** assumption and forces real design work:
      - **Chunking strategy** — by page / paragraph / fixed token-window with overlap;
        chunk size vs. retrieval quality; keep page/offset for locating the passage.
      - **Multi-vector-per-source schema change** — the cache keys rows on `source_file`
        (PRIMARY KEY, one row/note); PDF chunks need many rows per file, e.g.
        `(source_file, chunk_id)` + the chunk's text/page span. Touches `hydrate_cache.py`,
        `update_cache.py`, `search_vault.py`, and the sidecar format (one `.embed.json`
        holding many chunk vectors). Reconcile with hybrid FTS5 (task #3).
      - **Text extraction dependency** — a PDF parser (`pypdf` / PyMuPDF / `pdfplumber`)
        kept an **isolated optional dependency** (like `requirements-mcp.txt`) so core +
        CI stay lean/stdlib-only.
      - **Storage** — PDFs are binary and can be large: commit the PDF (git, maybe LFS) or
        keep it out and index only? Store extracted text/Markdown alongside? Sidecar holds
        vectors + spans + page refs.
      - **Search UX** — a hit points to the PDF **+ page/offset (+ chunk text)** so the
        user/AI can open the passage; a `get_note`-equivalent for a PDF chunk (MCP/skill).
      - **Document it in the emitted (brain) `README.md`** — a "Add a PDF" section: how to
        ingest a PDF, the optional parser install, where PDFs live, and how chunk hits read
        in search. Ships into every generated brain (the golden README → cleaned template).
      Chunking also helps **long Markdown notes** (the same one-note-one-vector weakness the
      line-count guard hints at), so design it source-type-agnostic. Substantial — will
      likely want its own `docs/` design doc when picked up. Not started.

## Marked-block helper: one splice utility — do BEFORE #8/#9
- [x] **Extract a single reusable "splice a marked block" helper, then reuse it.**
      (task #10; BUILT 2026-07-08) New emitted brain script `scripts/marked_block.py`
      exposes `has_block` / `splice_block` / `remove_block` with **markers passed in as
      arguments** (shares code, not tags). `splice_block` replaces the body in place
      (append if absent) and is **idempotent** — re-splicing an unchanged body returns
      byte-identical text; a lone marker raises `MarkedBlockError` (refuse a malformed
      doc, per the plan). **Proved by refactoring `install_skill.py --nudge` onto it with
      no behavior change:** the install→idempotent→uninstall round-trip was verified
      byte-for-byte against a throwaway HOME, and `splice_block`'s append output
      byte-matches the old inline logic. **Home decided:** an emitted `scripts/` module
      the brain scripts (`install_skill.py`, and #8's auto-linker) import via the
      established `sys.path.insert(parent)` + `from marked_block import …` convention;
      #9's devkit-tool `update_brain.py` will reuse it from `template/scripts/`. Manifest
      `verbatim` 34→35, re-vendored golden (55 files), rebuilt `template/` (40 files),
      **CI green (6/6; structural diff 46/46, 16 emitted scripts compile)**. Unblocks #8 and #9.

## Auto-linking (in progress): vector-derived Obsidian note links
- [~] **Materialize vector neighborhoods as Obsidian-visible links.** (task #8)
      **Foundation landed 2026-07-08 — embed substance, not metadata (§1/§4.1).** New
      emitted verbatim script `scripts/note_view.py` exposes `canonical_body(text)`: body
      only (leading YAML frontmatter stripped), `\n`-normalized, blank lines around the
      fences dropped, one trailing `\n` pinned → byte-identical across machines.
      `embed_staged.sidecar_bytes` now embeds `canonical_body(text)`, so the pre-commit hook
      **and** `embed_vault` (which reuses it) are substance-only — verified a frontmatter
      change no longer moves the vector, so writing `related_auto:` later can't feed back
      into the embedding (the rich-get-richer loop is broken at the source). Committed test
      fixtures regenerated; manifest verbatim 35→36, golden re-vendored (56), template
      rebuilt (41), **CI 6/6 green (structural diff 47/47)**.
      **KNN calibration tool landed 2026-07-08** — `scripts/autolink.py` (emitted verbatim,
      read-only) computes each note's neighbourhood from the vectors in `data/brain.db` (no
      re-embed) reusing the vec0 cosine KNN, with `--k` / `--threshold` preview + a distance
      summary. First run on `~/second-brain` (7 notes) showed the vectors behave well but the
      corpus is **one topical cluster** with no clean gap for a global `t_max` — confirming a
      distance cut alone is insufficient at small scale (top-N + mutual-KNN carry it) and that
      a meaningful threshold needs the larger, diverse corpus from #12/#13. Full findings +
      provisional defaults (`t_max≈0.45`, top-N 3–5, mutual-KNN) in
      [docs/auto-linking.md §2.1](docs/auto-linking.md).
      **Write path landed 2026-07-08** — `autolink.py` gains `select_links` (top-N ∩
      mutual-KNN ∩ `t_max`) and `apply_links` (frontmatter-aware `related_auto:` block via the
      [[marked-block splice helper]]; idempotent; removes its block when empty; never touches
      a hand-set `related:`/inline link — §3 namespace partition), plus a **dry-run diff**
      default and `--apply`. Built + dry-run-verified on `~/second-brain` (mutual-KNN pruned
      `magic-number` from 4 candidates to 1 reciprocal link) but **deliberately not applied**
      — see the [[task #15]] reminder (a near-complete graph on the homogeneous corpus).
      **Obsidian-format acceptance check landed 2026-07-08 (§5)** — `tools/check_autolink_format.py`
      (ci.py gate 4/7): asserts `related_auto:` emits **quoted** wikilinks in a YAML list (the
      only form Obsidian graphs), independently + negative self-test, hermetic (lazy `db`
      import → no sqlite-vec); verified it catches a bare-wikilink regression.
      **`content_hash` no-op gate landed 2026-07-08** — `note_view.content_hash` (SHA-256 of
      the canonical body) is stored in each `.embed.json` **sidecar** and `write_sidecar`
      skips the re-embed when substance + backend are unchanged (`force` bypass for `doctor
      --repair`); so unchanged notes never re-embed and a frontmatter-only `related_auto:`
      edit no longer churns the index. Stored in the sidecar (local gate) not frontmatter —
      frontmatter placement (cross-machine, big-brain A) deferred to dodge the §7 pre-commit
      write-back tension; recorded in [docs/auto-linking.md §4](docs/auto-linking.md). CI 7/7.
      **Still to do:** (1) **hysteresis** in `select_links` (add `t_hi`/drop `t_lo` band, needs
      the note's prior link set — deferred, lower priority); (2) final `t_max`/hysteresis
      calibration once the #12/#13/#15 corpus
      exists. Design detail:
- [ ] **(design, unchanged below)** A pass
      computes each note's nearest neighbors (KNN over the vectors already in
      `data/brain.db` — no re-embed to link) and writes them into a **managed frontmatter
      block** `related_auto:` as **quoted wikilinks** (`- "[[note-a]]"`), which Obsidian's
      link-type properties render as real **graph edges** (a **hard requirement** — add a
      build-time check, don't trust the client version; the `outputSchema`/Desktop lesson).
      Two features: (a) auto-linking, (b) **manual-link preservation** — a hand-set link
      (`related:` / inline `[[…]]`) is **never** touched; the auto-pass reads/writes *only*
      its own `related_auto:` block (namespace partition, like `--nudge`'s marked region).
      **Core invariant — embed *substance*, not *metadata about* the content** (author-
      agnostic: AI writes substance too; the discriminator is content vs. bookkeeping, and
      `related_auto:` is metadata *derived from the embedding*). Today `embed_staged.py`
      embeds the **whole file**, so a naive auto-linker would form a **rich-get-richer
      feedback loop** (links → vector drift → stronger links). Fix: embed a **canonical
      substance view** (body only, frontmatter stripped). **`content_hash` no-op gate:** a
      **byte-consistent** crypto hash (SHA-256 — a *change* detector, cross-machine stable,
      the deliberate inverse of the non-reproducible neural vector) of the canonical body,
      stored in frontmatter (committed → travels for [big-brain A](docs/big-brain.md));
      unchanged hash → **skip re-embed**, which kills both the loop and the OQ-3 neural-noise
      churn. Stability rules (threshold + top-N + deterministic order + hysteresis) keep
      committed-note churn down. Composes with #3 (FTS5 lexical neighbors) and #7 (multi-
      vector sources need a neighbor-aggregation rule). Full design in
      [docs/auto-linking.md](docs/auto-linking.md). **Before** Postgres/big-brain Approach B
      (local-first, no new service).

## Glossary (task #19, backlog): a controlled-vocabulary term layer for the brain
- [~] **Give every generated brain a controlled-vocabulary glossary — one atomic note per
      pre-identified term, linked from wherever the term is used.** (task #19) **INCREMENT 1 BUILT
      2026-07-12** — namespace + convention + `glossary_new.py` + docs + SPEC + harness emit into
      every brain (see the Namespace/Embedding-exclusion/New-term/Docs/Contract/Harness subtasks
      below, all done); embedding-exclusion verified free in the golden (embed_vault/hydrate/search
      ignore `glossary/`, zero sidecars, no `doctor` drift); CI 8/8. **Unblocks #20/#21.**
      **INCREMENT 2 BUILT 2026-07-12** — `scripts/glossary_scan.py`, the on-demand body-linker: report
      by default / `--apply` inserts `[[term]]` at the first unlinked occurrence per note, idempotent
      (skips already-linked terms + text inside existing wikilinks), dumb exact-phrase match
      (stemming/aliases/code-fence-skip deferred per §4); verified report→apply→no-op in the golden,
      CI 8/8.
      **INCREMENT 3 BUILT 2026-07-12 — auto-linking (shared engine, three triggers).** Extracted the
      link engine (`link_body`/`link_note_file`) from `glossary_scan.py` so three paths share it:
      (1) `glossary_scan.py --apply` whole-vault on-demand; (2) `glossary_new.py` sweeps *just the new
      term* across the vault after scaffolding it (`--no-relink` to skip) — the automatic path for
      adding a term, synchronous+visible (a commit hook is wrong here: a glossary note is non-PARA so
      its commit skips the embed hook, and a hook editing *other* notes would leave them unstaged);
      (3) opt-in per-commit — new `config/features.toml` `glossary_autolink` (default false, via
      `features.py`) drives `glossary_autolink_staged.py` in the pre-commit hook (before
      `embed_staged.py`), linking known terms in **staged** notes only + re-staging them, so a note
      embeds with its links. Contained (staged-only) is what makes the hook safe where the whole-vault
      sweep stayed on-demand. Verified in the golden (new-term sweep links first occurrence; --no-relink
      skips; hook no-op when off, links+re-stages when on) and no-op in a fresh brain; CI 8/8. Remaining:
      the flashcard/graph tail (mostly free). A curated
      **symbolic-layer** feature (distinct from the vector/semantic layer): the vault's ad-hoc
      concept notes become first-class. A term earns a `vault/glossary/{term}.md` note only when
      **pre-identified** as glossary-worthy (reused / non-obvious); a periodic **scan** links every
      body occurrence of the term to its definition. Definitions are **simple sub-notes** whose
      meaning is carried by *how they are referenced*, not by an embedding — so they are **excluded
      from the vector index**. A **devkit feature** (ships into every brain), built prototype-first
      in the golden. Full design + rationale in [docs/glossary.md](docs/glossary.md). Subtasks:
      - **Namespace — `vault/glossary/` (typed, non-PARA sibling).** A top-level folder beside
        `templates/` (already a non-PARA sibling — the precedent), one note per term, plus a
        `type: glossary` frontmatter marker as the tool-facing key. Advertised as **PARA(G)**. Keeps
        the ~10:1 tiny definition notes out of `resources/` and out of search. Generated brains ship
        the **empty** folder + a `glossary/README.md` explaining the convention — **not** pre-filled
        terms (the vocabulary is the user's to curate).
      - **Embedding-exclusion — the core decision (near-free, verified 2026-07-10).** Glossary notes
        must never enter `data/brain.db` (a keyword-dense definition would otherwise rank too high for
        its own term — stub-pollution). **This falls out for free:** every embed/cache path already
        scopes to `PARA_ROOTS`, and `glossary/` is a non-PARA sibling (like `templates/`) — proven by
        committing seven glossary notes to `~/second-brain` (`update_cache: no PARA-note changes`,
        zero sidecars/vectors). `doctor.py` is also `PARA_ROOTS`-scoped, so it ignores them (the
        feared missing-sidecar false-drift does not happen). Subtask is thus **confirm + document +
        keep `glossary/` out of `PARA_ROOTS`**, not new code. Distinct from
        emission-exclusion (glossary notes *are* emitted into a brain; the term-scan links they
        write into other notes' **bodies** *are* embedded — genuine substance, the deliberate
        opposite of `related_auto:` metadata).
      - **Scan tool — `scripts/glossary_scan.py` (emitted, stdlib).** Report unlinked term
        occurrences by default; `--apply` inserts `[[term]]` inline. On-demand (not a hook — the
        body edit re-embeds the touched note), `--apply`-gated + idempotent (the `install_skill` /
        `doctor` / `autolink` stance). Start dumb (exact-term match); stemming/aliases/code-fence
        skipping are follow-ons only if the dumb pass is noisy.
      - **New-term helper + template — `scripts/glossary_new.py <term>` (emitted, stdlib).**
        Slugify the term → `vault/glossary/<slug>.md`; **dedup-check** the folder and refuse
        (print the existing path) if it already exists; else **scaffold from the flashcard
        template** — frontmatter (`type: glossary` + tags placeholder), `# Title`, the
        `Term ? <definition — fill in>` card, and the `#flashcards/…` deck-tag placeholder — so
        every new card is valid for the *Spaced Repetition* plugin by construction. Print the
        path; never open or overwrite (detect-and-instruct). Ship the shared **term template**
        (embedded or `glossary/_TEMPLATE.md`) so humans and the script scaffold identically. The
        value is for a **human** hand-adding terms (consistency + dedup + plugin-valid structure);
        an AI just follows the template.
      - **Docs — DUAL README subtask (explicit), and PARA → PARA(G).** Document the glossary in
        **both** READMEs, and in both switch **PARA → PARA(G)**: spell out the letters
        (**P**rojects, **A**reas, **R**esources, **A**rchive, **G**lossary) and state that the **G**
        is a *slight modification* of the standard PARA method — an orthogonal note-*type* sibling
        (the `templates/` precedent), **not** a fifth actionability bucket. (1) The **devkit
        `README.md`** — the feature for a devkit developer (where it lives, the embed-exclusion, the
        build loop). (2) The **generated brain `README.md`** (via the golden → cleaned template, per
        the managed-block flow) — the convention for a brain *user*: how to add a glossary term, the
        `glossary_scan.py` command, and that glossary notes are not semantically searchable by
        design. Wherever either README lists the PARA roots today, update the wording to PARA(G) with
        the G defined. (No devkit `CLAUDE.md` pointer — devkit development does not need the glossary
        spec location; this task carries the reference, keeping the always-loaded index lean.)
      - **Contract in the product spec.** Specify `type: glossary`, the folder, embed-exclusion, and
        scan behavior in `../second-brain-test/SPEC.md` (per the no-duplicate-product-contracts rule)
        — prototype-first in the golden.
      - **Harness / plumbing.** Add the new emitted files (`glossary/README.md`, `glossary_scan.py`)
        to `emit-manifest.toml`, re-vendor `tests/golden/`, rebuild `template/`, keep the structural
        diff + partition green; the emitted-scripts-compile gate covers the scanner. Optional opt-in
        semantic check that a glossary note is absent from the index (out of the hermetic gate, like
        the Ollama checks).
      - **Downstream (the remaining tail — docs-only, no code).** Both features already *work*; the
        consistent term-title/definition-body shape is what buys them. All that is missing is telling
        the user they exist, in `glossary/README.md`. **Each must be manually exercised in real
        Obsidian before it is written up — neither is reachable from `tools/ci.py`, so a hand-test is
        the only evidence there is. Do not document either as working on inspection alone.**
        - [ ] **Flashcards.** Document that the term shape (`Term ? <definition>` + a
              `#flashcards/…` deck tag) is drop-in for the community *Spaced Repetition* plugin.
              - [ ] **Manual test (acceptance):** in a real vault, install the *Spaced Repetition*
                    plugin, point it at the deck tag, and confirm a real glossary term **renders as a
                    card and can be reviewed** (front = term, back = definition). Record the plugin
                    version tested and any setting the user must change from the default. If the shape
                    needs a tweak to be picked up, that tweak is part of this subtask — fix the term
                    scaffold in `glossary_new.py`, don't paper over it in the README.
        - [ ] **Graph colour.** Document the native Obsidian graph-view colour group that makes
              glossary terms visually distinct from PARA notes (no plugin needed).
              - [ ] **Manual test (acceptance):** add the colour group in Obsidian's graph view and
                    confirm glossary notes — and *only* glossary notes — pick up the colour. **Settle
                    the query while doing it:** `path:glossary/` (folder) vs `tag:#glossary` (tag) are
                    both plausible and the docs currently disagree; test both, document the one that
                    actually works, and make the other stop being mentioned.
        A per-term-colouring plugin is last, if ever. Sequence: convention → embed-exclusion →
        scanner → flashcards → graph colour. Not started.

## README managed block (task #9, BUILT 2026-07-09): a devkit-owned region in a user-editable README
- [x] **Made the brain `README.md` a hybrid — devkit-owned block + user-owned space.**
      (task #9) Before, the brain README was **fully devkit-owned**: `update_brain.py` re-emitted
      it from `template/` **wholesale**, so any user edit was **silently clobbered** on upgrade —
      and the front-page doc of a repo the user owns had **no place for them at all** (surfaced
      2026-07-07 dogfooding). **Built:** the golden/template README now wraps its body in inert
      HTML-comment markers (`<!-- BEGIN generated by second-brain-devkit: … -->` / `END`), ASCII so
      the `update_brain` constants match byte-for-byte; the user writes **above/below**, the devkit
      owns **between**. **Create and update unify** — the template ships the markers with empty user
      regions (create is a plain copy); `update_brain` now **splices** the fresh devkit body between
      the *existing* file's markers via the [[task #10]] `marked_block` helper (imported from
      `template/scripts`, `sys.dont_write_bytecode` so no `__pycache__` leaks into the tracked
      tree), preserving the user's preamble/appendix byte-for-byte and reporting the README
      NEW/CHANGED/SKIP in the dry-run. **Opt-out / safety:** no markers → SKIP (full user
      ownership); one marker only or duplicate markers → SKIP + warn (never guess a boundary).
      Markers are inert comments (invisible in Markdown/Obsidian); the blockquote-swap `clean_readme`
      transform, structural-diff, and self-test are all unaffected (markers sit outside the swapped
      text). **Hermetic CI gate 8/8** (`tools/check_readme_block.py`): create → user preamble/appendix
      + stale body → `update_brain --apply` → assert user space preserved, block regenerated to match
      `template/README.md`, idempotent, and the no-marker/half-marker SKIP cases — git + stdlib, no
      Ollama/mcp. Same **managed-block** primitive as `--nudge`, the `ai-project-status` block, and
      the auto-link `related_auto:` block (task #8). Full design in
      [docs/readme-managed-block.md](docs/readme-managed-block.md). Local-first; **before**
      Postgres/Approach B. Closes the #10→#8→#9 thread.

## Project rename (backlog): second-brain-devkit → create-second-brain
- [ ] **Rename the project `second-brain-devkit/` → `create-second-brain/`.** (task #11)
      Aligns the repo name with its primary end-user entry point (`create_second_brain.py`) —
      what a user actually runs to make a brain. Touches **four layers**, in order:
      - **Emitted provenance (the risky part — do prototype-first).** `template/README.md`,
        `template/CLAUDE.md`, and `template/tests/README.md` embed a devkit back-reference
        that ships into **every generated brain** and links to the GitHub URL
        (`github.com/cornjacket/second-brain-devkit`). A stale name/URL here breaks the
        provenance link in every brain. Change it through the normal loop — prototype in the
        golden (`../second-brain-test`), `vendor_golden.py`, rebuild `template/`, `ci.py`
        green — **not** by hand-editing `template/`. Re-vendor updates `tests/golden/` too.
      - **GitHub repo + remote.** Rename the repo on GitHub, update `origin`
        (`git remote set-url origin …`). GitHub auto-redirects the old URL, but update the
        emitted links so new brains point at the canonical name. (Keep the SSH-push note in
        mind — see [[push-workflow-files-over-ssh]] — for any `.github/workflows/` edits.)
      - **Devkit-internal references (~17 files).** PLAN.md, SPEC.md, open-questions.md,
        docs/, and `tools/` (`build_template.py`, `check_remote_sync.py`, `ci.py`,
        `create_second_brain.py`, `update_brain.py`) mention the name in prose/paths.
      - **Local dir + ai-project-status tracking.** Rename the working directory; update the
        meta-repo's tracked-repo config so `summary.md`/`daily-plan-summary.md` keep
        aggregating this repo under the new name (this repo is *tracked by* ai-project-status,
        but that must never leak into a brain — the forbidden-ref invariant still holds).
      Best done as an isolated, mechanical commit (no behavior change); low risk but wide
      blast radius, so gate on `ci.py` green + a grep for the old name afterward. Not started.

## Milestone G4 — Lifecycle
- [x] **`tools/update_brain.py` — non-destructive upgrade of an existing populated
      brain (surfaced 2026-07-03; BUILT 2026-07-06).** The devkit can only *generate* —
      `create_second_brain.py` refuses a non-empty target — so before this, every devkit
      improvement (WAL, `doctor.py`, `--nudge`, the **MCP server**) reached an existing
      brain only via delete + regenerate. `update_brain.py`:
      - re-emits **tooling** from the tracked `template/` tree (`scripts/`, `skill/`,
        `.githooks/`, `requirements*.txt`, `tests/`, `seeds/`, `README.md`) — walks
        the template so new files (`mcp_server.py`, `requirements-mcp.txt`) are picked
        up automatically, no per-feature edits;
      - **never touches** user territory — `vault/`, `data/`, `config/`, `CLAUDE.md`,
        `GEMINI.md` (a PRESERVE list) — nor git history;
      - **dry-run by default** (reports NEW / CHANGED / preserved); `--apply` writes
        the files and records **one revertable commit** (`--no-verify`, stamped with
        the devkit SHA), refusing a dirty tree so the update lands isolated;
      - guards: refuses a non-brain target and the devkit itself.
      Verified end-to-end: on a simulated outdated+personalized brain it added the MCP
      files (NEW), restored a tampered `db.py` (CHANGED), and **preserved** the vault
      note, customized `config/embedder.toml`, and personal `CLAUDE.md`; plus the
      already-up-to-date, dirty-tree, and non-brain guard paths. **MVP limits:** additive
      (won't delete a file the devkit dropped) and can't distinguish a user-edited
      tooling file from an old version (both are git-revertable; dirty-tree guard +
      dry-run preview cover it).
      Interim until it exists: if the brain is disposable, delete + regenerate (done
      for `~/second-brain` on 2026-07-04 to pick up the MCP server + layer-2 hydrate);
      a *populated* brain still has no safe path.
- [ ] Promote the canonical product spec into the devkit (`SPEC.md` §4 lifecycle).
      The golden keeps its `SPEC.md` as the build-time reference until then
      ([OQ-4](open-questions.md#oq-4)); this promotion happens at mothball, when the
      golden's `SPEC.md` is removed and the devkit becomes its sole home.
- [ ] Mothball `second-brain-test` once generation + harness are trustworthy
- [x] Resolve OQ-1 long-term (golden storage → Option A, tracked files in devkit)
      — **done** via the CI milestone: the golden is vendored at `tests/golden/`
      and the harness reads it there. `open-questions.md`

## Roadmap: big-brain — a shared brain (two approaches)
A **shared** brain (many people/clients), not a replacement for the local-first single
-user brain — details to be hashed out. Full design in [docs/big-brain.md](docs/big-brain.md).
Surfaced a real gap in the **current** design: the brain has **no sync layer at all**
(`create_second_brain.py` inits a local repo with no remote; hooks never pull/push) — fine for one
machine, but multi-machine/multi-user would silently drift.
- [ ] **Approach A — shared git remote (distributed, keeps local-first) — start here.**
      Vault in a shared git remote; every user runs the same local-first brain and syncs
      by git: *pull → post-pull reaction* before reading, *commit → pull --rebase → push*
      after writing; the derived cache stays per-user/git-ignored. **Post-pull reaction
      (essential):** any pulled/changed note must (re-)embed + hydrate — natural home is a
      `post-merge` hook mirroring `post-commit`, or new notes stay unsearchable.
      **Merge conflicts need a human/AI in the loop** (two users, same note) — the `sync`
      helper must surface, not auto-resolve. **Don't commit embeddings** — they're not
      byte-reproducible across machines (the reason sidecars are git-ignored + CI uses
      `test`), so committing → merge churn; each peer re-embeds changed notes locally then
      hydrates ([OQ-3](open-questions.md)). No new services; also fixes the
      single-user-multi-machine gap.
- [ ] **Approach B — deployed, centralized (Postgres + S3 + Lambda).** Only when clients
      **can't run locally** (claude.ai-web, no-install) or you need one central store.
      Brain logic on **Lambda**, notes in **S3**, vector index in **Postgres/`pgvector`**
      (MVCC → real concurrent writers, **retiring the SQLite-only
      [OQ-5](open-questions.md#oq-5) WAL/hydrate/`flock` layering** for this variant),
      embeddings via a cloud API, reached over HTTP / remote MCP (the hosted variant
      [mcp-server.md §2](docs/mcp-server.md) deferred). Requires abstracting three seams —
      **store** (git→S3), **cache** (sqlite-vec→pgvector), **embedder** (→cloud) — via the
      `embedder.py` pattern. Bigger lift.
      Both reuse the `add_note` write design (G6 / task #5). **Local-first must not be
      eroded to enable either.** Not started.
