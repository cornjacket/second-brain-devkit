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
- Retrieval design (planned hybrid search) → [docs/retrieval-quality.md](docs/retrieval-quality.md)
- Vector-derived Obsidian auto-linking (backlog, task #8) → [docs/auto-linking.md](docs/auto-linking.md)
- Connect a new brain to a git remote (`new_brain.py --remote`, built) → [docs/remote-backed-brains.md](docs/remote-backed-brains.md)
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

<!-- ai-project-status:begin -->
<!--
  This block is injected and refreshed by ai-project-status:
  https://github.com/cornjacket/ai-project-status

  It defines the commit-message discipline this repo must follow so
  the meta-repo can summarize cross-portfolio activity in summary.md.

  Do not edit between the begin/end markers — local edits will be
  overwritten on the next `setup-new-repo.sh --update`. To change
  the rules, edit templates/claude-rule.md in ai-project-status
  and re-run `setup-new-repo.sh --update <this-repo-remote>`.
-->
## Knowledge Extraction & Git Automation

This repo is monitored by [`ai-project-status`](https://github.com/cornjacket/ai-project-status). It no longer reads a `log.md` file — backward-looking activity is reconstructed **directly from your git history**. Your job is to make every commit message a high-level, self-contained telemetry record so the meta-repo can summarize cross-portfolio activity in `summary.md`.

### Commit-message schema

Every commit MUST follow this shape:

```
<domain>(<scope>): <high-level functional summary>
- [Context]: Why this was done / what was learned.
- [Impact]: How it alters the project or system behavior.
```

### Rules

1. **The title summarizes the functional change, not the files.** Describe the overall behavior change or architectural decision (`engine(telemetry): replace log.md mining with commit parsing`), NOT a list of touched file names (`update _lib.py and tests`). A reader scanning `git log` should grasp *what changed in the system* from the title alone.

2. **`[Context]` and `[Impact]` are required on any non-trivial commit.** `[Context]` captures the why / the lesson learned; `[Impact]` captures how the project or system behavior changes. Each may span multiple lines. Trivial mechanical commits (typo, formatting) may omit them.

3. **Commit at task granularity — never per-prompt.** Multiple prompts inside one task land in one commit. Open a new commit when the focus changes (a new task, a substantively different question, a meaningfully new concept). Avoid both **commit-per-prompt** (noise that drowns out signal) and **task-without-a-commit** (gaps that make the history untrustworthy).

4. **Automate the commit before session close.** Stage the work (`git add`) and run `git commit -m` with a schema-compliant message before ending the session. Do not leave completed work uncommitted — uncommitted work is invisible to the meta-repo.

5. **Announce each task commit.** Immediately after committing, print `✅ <short-hash> — <title>` on its own line in the conversation, so the user can scan the transcript for recorded work at a glance. One checkmark per task commit — the commit *is* the record, so there is nothing else to back-fill.

## Daily plan (daily-plan.md)

`daily-plan.md` is a **forward-looking** plan file at the repo root. It captures the intent for one working day. ai-project-status aggregates every tracked repo's `daily-plan.md` into [`daily-plan-summary.md`](https://github.com/cornjacket/ai-project-status/blob/main/daily-plan-summary.md).

### Rules

1. **Single-day scope.** The file represents *one* day's plan. It is **always overwritten**, never appended. History of what actually happened lives in your git history and `summary.md`.

2. **Header carries the date.** The first line MUST be `# Daily plan — YYYY-MM-DD`, where the date is the day the plan is *for*. The aggregator parses this to detect stale plans; an unparseable header is treated as stale.

3. **Body is a 100-ft view, written as a bullet list.** Capture the day's intent as a short bullet list (a handful of bullets, not a wall of prose), plus a small ASCII diagram (timeline, flow, milestones) that conveys the shape of the day at a glance. Each bullet is one scannable line of intent. Don't write a dense paragraph — the aggregated `daily-plan-summary.md` is meant to be skimmed in seconds. Don't write granular tasks either — your commit history records granularity after the fact.

4. **Forward-write rule.** Overwrite `daily-plan.md` with the next working day's plan **only when the user explicitly asks to plan tomorrow** — e.g., "write tomorrow's plan", "set up tomorrow", or an end-of-day signoff that includes a forward-planning intent. Do NOT auto-trigger on ambiguous "let's stop here" or "good for today" signoffs — wait for an explicit forward-planning ask. If today is Friday, write Monday's plan (the aggregator's weekend tolerance keeps the Friday-written-on-Friday plan valid through the weekend; Monday's plan is what's needed for Monday).

5. **Start-of-session safety net.** A `SessionStart` hook (installed at `.claude/hooks/check-daily-plan.py`) checks `daily-plan.md` freshness against today's most-recent-weekday. If stale or missing, it injects a prompt instructing you to ask the user for today's plan and overwrite the file before doing other work. Treat this as a hard precondition — don't proceed with other tasks until the plan is fresh.

<!-- ai-project-status:end -->
