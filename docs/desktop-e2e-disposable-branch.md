# Desktop e2e against your real brain — disposable-branch harness (task #34)

**Status:** **PLANNED — ▶▶ next up** (2026-07-17). Extends the #33 suite
([docs/desktop-e2e.md](desktop-e2e.md)); no code yet.

## 1. Why

The #33 suite assumes a **throwaway fixture brain**. But a real user's Claude Desktop is
configured to point at their **real** brain (`~/second-brain`), and pointing it at a fresh brain
means editing `claude_desktop_config.json` + restarting Desktop every run — enough friction that
the suite won't actually get run. And the scenarios **write** (`add_note` / `add_glossary_term`
commit to the vault), so we can't just aim them at the real brain and shrug. We need tests that
can be **added to the real brain and then removed**, leaving it byte-identical, with **zero
Desktop reconfiguration**.

## 2. The idea — a disposable git branch *is* the throwaway brain

Desktop's MCP server operates on whatever is checked out in the brain directory. So isolate the
entire run on a branch instead of standing up a new brain:

- **Setup (`setup.sh`):** assert `main` is clean, record its HEAD, `git checkout -b e2e-run`.
  Every note the scenarios create now commits onto that branch, never `main`. A fresh branch has
  no upstream, so `add_note`'s push step fails **harmlessly** — the note is created locally and
  nothing reaches the remote.
- **Run:** paste the #33 prompts into Desktop **unchanged** — same brain, same connector, no
  reconfiguration.
- **Teardown (`teardown.sh`):** `git checkout main`; `git branch -D e2e-run`; then restore the
  *derived* state git does not track — re-run `scripts/hydrate_cache.py` (drop the test notes from
  the search cache) and remove the orphaned `.embed.json` sidecars; finally **assert** `main`'s
  HEAD equals the recorded HEAD and `git status` is clean.

## 3. Correctness — leave no trace

- **git-tracked** artifacts (the test notes, the glossary term, the term's link-cascade edits to
  other notes) vanish with the branch delete.
- **derived** artifacts survive a branch delete because they are gitignored: the cache
  (`data/brain.db`) and the per-note `.embed.json` sidecars. Teardown re-hydrates the cache and
  removes orphan sidecars.
- teardown **asserts** the end state (HEAD unchanged, working tree clean, no orphan test files)
  and fails **loudly** if anything is off, rather than claiming a clean-up it did not achieve.

## 4. The #33 verifiers work as-is

They check "does *this* test note exist with *these* tags" (state-relative), so they run against
the real brain on the branch unchanged. The near-miss scenario is actually **stronger** here:
`ai-agents` already exists in the real vocabulary, so `ai-agent` near-misses it directly.

## 5. Caveats (honest scope)

- This tests the **real brain + current code** — good for "does my live Desktop setup work." It is
  NOT "what the generator emits to a brand-new user" (that is the fresh-brain path, still
  available and better for certifying the generator's output). Both are valid; this one fits
  running **without reconfiguring Desktop**.
- Requires a **clean `main`** before setup — uncommitted work would be carried onto the branch.
- Devkit-only tooling (bash + the existing `desktop-e2e/verify/` scripts); **not emitted** into a
  brain, no `emit-manifest` entry, no CI gate (it needs a human at Desktop, like #33).

## 6. Deliverables

- `desktop-e2e/setup.sh` and `desktop-e2e/teardown.sh`.
- `desktop-e2e/README.md` updated so the **branch-against-your-real-brain** flow is the primary
  path, with the fresh-fixture-brain flow kept as the alternative (for certifying a new user's
  brain).
- teardown's byte-identical assertion doubles as a standalone "did it clean up?" check.
