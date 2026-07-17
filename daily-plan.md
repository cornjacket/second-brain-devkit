# Daily plan — 2026-07-17

**What this repo is (for a newcomer):** `second-brain-devkit` is a *generator*. It builds a personal
"second brain" — a plain-Markdown notes vault a human edits in Obsidian, plus a local SQLite
semantic-search index an AI reads — and ships it as a ready-to-run repo. Working here means improving
the generator and the features every generated brain inherits. The rhythm is always the same:
prototype a feature by hand in the sibling `second-brain-test/`, copy it in, and prove it with one
command — `python3 tools/ci.py` (13 automated gates).

**Where we left off:** the last push shipped two things into every brain — **tag hygiene** (tools that
find and fix a messy tag vocabulary, task #32) and a **Claude Desktop end-to-end test kit** (ready-made
prompts + checker scripts, task #33). CI is green.

**Today — top of the list is building #34, then using it:**
- **▶▶ Build #34 — the disposable-branch e2e harness** (`desktop-e2e/setup.sh` + `teardown.sh`). It
  lets the #33 Desktop test kit run against the **real** `~/second-brain` on a throwaway git branch —
  **no Desktop reconfiguration** — then tear down to a byte-identical brain. This is the blocker:
  today, running the kit means standing up a fresh brain and re-pointing Desktop at it, which is why
  it hasn't happened. → [docs/desktop-e2e-disposable-branch.md](docs/desktop-e2e-disposable-branch.md).
- **Then run the Desktop e2e kit** on the real brain via that branch — paste the 5 prompts in Desktop,
  run `verify/run_all.py`: the first real end-to-end pass in the actual client.
- **Glossary Obsidian hand-test** (carry, needs a human): a glossary term renders as a flashcard and
  shows in the graph view.
- **#23 plugin research** (if time; notes only, no code): could the brain install as one Claude Code
  *plugin* instead of the skill-install + MCP-registration two-step?

```
 shipped ▶ tag hygiene (#32) + Desktop e2e kit (#33) — CI 13/13 green
              │
              ▼
 today   ▶▶ BUILD #34 (disposable-branch setup/teardown) ──► run the e2e kit on the REAL brain
         └─ carry: glossary Obsidian hand-test · #23 plugin research (notes only)
 guardrail: any code change still goes prototype → vendor → tools/ci.py green
```
