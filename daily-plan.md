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

**Today — cleared the coding backlog:**
- **✅ Finding 2a — `list_tags` cap robustness.** The pure-client tag query now calls
  `list_tags` with `match="zephyr"`, so the count-1 canary tag survives on a brain with a large
  vocabulary (the filter runs before the 50-item cap). Prototyped → vendored → CI 13/13 green.
- **✅ Finding 2b — disposable-branch push leak (was mis-scoped as a "harmless no-op").** `add_note`
  runs `git push origin <branch>`, which needs no upstream, so the disposable `e2e-run` branch was
  really pushed to the real remote and orphaned there. Fix: teardown now deletes the branch on the
  remote too; setup.sh's wrong comment corrected; yesterday's orphaned `origin/e2e-run` removed.
- **✅ #23 plugin research — CLOSED.** Verdict: a Claude Code plugin can't collapse the skill + MCP
  two-step (its MCP server never reaches the Desktop **Chat** tab where a brain is used) and is
  Claude-only, so it fragments Gemini. Plugin route **declined**; `.mcpb`/Connector Desktop
  extension **deferred** behind a trigger (first external Desktop user). → `docs/plugin-packaging.md`.

**Deferred — human-driven, no Claude work available:**
- **Glossary Obsidian hand-test** (flashcard + graph view) — a manual in-Obsidian check. *Deferred.*
- **Run Suite A live on the real brain** (the 5-scenario script-verified kit) — needs a human
  pasting `prompts/01..05` into Claude Desktop. *Deferred.*

```
 shipped ▶ #34 harness · #35 emit · #36 pure-client — Suite B ran LIVE 4/4 on the real brain
              │
              ▼
 today   ✅ Suite B findings folded in (list_tags filter · push-leak fix) · ✅ #23 plugin research CLOSED
              │
              ▼
 deferred ▶ glossary Obsidian hand-test · Suite A live Desktop pass  (both human-driven — no Claude work left)
 guardrail: any code change still goes prototype → vendor → tools/ci.py green
```
