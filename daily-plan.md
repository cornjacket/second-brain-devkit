# Daily plan — 2026-07-17

**What this repo is (for a newcomer):** `second-brain-devkit` is a *generator*. It builds a personal
"second brain" — a plain-Markdown notes vault a human edits in Obsidian, plus a local SQLite
semantic-search index an AI reads — and ships it as a ready-to-run repo. Working here means improving
the generator and the features every generated brain inherits. The rhythm is always the same:
prototype a feature by hand in the sibling `second-brain-test/`, copy it in, and prove it with one
command — `python3 tools/ci.py` (13 automated gates).

**Where we left off:** shipped **#34** (disposable-branch e2e harness — run the Desktop test suite
against the real `~/second-brain` on a throwaway branch, revert byte-identical), then **#35**: the
whole Desktop e2e suite (prompts + verifiers + setup/teardown) now **emits into every generated
brain**, so a user who creates a brain can self-verify their Claude Desktop connection with no devkit
checkout. Prototyped in the golden, wired into `emit-manifest.toml`, CI 13/13 green.

**Today — #35 shipped; now use it, then carry-overs:**
- **▶▶ Run the Desktop e2e kit on the REAL brain** (the human-in-the-loop pass, still not done):
  `~/second-brain/desktop-e2e/setup.sh` → paste the 5 prompts into Desktop → `run_all.py` →
  `teardown.sh`. First real end-to-end pass in the actual client (needs `update_brain.py` to land
  `desktop-e2e/` in `~/second-brain` first).
- **#36 pure-client cross-session retrieval test** (built + emitted): Desktop-only black-box —
  seed canary values in one chat, delete it, retrieve in a fresh chat (proves retrieval + persistence
  through the real client, not chat memory). Ships at `<brain>/desktop-e2e/pure-client/`; the live
  Desktop pass is part of the run-on-real-brain step below.
- **Glossary Obsidian hand-test** (carry, needs a human): a glossary term renders as a flashcard and
  shows in the graph view.
- **#23 plugin research** (if time; notes only, no code): could the brain install as one Claude Code
  *plugin* instead of the skill-install + MCP-registration two-step?

```
 shipped ▶ #34 disposable-branch harness ─► #35 emit the e2e suite into every brain — CI 13/13 green
              │
              ▼
 today   ▶▶ RUN the Desktop e2e kit on the REAL brain (human pastes prompts) — first live pass
         └─ carry: glossary Obsidian hand-test · #23 plugin research (notes only)
 guardrail: any code change still goes prototype → vendor → tools/ci.py green
```
