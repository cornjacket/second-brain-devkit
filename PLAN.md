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

## Milestone CI — Self-sustaining automation  ✅
Robust, hands-off regression checking on every push/PR. **Hard requirement: the
devkit is self-contained — CI checks out only this repo and never reaches the
external golden.** That forces the long-deferred [OQ-1](open-questions.md#oq-1)
resolution: vendor the golden's *expected output* **into** the devkit as a tracked
regression baseline (Option A). The live `../second-brain-test/` reverts to a
hand-prototyping surface only, and its mothball ([G4](#milestone-g4--lifecycle))
gets closer. Vendoring loses no coverage: the pre-commit hook is still exercised
**for real** via Mode-B generation (`new_brain.py` git-inits and the hook fires on
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
      guard) → Mode-A harness → Mode-B smoke (`new_brain.py` + the same diff
      oracle). Passes locally end-to-end; a self-contained git identity lets the
      Mode-B commit run on a bare CI runner.

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
      write note → commit → searchable. `new_brain.py` must commit the scaffold
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
- [ ] **MCP server — SECONDARY, web/desktop chat only.** For clients that **cannot
      shell out to local Python** (Claude Desktop, claude.ai). Exposes
      `search_second_brain(query, k)` over the same Ollama+sqlite-vec index. Not the
      default path; built when we want brain access from a web chat.
  - [ ] **Concurrency layer 2 — in-place hydrate ([OQ-5](open-questions.md#oq-5)).**
        The MCP server is a **long-lived reader** holding a connection open while
        post-commit rebuilds fire — this is what makes `hydrate`'s `unlink()`+rebuild
        a real hazard. Fix: rebuild in one transaction (`DELETE FROM notes`, or
        temp-table swap) so a reader sees old rows until commit, then new, atomically.
        `doctor --repair` benefits too. Do alongside the server.
  - [ ] **Concurrency layer 3 — `flock` writer lock ([OQ-5](open-questions.md#oq-5)).**
        Serialize the *writers* (repair/hydrate/update_cache) against each other for
        the multi-statement critical sections SQLite transactions can't span, while
        WAL handles reader-vs-writer. Only if overlapping writes prove real once the
        server lands.
- **Usage note:** the brain's value as a conventions oracle grows as it is
  populated with decision/convention notes — today it holds only the 4 system seed
  notes.

## Milestone G4 — Lifecycle
- [ ] **Update/upgrade an existing populated brain (surfaced 2026-07-03).** The
      devkit can only *generate* a new brain — `new_brain.py` git-inits a fresh repo
      and refuses a non-empty target unless `--force`, so it **cannot** be run over a
      user's real brain without destroying their notes + history. A real gap: once a
      brain is generated and filled, there is no supported path to pull in later
      devkit improvements (new scripts, bug fixes, WAL, `--nudge`). Needs a
      `tools/update_brain.py` that re-emits **tooling only** (the `verbatim`/`cleaned`
      emitted set: `scripts/`, `README.md`, hooks, `requirements.txt`) into an
      existing brain, leaving `vault/`, `data/`, `config/`, and git history untouched,
      and commits the update in the brain's own repo. Interim: if the brain is
      disposable, delete + regenerate (done for `~/second-brain` on 2026-07-03 to pick
      up `doctor.py`/WAL/`--nudge`); a *populated* brain has no safe path yet.
- [ ] Promote the canonical product spec into the devkit (`SPEC.md` §4 lifecycle).
      The golden keeps its `SPEC.md` as the build-time reference until then
      ([OQ-4](open-questions.md#oq-4)); this promotion happens at mothball, when the
      golden's `SPEC.md` is removed and the devkit becomes its sole home.
- [ ] Mothball `second-brain-test` once generation + harness are trustworthy
- [x] Resolve OQ-1 long-term (golden storage → Option A, tracked files in devkit)
      — **done** via the CI milestone: the golden is vendored at `tests/golden/`
      and the harness reads it there. `open-questions.md`
