# Daily plan — 2026-07-18

**What this repo is (for a newcomer):** `second-brain-devkit` is a *generator*. It builds a personal
"second brain" — a plain-Markdown notes vault a human edits in Obsidian, plus a local SQLite
semantic-search index an AI reads — and ships it as a ready-to-run repo. Working here means improving
the generator and the features every generated brain inherits. The rhythm is always the same:
prototype a feature by hand in the sibling `second-brain-test/`, copy it in, and prove it with one
command — `python3 tools/ci.py` (13 automated gates).

**Where we left off:** the Desktop e2e kit is now **emitted into every brain** (#35) alongside the
disposable-branch harness (#34) and the pure-client cross-session test (#36). Suite B (pure-client)
ran live 4/4 against the real `~/second-brain`. Today we folded its two findings back into the kit.

**Today — folded in the Suite B findings (done); Suite A + carries postponed to the end:**
- **✅ Finding 2a — `list_tags` cap robustness.** The pure-client tag query now calls
  `list_tags` with `match="zephyr"`, so the count-1 canary tag survives on a brain with a large
  vocabulary (the filter runs before the 50-item cap). Prototyped → vendored → CI 13/13 green.
- **✅ Finding 2b — disposable-branch push leak (was mis-scoped as a "harmless no-op").** `add_note`
  runs `git push origin <branch>`, which needs no upstream, so the disposable `e2e-run` branch was
  really pushed to the real remote and orphaned there. Fix: teardown now deletes the branch on the
  remote too; setup.sh's wrong comment corrected; yesterday's orphaned `origin/e2e-run` removed.

**Postponed — queued for a later session:**
- **▶ Task: Run Suite A live on the real brain** (the 5-scenario script-verified kit) — the remaining
  human Desktop pass: `~/second-brain/desktop-e2e/setup.sh` → paste `prompts/01..05` → `run_all.py`
  → `teardown.sh`. Proves the write path + tool surface (incl. the #32 near-miss TAG HINT) through
  the real client.
- **Carry:** glossary Obsidian hand-test (flashcard + graph view); **#23** plugin research (notes
  only) — brain-as-one-Claude-Code-plugin vs the skill-install + MCP-registration two-step.

```
 shipped ▶ #34 harness · #35 emit · #36 pure-client — Suite B ran LIVE 4/4 on the real brain
              │
              ▼
 today   ✅ folded in Suite B findings: list_tags match filter · disposable-branch push leak fixed
              │
              ▼
 postponed ▶ run Suite A live on the real brain  ·  carry: glossary Obsidian test · #23 plugin research
 guardrail: any code change still goes prototype → vendor → tools/ci.py green
```
