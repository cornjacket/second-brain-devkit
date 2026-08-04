# Second Brain Devkit — Agent Memory

This is memory for working **on the devkit** — the generator and system home. It
is *not* the memory for working inside a brain; that lives in the product repo at
`../second-brain-test/CLAUDE.md`.

## Where things are specified

Do **not** duplicate product (per-brain) contracts here — link to the product
spec so they cannot drift.

- System workflow, roles, lifecycle, generator/validation loop → [SPEC.md](SPEC.md)
- Per-brain contracts (PARA, sidecar schema, embedding, cache DDL, search,
  `register`) → `../second-brain-test/SPEC.md` (canonical product spec, for now —
  promoted into the devkit only at mothball, see [OQ-4](open-questions.md))
- Unresolved design decisions → [open-questions.md](open-questions.md)
- What every source file is for → [docs/source-map.md](docs/source-map.md)
- MCP server design + Claude Desktop → [docs/mcp-server.md](docs/mcp-server.md),
  [docs/claude-desktop-workflow.md](docs/claude-desktop-workflow.md)
- MCP hardening — nothing may hang the server (task #24, done; CI gate 12) → [docs/mcp-hardening.md](docs/mcp-hardening.md)
- Partial-commit index poisoning — the `add_note` content-corruption bug (task #28, fixed; **awaiting review**) → [docs/partial-commit-index-poisoning.md](docs/partial-commit-index-poisoning.md)
- Stale-embedding detection — doctor flags a vector that predates the note's canonical view (task #30, built) → CI gate 11 (`tools/check_doctor_stale.py`)
- Embed-excluded block — decorative regions (ASCII art, diagrams) fenced in `<!-- second-brain:no-embed:begin/end -->` are cut from `canonical_body()`, so they leave **both** the embedding and the content hash (task #39, built; CI gate 15 `tools/check_embed_excluded.py`). Line count is the wrong proxy for the embed budget — the budget is tokens. → [docs/embed-excluded-block.md](docs/embed-excluded-block.md)
- Tag hygiene — deterministic detector + backfill applier + write-time near-miss warning, emitted into every brain (task #32, Stages 1–6 done; CI gate 13 `tools/check_tag_lint.py`; read-only MCP tool deferred) → [docs/tag-hygiene.md](docs/tag-hygiene.md)
- Claude Desktop e2e — canned prompts + side-effect verifiers, human-driven (task #33; not a CI gate) → [docs/desktop-e2e.md](docs/desktop-e2e.md)
- Desktop e2e against a real brain — disposable-branch setup/teardown so the suite runs against a brain with no Desktop reconfig, then reverts byte-identical (task #34) → [docs/desktop-e2e-disposable-branch.md](docs/desktop-e2e-disposable-branch.md)
- Desktop e2e **emitted into every brain** — the #33+#34 suite now ships at `<brain>/desktop-e2e/` (prototyped in the golden, `verbatim` in `emit-manifest.toml`, self-targeting the brain it ships in) so a user who generates a brain can self-verify their Claude Desktop connection (task #35, built; smoke-tested on golden + real brain; human Desktop pass still to run) → [docs/desktop-e2e.md](docs/desktop-e2e.md)
- Pure-client cross-session retrieval test — Desktop-only, no local verifiers: seed canary values in one chat, delete it, retrieve in a fresh chat (rules out conversation memory; targets the right retrieval substrate per [[unfindable-is-not-nonexistent]]) (task #36, built + emitted at `<brain>/desktop-e2e/pure-client/`; human Desktop pass still to run) → [docs/desktop-e2e-pure-client.md](docs/desktop-e2e-pure-client.md)
- Plugin packaging — one Claude Code plugin vs. the skill + MCP two-step (task #23, **CLOSED 2026-07-18**): plugin route **declined** (can't collapse the two-step — its MCP server serves only the CLI + Desktop Code tab, not the Desktop **Chat** tab where a brain is used — and it's Claude-only, fragmenting Gemini); `.mcpb`/Connector **deferred** behind a trigger (first external Desktop user) → [docs/plugin-packaging.md](docs/plugin-packaging.md)
- Retrieval design (planned hybrid search) → [docs/retrieval-quality.md](docs/retrieval-quality.md)
- PDF ingestion — chunk-and-embed long documents (task #7, **SHIPPED — M1–M6 done**): breaks "one note = one vector" (many chunk-vectors per source), solved bolt-on so the note path stays byte-identical; PDF git-ignored in the vault (Git-LFS later), `pypdf` optional dep (`requirements-pdf.txt`). Emitted into every brain: `chunker`/`pdf_extract`/`embed_pdf`/`pdf_cache`/`pdf_search`/`pdf_config`/`add_pdf`, the `[pdf]` config block, four MCP tools (`list_inbox_pdfs`/`add_pdf`/`search_pdf_passages`/`get_pdf_passage`), README "Add a PDF", CI gate 14, and doctor PDF parity. → [docs/pdf-ingestion.md](docs/pdf-ingestion.md)
- PDF ingestion — interactive selection via MCP elicitation (task #7 follow-up, **live pass CONFIRMED 2026-07-20**): `add_pdf_guided` MCP tool walks folder → PDF → PARA as client-rendered elicitation forms, falling back to the `list_inbox_pdfs`/`add_pdf` chat flow at runtime otherwise. Verified end-to-end on **Claude Code CLI 2.1.215** — it ingested a real PDF with no fallback; the earlier same-version fallback was a stale pre-restart MCP subprocess, not a capability gap. Desktop chat still lacks elicitation. → [docs/pdf-elicitation.md](docs/pdf-elicitation.md)
- Vector-derived Obsidian auto-linking (task #8 — **engine BUILT**, `scripts/autolink.py` emitted + CI gate 4; split into **#8a** turn-it-on via `--apply` on a real brain, *ready now*, and **#8b** the calibration deriver + hysteresis, gated on the #12/#13/#15 diverse corpus) → [docs/auto-linking.md](docs/auto-linking.md)
- Managed blocks — devkit region + user space in the brain's `README.md` (task #9) **and `CLAUDE.md`** (task #40, built; CI gate 16 `tools/check_claude_block.py`). `update_brain.py` splices both; a marker-less file (a brain older than the markers) is reported loudly on every run and adoptable via an opt-in `--adopt` that keeps the existing file verbatim. Adoption first covered `CLAUDE.md` only — dogfooding extended it to the README the same day: **"a human will notice" guards against wrong content, never against missing content.** → [docs/readme-managed-block.md](docs/readme-managed-block.md)
- Connect a new brain to a git remote (`create_second_brain.py --remote`, built) → [docs/remote-backed-brains.md](docs/remote-backed-brains.md)
- Roadmap: shared brain (git-remote or Postgres/S3/Lambda) → [docs/big-brain.md](docs/big-brain.md)

## Style & conventions (devkit code)

- Imports: standard library unless declared in `requirements.txt`.
- Match the surrounding code's style and comment density.
- The devkit is **disjoint from its own tracker**: nothing the generator emits
  may depend on it. (This repo is itself *tracked by* a **git-workspace** for
  its own development — see the managed block below — but that must never leak
  into a generated brain. The tracker has already been swapped once; the
  invariant survived it precisely because it was never named in output.)
- **Hard invariant — zero forbidden references in a generated brain.** No file
  the generator emits may contain the string `ai-project-status` (or any other
  devkit-internal dependency) — not even to *declare independence* from it; an
  end user has never heard of it, so naming it only confuses. This is
  **deterministically enforced**, not trusted: the validation harness greps the
  generated tree for a denylist and fails on any hit
  (`tools/check_no_forbidden_refs.py`). When you clean a golden file into a
  template, scrub the reference entirely rather than reword it. See
  [SPEC §5.2](SPEC.md).

## Development Workflow
This repo is a **generator**: it produces a `second-brain/` repo. Build each feature with this loop:
1. **Prototype** the feature by hand in the golden reference (`../second-brain-test/`, a standalone sibling repo — see OQ-1) and confirm it behaves as expected. The golden is the known-good *expected output* and serves as the regression baseline.
2. **Productize** it into the devkit — the script, prompt, or harness that generates the feature.
3. **Validate** by running the devkit against a throwaway repo at `sandbox/scratch/`. The harness must **wipe-and-regenerate** `sandbox/scratch/` on every run (never test against stale state), then **diff** the generated output against the golden reference. A clean diff is the acceptance test. Run the whole gate with `python3 tools/ci.py` (the same entry point CI runs — local ≡ CI).

- `sandbox/` is gitignored — it is regenerated output, never committed.
- The live golden answers *"does the feature work?"*; `sandbox/scratch/` answers *"does the devkit generate it correctly?"*
- **Golden location (OQ-1, RESOLVED → Option A):** the golden is **vendored into the devkit** at `tests/golden/` — plain tracked files (no `.git`), the regression baseline the whole harness reads. Refresh it from the live prototype with `python3 tools/vendor_golden.py` (a dev-machine step; **CI never runs it** and never reaches outside this repo). The live `../second-brain-test/` is now only the **hand-prototyping surface** — its own `.git` + hook still fire for real while you build a feature (step 1) — and heads for mothball ([G4](PLAN.md)); the pre-commit hook is exercised in CI via Mode-B generation, not via the golden. After prototyping in the live golden, run `vendor_golden.py` to update the snapshot, then commit. See OQ-1 in [open-questions.md](open-questions.md).

### Creating a brain during development (review the README installation checklist)

When you create or reinstall a real brain with `tools/create_second_brain.py`
(dogfooding, a demo, or the user's own brain — **not** the throwaway `sandbox/scratch/`
of the harness), **review the brain's installation checklist in the [README](README.md)
and make sure every item is satisfied before reporting the brain ready.** Generating the
scaffold is only step one; a brain is not "installed" until it is verified runnable.

**Review, don't blindly repeat.** Walk the checklist and **complete the items not yet
done**; you need not re-run steps already completed in this session/environment (deps
already installed, Ollama already running) — but **verify** their end state rather than
assume it. The README is the source of truth for the steps and their order — don't
duplicate them here — but the shape is:

1. `create_second_brain.py <path>` (add `--remote <URL>` to back it up — see the
   README's "Back it up / share it" prerequisites: empty repo, per-machine creds, git
   identity; all preflighted).
2. `cd <path>` → `pip install -r requirements.txt` → `python3 scripts/self_test.py`
   (confirm the plumbing).
3. For real semantic search: start Ollama + pull the model, then
   `python3 scripts/doctor.py` (the "is my brain ready?" preflight).

Report the brain working only once you've walked the checklist and `doctor.py` is green —
not merely because the files generated. If you skipped or couldn't verify an item, say so
plainly rather than implying the brain is ready.

## Commit & working style (devkit-owned)

This section is **outside** the managed block below, so it is this repo's own
directive: the injector only ever rewrites the content *between* its begin/end markers
and leaves everything else (including this) untouched. That held for the previous
tracker's injector and holds for the git-workspace kernel that replaced it — the
guarantee is the marker pair, not the tool.

- **Commit autonomously; never push unless asked; stop at the task boundary.** Do **not** ask permission to commit and do **not** ask "shall I commit?" in prose — stage and commit completed work following the commit-message schema below on your own initiative. To keep commits silent (no permission prompt), match the allow-list: run `git add <paths>` and `git commit` as **separate** calls (not a `&&` compound), and pass the message as a **single-quoted** string — **no `$(cat <<EOF)` command substitution** (avoid apostrophes in the body so single-quoting works). **Never `git push` on your own** — push only when the user **explicitly** asks; do not ask to push either. Autonomy is *within* a task: do everything the task needs **except** pushing. Once a task's commit is announced, **stop and yield to the user** — report what landed and wait, rather than rolling forward into the next task unprompted. The task boundary is a checkpoint, not a place to keep going.

- **Put a BLANK LINE between the title and `- [Context]:`.** Git ends the *subject* at the
  first blank line — with none, the entire message becomes the subject, and `git log --oneline`,
  `git shortlog`, GitHub's commit list, and every `%s`-based tool print the whole body on one
  line. This repo did that for **83 of its first 158 commits** (subjects of 1,600–3,400 chars),
  destroying the very "scan `git log` and grasp the change from the title alone" property the
  schema exists to guarantee. The tell that it is happening: needing `| cut -c1-80` to make
  `git log --oneline` readable. The whole fix is one blank line:

  ```
  feat(mcp): add a note to the brain from Claude Desktop
                                          ← this blank line IS the fix
  - [Context]: …
  - [Impact]: …
  ```

  `[Context]`/`[Impact]` still sit in the body, so the schema and the tracker's extraction
  are unaffected (it reads the full message, not the subject). **Do not rewrite existing
  history** to fix it — the content is fine, only the framing was wrong. The schema block
  below is *injected* and cannot be edited here; the durable fix belongs **upstream in the
  injector's template**, which would fix every repo in the portfolio at once. That upstream
  moved on 2026-08-04: it was `templates/claude-rule.md` in `project-status`, which is
  retiring, and is now `template/workspace/templates/commit-kernel.md` in
  [create-git-workspace](https://github.com/cornjacket/create-git-workspace) — where the
  missing blank line was **confirmed still present** in all four copies of the schema when
  this repo migrated. Filed there. This bullet is the local guard until it lands.

<!-- git-workspace-commits:begin -->
<!--
  Injected and refreshed by a git-workspace that tracks this repo:
  https://github.com/cornjacket/create-git-workspace

  Do not edit between the markers — the next injection overwrites this block.
  Everything OUTSIDE the markers is yours and is preserved.

  This block is deliberately a KERNEL: only the rules that would be too late if
  they loaded on demand. It is also deliberately WORKSPACE-AGNOSTIC — it is
  committed to this shared repo, and several developers may each track it from
  their own workspace. Nothing here may name one workspace, one developer, or
  one generator version, or two developers would overwrite each other's block on
  every injection.
-->
## Commit discipline

Your commits are this repo's telemetry. A workspace reconstructs what happened
here from `git log` alone and summarizes it across a whole portfolio, so a commit
that does not say what changed is work nobody can see.

1. Every commit follows this shape. `[Context]` and `[Impact]` are required on any
   non-trivial commit (a typo or pure formatting may omit them):

   ```
   <domain>(<scope>): <high-level functional summary>
   - [Context]: why this was done / what was learned
   - [Impact]: how it alters the project or system behavior
   ```

2. Title the **system change, not the files**, and write it for a reader who has
   never seen this repo — these messages are read across the whole portfolio.
   `feat(auth): let users reset a forgotten password by email`, not
   `add token TTL check to reset handler`.

3. Commit at **task granularity** — never per-prompt — and commit completed work
   **before the session ends**. Uncommitted work is invisible to the tracker.

4. Immediately after committing, print `✅ <short-hash> — <title>` on its own line.

### Daily plans do not live here

Do **not** create a `daily-plan.md` in this repo. Plans are *per-developer*
intent, so each developer keeps their own in their own workspace
(`.workspace/daily-plans/<repo>/daily-plan.md`). A shared plan file in a shared repo is
a file two people overwrite.

<!-- git-workspace-commits:end -->
