# Daily plan — 2026-07-18

**What this repo is (for a newcomer):** `second-brain-devkit` is a *generator*. It builds a personal
"second brain" — a plain-Markdown notes vault a human edits in Obsidian, plus a local SQLite
semantic-search index an AI reads — and ships it as a ready-to-run repo. Working here means improving
the generator and the features every generated brain inherits. The rhythm is always the same:
prototype a feature by hand in the sibling `second-brain-test/`, copy it in, and prove it with one
command — `python3 tools/ci.py` (13 automated gates).

**Where we left off:** the Desktop e2e kit is now **emitted into every brain** (#35) alongside the
disposable-branch harness (#34) and the pure-client cross-session test (#36). Yesterday we ran
**Suite B (pure-client) live against the real `~/second-brain` for the first time — 4/4 PASS**: the
brain retrieves across three substrates (search / glossary lookup / tag list) in a fresh session with
the ingest chat deleted, and returns a truthful "not found" for the negative control. Teardown
restored the brain byte-identical. CI 13/13 green; all repos pushed.

**Today — run Suite A live, then fold in yesterday's findings:**
- **▶▶ Run Suite A (the 5-scenario script-verified kit) live on the real brain** — the remaining
  human Desktop pass: `~/second-brain/desktop-e2e/setup.sh` → paste `prompts/01..05` → `run_all.py`
  → `teardown.sh`. Proves the write path + tool surface (incl. the #32 near-miss TAG HINT) through
  the real client.
- **Fold in two findings from the Suite B run:**
  - `list_tags` has a cap of 50; query-03 relied on the vocabulary (21) being under it. Add a
    `match=` filter to the pure-client tag query so it stays robust on a large brain.
  - Desktop reports "pushed" on the disposable branch though it is a harmless no-op (no upstream) —
    decide whether to clarify/suppress that in the flow or just document it.
- **Carry:** glossary Obsidian hand-test (flashcard + graph view); **#23** plugin research (notes
  only) — brain-as-one-Claude-Code-plugin vs the skill-install + MCP-registration two-step.

```
 shipped ▶ #34 harness · #35 emit · #36 pure-client — Suite B ran LIVE 4/4 on the real brain
              │
              ▼
 today   ▶▶ run Suite A live on the real brain ──► fold in findings (list_tags match filter · "pushed" no-op)
         └─ carry: glossary Obsidian hand-test · #23 plugin research (notes only)
 guardrail: any code change still goes prototype → vendor → tools/ci.py green
```
