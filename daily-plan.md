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

**Today — mostly the acceptance work automation can't do (a human at the app):**
- **Run the Desktop e2e kit end-to-end** (`desktop-e2e/`): generate a throwaway brain, connect Claude
  Desktop to it, paste the 5 prompts, run `verify/run_all.py`. This is the only way to confirm the
  features work in the *real* Desktop client (the automated tests use a different client).
- **Glossary Obsidian hand-test** (carried over, needs a human): open the vault in Obsidian and check a
  glossary term renders as a flashcard and appears in the graph view.
- **Investigate the "plugin" path (#23) — research + notes only, no code:** could the brain install as a
  single Claude Code *plugin* instead of today's two-step (skill install + MCP registration)? Key
  unknown: does a plugin-bundled server even reach Claude *Desktop*? Decide and write it down — "not
  worth it" is a perfectly good answer.

```
 shipped ▶ tag hygiene (#32) + Desktop e2e kit (#33) — CI 13/13 green
              │
              ▼
 today   run the Desktop e2e kit in the real app ─► glossary Obsidian hand-test
         └─ side quest: #23 plugin research (notes only, no code)
 guardrail: any code change still goes prototype → vendor → tools/ci.py green
```
