# Second Brain Devkit — Build Plan

The durable milestone tracker for **this repo** (the generator + system home).

Distinct from:
- `daily-plan.md` — single-day, forward-looking, `ai-project-status`-managed.
- `SPEC.md` — the spec (what the system *is*), not a progress tracker.

Status: `[x]` done & committed · `[~]` in progress · `[ ]` not started

## ▶ Next up (2026-07-09)
- **▶▶ NEXT — task #9 (README managed block)** — closes the #10→#8→#9 thread.
- **Then queued:** #18 (review the corpus clustering / decide separation strategy — now a lighter
  checkpoint after #17 raised purity), #15 (diverse benchmark corpus — can reuse the #16/#17
  corpus), #12/#13 (feature catalog + ablation harness), #3 (hybrid FTS5 retrieval), #5
  (`add_note` write tool).
- **Done recently:** #17 test-corpus clustering improvement (2026-07-09: rewrote all 100 notes
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
  - [ ] **Write path — add a note to the brain from Claude Desktop (`add_note` tool).**
        (task #5) v1 is read-only, so there is **no way to create a note from Desktop**
        (asked 2026-07-04). A write tool must not just drop a file: it has to land the note in
        a PARA root and run the same **embed → hydrate** path the git hooks do (or make
        a real commit) so it's immediately searchable and history stays consistent —
        otherwise the cache drifts. Design tension: read-only v1 deliberately kept the
        git-committed vault flow the single source of truth
        ([docs/mcp-server.md §3](docs/mcp-server.md)). Scope carefully (where does an
        uncommitted note live? does the tool commit for the user?) before building.
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
- [ ] **Hybrid lexical + vector search (SQLite FTS5).** Add an **FTS5** virtual table
      in the *same* `data/brain.db` (built-in to SQLite — verified available; no new
      dependency, no separate index file), hydrated by the same sidecar/hook flow as
      the vec0 table. Fuse the lexical (BM25) and vector rankings with **Reciprocal
      Rank Fusion** in `search_vault.search()` so both the CLI, the skill, and the MCP
      server benefit at once. Fold `tags:` into the lexical text. **Do NOT** add a
      manual `keywords:` note section — FTS5 over the body + tags already covers literal
      terms, at real authoring cost for marginal gain.
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

## Review test-corpus clustering (task #18, backlog)
- [ ] **Review the clustering analysis + post-#17 cohesion and decide the separation strategy.**
      (task #18) Once #17 improves the notes, reassess whether the corpus separates well enough for
      the #12/#13 benchmark, or whether to pursue further levers (more notes/topic; merging the
      adjacent rust↔golang / AI topics; a stronger embedder) — or to lean on the **ground-truth
      topic labels** instead of unsupervised separation (the reframe in
      [docs/test-corpus-clustering.md](docs/test-corpus-clustering.md)). A decision checkpoint, not
      new code.

## Benchmarking & feature toggles (backlog): quantify each quality enhancement
Goal: measure the **relative** retrieval/graph-quality payoff of each enhancement by
turning it on/off and benchmarking — an ablation study — so we know which features
actually earn their keep. Both tasks below are exploratory (**may not become a shipped
requirement**); they also produce the material for a future GitHub tutorial.

- [ ] **Seed a brain with a large, topically-diverse test corpus.** (task #15; the shared
      dataset prerequisite — do before the calibration/ablation work depends on it.) A
      test/harness that populates a second-brain with a **large collection of made-up notes
      spanning many distinct topics** (e.g. cooking, personal finance, distributed systems,
      history, biology, music theory…), so the embedding space has real **cluster structure**
      — the thing today's ~7 homogeneous notes lack. This corpus is what makes several other
      tasks meaningful: the auto-link threshold work (§2.2/§2.3 — `t_max` and topic-count
      calibration need separable topics), the **ablation benchmark (#12)** (this **extracts
      and satisfies** #12's "author a substantial evaluation corpus" sub-goal), the feature
      catalog's worked examples (#13), and Medium-post/tutorial screenshots (#14). Design
      points: enough notes per topic **and** enough topics that single-linkage/HDBSCAN
      recovers the intended clusters (a clear plateau in the cluster-count sweep);
      **deterministic/scriptable** seeding (a generator or a committed `seeds/` corpus) so
      runs are repeatable; **realistic note bodies** (real substance, not lorem ipsum) so
      semantic distances mean something. Opt-in/local (needs Ollama to embed), out of the
      hermetic CI gate. Unblocks #12/#13 and #8 final threshold calibration. Not started.
  - **Reminder — run the deferred auto-link `--apply` here.** #8's write path is built and
    dry-run-verified, but **deliberately not applied** to any brain: on today's 7 homogeneous
    notes it draws a near-complete graph (nothing to discriminate) and churns every committed
    note. Once this diverse corpus is seeded, calibrate `t_max` on it (§2.2), then
    `autolink.py --apply` — that is the first point where the graph is actually illuminating
    (distinct topic clusters, sparse cross-topic edges) and worth committing / viewing in
    Obsidian's graph view.
- [ ] **Catalog every second-brain quality-enhancement feature.** (task #13; do FIRST —
      it is the input to #12 and the outline for the tutorial.) Produce a single inventory
      (likely `docs/quality-features.md`) listing each retrieval/graph quality feature the
      brain has or plans, each with: **name**, one-line **what/why**, **mechanism**,
      **index-time vs query-time** (does flipping it require a re-embed?), the intended
      **config toggle key**, and **status**. Starting set (the task completes / corrects it):
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
- [ ] **Global feature toggles + ablation benchmark harness.** (task #12) Make each feature
      in the #13 catalog a **global feature toggle** (config-driven, following
      `embedder.py`'s env-override > `config/…` > default pattern — e.g. a `[features]`
      block or `config/features.toml`), then build an **ablation harness** that runs a
      **labeled eval set** (queries → expected relevant notes) against the brain under each
      toggle configuration and reports IR metrics (recall@k, MRR, nDCG, top-1 distance +
      **margin/separation**) so each feature's contribution is quantified.
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

## README managed block (backlog): a devkit-owned region in a user-editable README
- [ ] **Make the brain `README.md` a hybrid — devkit-owned block + user-owned space.**
      (task #9) Today the brain README is **fully devkit-owned**: `update_brain.py` re-emits
      it from `template/` **wholesale** (re-emit list, not `PRESERVE`), so any user edit is
      **silently clobbered** on upgrade — and the front-page doc of a repo the user owns has
      **no place for them at all**. Surfaced 2026-07-07 dogfooding (a hand-added README blurb
      that was both misplaced *and* fated to be overwritten). Fix: wrap the devkit content in
      HTML-comment markers (`<!-- BEGIN generated by second-brain-devkit … -->` / `END`); the
      user writes **above/below**, the devkit owns **between**. **Create and update unify** —
      the template ships the markers with empty user regions; `update_brain` **splices** the
      fresh devkit body between the *existing* file's markers, preserving the user's
      preamble/appendix. **Opt-out:** delete the `BEGIN` marker → the upgrader implants
      nothing (full user ownership; detect-+-instruct stance). Markers are inert comments
      (invisible in Markdown/Obsidian); structural-diff + self-test unaffected. Same
      **managed-block** primitive as `--nudge`, the `ai-project-status` block, and the
      auto-link `related_auto:` block (task #8), all built on the shared splice helper
      (task #10, do first). Touches: golden README (prototype-first → vendor → template) +
      `update_brain.py` splice logic (guard the malformed one-marker case). Full design in
      [docs/readme-managed-block.md](docs/readme-managed-block.md). Local-first; **before**
      Postgres/Approach B. Not started.

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
