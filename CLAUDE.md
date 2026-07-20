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
- Tag hygiene — deterministic detector + backfill applier + write-time near-miss warning, emitted into every brain (task #32, Stages 1–6 done; CI gate 13 `tools/check_tag_lint.py`; read-only MCP tool deferred) → [docs/tag-hygiene.md](docs/tag-hygiene.md)
- Claude Desktop e2e — canned prompts + side-effect verifiers, human-driven (task #33; not a CI gate) → [docs/desktop-e2e.md](docs/desktop-e2e.md)
- Desktop e2e against a real brain — disposable-branch setup/teardown so the suite runs against a brain with no Desktop reconfig, then reverts byte-identical (task #34) → [docs/desktop-e2e-disposable-branch.md](docs/desktop-e2e-disposable-branch.md)
- Desktop e2e **emitted into every brain** — the #33+#34 suite now ships at `<brain>/desktop-e2e/` (prototyped in the golden, `verbatim` in `emit-manifest.toml`, self-targeting the brain it ships in) so a user who generates a brain can self-verify their Claude Desktop connection (task #35, built; smoke-tested on golden + real brain; human Desktop pass still to run) → [docs/desktop-e2e.md](docs/desktop-e2e.md)
- Pure-client cross-session retrieval test — Desktop-only, no local verifiers: seed canary values in one chat, delete it, retrieve in a fresh chat (rules out conversation memory; targets the right retrieval substrate per [[unfindable-is-not-nonexistent]]) (task #36, built + emitted at `<brain>/desktop-e2e/pure-client/`; human Desktop pass still to run) → [docs/desktop-e2e-pure-client.md](docs/desktop-e2e-pure-client.md)
- Plugin packaging — one Claude Code plugin vs. the skill + MCP two-step (task #23, **CLOSED 2026-07-18**): plugin route **declined** (can't collapse the two-step — its MCP server serves only the CLI + Desktop Code tab, not the Desktop **Chat** tab where a brain is used — and it's Claude-only, fragmenting Gemini); `.mcpb`/Connector **deferred** behind a trigger (first external Desktop user) → [docs/plugin-packaging.md](docs/plugin-packaging.md)
- Retrieval design (planned hybrid search) → [docs/retrieval-quality.md](docs/retrieval-quality.md)
- PDF ingestion — chunk-and-embed long documents (task #7, **SHIPPED — M1–M6 done**): breaks "one note = one vector" (many chunk-vectors per source), solved bolt-on so the note path stays byte-identical; PDF git-ignored in the vault (Git-LFS later), `pypdf` optional dep (`requirements-pdf.txt`). Emitted into every brain: `chunker`/`pdf_extract`/`embed_pdf`/`pdf_cache`/`pdf_search`/`pdf_config`/`add_pdf`, the `[pdf]` config block, four MCP tools (`list_inbox_pdfs`/`add_pdf`/`search_pdf_passages`/`get_pdf_passage`), README "Add a PDF", CI gate 14, and doctor PDF parity. → [docs/pdf-ingestion.md](docs/pdf-ingestion.md)
- PDF ingestion — interactive selection via MCP elicitation (task #7 follow-up, **built**): `add_pdf_guided` MCP tool walks folder → PDF → PARA as client-rendered elicitation forms on clients that support it (**Claude Code CLI**; Desktop chat does not — issue #56243), falling back to the `list_inbox_pdfs`/`add_pdf` chat flow at runtime otherwise. Live CLI form pass still to run → [docs/pdf-elicitation.md](docs/pdf-elicitation.md)
- Vector-derived Obsidian auto-linking (backlog, task #8) → [docs/auto-linking.md](docs/auto-linking.md)
- Brain README managed block — devkit region + user space (`update_brain.py` splices, built task #9) → [docs/readme-managed-block.md](docs/readme-managed-block.md)
- Connect a new brain to a git remote (`create_second_brain.py --remote`, built) → [docs/remote-backed-brains.md](docs/remote-backed-brains.md)
- Roadmap: shared brain (git-remote or Postgres/S3/Lambda) → [docs/big-brain.md](docs/big-brain.md)

## Style & conventions (devkit code)

- Imports: standard library unless declared in `requirements.txt`.
- Match the surrounding code's style and comment density.
- The devkit is **disjoint from `ai-project-status`**: nothing the generator
  emits may depend on it. (This repo is itself *tracked by* `ai-project-status`
  for its own development — see the managed block below — but that must never
  leak into a generated brain.)
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

This section is **outside** the `ai-project-status` managed block below, so it is this
repo's own directive: `setup-new-repo.sh --update` only ever rewrites the content
*between* its begin/end markers and leaves everything else (including this) untouched.

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

  `[Context]`/`[Impact]` still sit in the body, so the schema and project-status's extraction
  are unaffected (it reads the full message, not the subject). **Do not rewrite existing
  history** to fix it — the content is fine, only the framing was wrong. The schema block
  below is *injected* and cannot be edited here; the durable fix belongs upstream in
  `templates/claude-rule.md` in [project-status](https://github.com/cornjacket/project-status),
  which would fix every repo in the portfolio at once. This bullet is the local guard until then.

<!-- ai-project-status:begin -->
<!--
  This block is injected and refreshed by project-status:
  https://github.com/cornjacket/project-status

  It defines the commit-message discipline this repo must follow so
  the meta-repo can summarize cross-portfolio activity in summary.md.

  Do not edit between the begin/end markers — local edits will be
  overwritten on the next `setup-new-repo.sh --update`. To change
  the rules, edit templates/claude-rule.md in project-status
  and re-run `setup-new-repo.sh --update <this-repo-remote>`.
-->
## Knowledge Extraction & Git Automation

This repo is monitored by [`project-status`](https://github.com/cornjacket/project-status). It no longer reads a `log.md` file — backward-looking activity is reconstructed **directly from your git history**. Your job is to make every commit message a high-level, self-contained telemetry record so the meta-repo can summarize cross-portfolio activity in `summary.md`.

### Commit-message schema

Every commit MUST follow this shape:

```
<domain>(<scope>): <high-level functional summary>
- [Context]: Why this was done / what was learned.
- [Impact]: How it alters the project or system behavior.
```

### Rules

1. **The title summarizes the functional change, not the files.** Describe the overall behavior change or architectural decision (`engine(telemetry): replace log.md mining with commit parsing`), NOT a list of touched file names (`update _lib.py and tests`). A reader scanning `git log` should grasp *what changed in the system* from the title alone.

1a. **Write for a reader unfamiliar with the project — carry enough top-level context to be self-contained.** These commits are summarized **across the whole portfolio** in `summary.md`, so a low-level, jargon-only message summarizes poorly. Name the capability in plain language and say *what it does for the product or user*, not just the internal mechanic; lead with the outcome, then the detail. Prefer `feat(auth): let users reset a forgotten password by email` over `add token TTL check to reset handler`. Assume the reader knows neither the file names nor the internal shorthand — a bare `refactor: lazy-import db` or `wire gate 4/7` is too esoteric on its own. This applies to the title **and** `[Context]`/`[Impact]`.

2. **`[Context]` and `[Impact]` are required on any non-trivial commit.** `[Context]` captures the why / the lesson learned; `[Impact]` captures how the project or system behavior changes. Each may span multiple lines. Trivial mechanical commits (typo, formatting) may omit them.

3. **Commit at task granularity — never per-prompt.** Multiple prompts inside one task land in one commit. Open a new commit when the focus changes (a new task, a substantively different question, a meaningfully new concept). Avoid both **commit-per-prompt** (noise that drowns out signal) and **task-without-a-commit** (gaps that make the history untrustworthy).

4. **Automate the commit before session close.** Stage the work (`git add`) and run `git commit -m` with a schema-compliant message before ending the session. Do not leave completed work uncommitted — uncommitted work is invisible to the meta-repo.

5. **Announce each task commit.** Immediately after committing, print `✅ <short-hash> — <title>` on its own line in the conversation, so the user can scan the transcript for recorded work at a glance. One checkmark per task commit — the commit *is* the record, so there is nothing else to back-fill.

## Daily plan (daily-plan.md)

`daily-plan.md` is a **forward-looking** plan file at the repo root. It captures the intent for one working day. project-status aggregates every tracked repo's `daily-plan.md` into [`daily-plan-summary.md`](https://github.com/cornjacket/project-status/blob/main/daily-plan-summary.md).

### Rules

1. **Single-day scope.** The file represents *one* day's plan. It is **always overwritten**, never appended. History of what actually happened lives in your git history and `summary.md`.

2. **Header carries the date — and nothing else.** The first line MUST be exactly `# Daily plan — YYYY-MM-DD`, where the date is the day the plan is *for*. The aggregator parses this to detect stale plans; an unparseable header is treated as stale. **Do not put the repo's URL (or anything else) on this line** — project-status already knows each repo's URL from its registry and links the repo name to it automatically in `daily-plan-summary.md`, so the one-click link is handled for you. Never hand-write the repo URL anywhere in this file.

3. **Body is a 100-ft view with a fixed structure**, in this order, so the aggregated summary reads consistently across the whole portfolio:
   1. **`**What this repo is (for a newcomer):**`** — one or two plain-language sentences so a reader who has *never seen this repo* understands what it is and what it does. This is the standalone context that makes the plan legible in the cross-portfolio rollup. Keep it stable day-to-day; only revise it when the repo's purpose actually shifts.
   2. **`**Last implemented:**`** — a one-liner naming the most recent thing shipped (the last meaningful commit/feature), so the reader knows where the repo currently stands.
   3. **Focus / plan** — a short bullet list of the day's intent (a handful of bullets, not a wall of prose). Each bullet is one scannable line. Don't write a dense paragraph — `daily-plan-summary.md` is meant to be skimmed in seconds. Don't write granular tasks either — your commit history records granularity after the fact.
   4. **A small ASCII diagram** (timeline, flow, milestones) that conveys the shape of the day at a glance.

4. **Forward-write rule.** Overwrite `daily-plan.md` with the next working day's plan **only when the user explicitly asks to plan tomorrow** — e.g., "write tomorrow's plan", "set up tomorrow", or an end-of-day signoff that includes a forward-planning intent. Do NOT auto-trigger on ambiguous "let's stop here" or "good for today" signoffs — wait for an explicit forward-planning ask. If today is Friday, write Monday's plan (the aggregator's weekend tolerance keeps the Friday-written-on-Friday plan valid through the weekend; Monday's plan is what's needed for Monday).

5. **Start-of-session safety net.** A `SessionStart` hook (installed at `.claude/hooks/check-daily-plan.py`) checks `daily-plan.md` freshness against today's most-recent-weekday. If stale or missing, it injects a prompt instructing you to ask the user for today's plan and overwrite the file before doing other work. Treat this as a hard precondition — don't proceed with other tasks until the plan is fresh.

<!-- ai-project-status:end -->
