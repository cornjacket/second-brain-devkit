# Desktop e2e against your real brain — disposable-branch harness (task #34)

**Status:** **BUILT** (2026-07-17) — `desktop-e2e/setup.sh` + `teardown.sh`, README primary path
updated. Extends the #33 suite ([docs/desktop-e2e.md](desktop-e2e.md)). Smoke-tested end-to-end
against the real `~/second-brain` (branch create → committed note → teardown → byte-identical
restore, doctor green); the human-driven Desktop pass is still to run.

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

- **Setup (`setup.sh`):** assert `main` is clean **and its search index already matches the vault**
  (`scripts/doctor.py` green — a known-good baseline, so we don't blame the test for pre-existing
  drift), record HEAD, `git checkout -b e2e-run`. Every note the scenarios create now commits onto
  that branch, never `main`. A fresh branch has no upstream, so `add_note`'s push step fails
  **harmlessly** — the note is created locally and nothing reaches the remote.
- **Run:** paste the #33 prompts into Desktop **unchanged** — same brain, same connector, no
  reconfiguration. (As each note is written, the brain's own commit hooks embed it, so the branch's
  index stays consistent *during* the run.)
- **Teardown (`teardown.sh`):** `git checkout main`; `git branch -D e2e-run`; then **rebuild the
  derived search layer to match the restored vault** — remove the test notes' orphan `.embed.json`
  sidecars and rebuild `data/brain.db` (re-embed + `scripts/hydrate_cache.py`) so no test embeddings
  linger; finally **assert** HEAD equals the recorded HEAD, `git status` is clean, and
  `scripts/doctor.py` is green.

## 3. Correctness — the derived index MUST follow the vault, or the brain is corrupted

The search layer is **derived** state git does not version: the per-note `.embed.json` vectors and
the `data/brain.db` index (vectors + FTS). It must always describe *whatever vault is currently
checked out*. A branch swap changes the `.md` files but **not** this derived layer, so if
setup/teardown don't resync it, you get a **corrupted brain** — three concrete failure modes:

- **Phantom hits** — after teardown reverts the vault, `data/brain.db` still holds the test notes'
  vectors, so search keeps returning "Planning agents" / "ablation study" that no longer exist.
- **Orphan sidecars** — the test notes' gitignored `.embed.json` files survive the branch delete,
  litter `vault/`, and can re-poison a later `hydrate_cache`.
- **Missing embeddings** (the reverse) — a note present on a branch but never embedded looks
  unsearchable until the index is rebuilt.

So both scripts own the derived layer, not just the git state: **setup** proves the baseline index
matches the vault (a clean target to restore to), and **teardown** clears the old embeddings + index
and rebuilds them from the restored vault, then **verifies `doctor.py` is green** — no phantom, no
orphan, no stale vector. Teardown fails **loudly** if HEAD moved, the tree is dirty, or the index
does not match, rather than claiming a clean-up it did not achieve.

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
