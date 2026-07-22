# Daily plan — 2026-07-23

**What this repo is (for a newcomer):** `second-brain-devkit` is a *generator*. It builds a personal
"second brain" — a plain-Markdown notes vault a human edits in Obsidian, plus a local SQLite
semantic-search index an AI reads — and ships it as a ready-to-run repo. Every change goes
prototype → vendor → one command, `python3 tools/ci.py` (14 automated gates).

**Last implemented:** #38 (a permission-denied source folder is no longer reported as empty) shipped
2026-07-20. #39 — the *embed-excluded block* (strip decorative ASCII from a note's embedding + content
hash) — is filed but not yet built; it stays queued behind today's learning.

**Focus / plan:**
- **Course — Kaggle 5-Day Agents, Day 1 (intro to agents):** start the guided course
  (https://www.kaggle.com/learn-guide/5-day-agents). Work Day 1 end-to-end and capture the
  transferable agent lessons for the second-brain's own AI-read path.
- **Tie-back:** map Day 1's agent concepts onto the brain — where the retrieval/MCP path is
  already agent-shaped and where a cleaner agent loop would help.
- **Queued build — #39 embed-excluded block:** marker (reuse `scripts/marked_block.py`) strips a
  decorative region from `canonical_body()` before embedding **and** from the content hash; prototype
  in golden → `vendor_golden.py` → `build_template.py` → `tools/ci.py` green + a new strip/hash gate.
- **Later (not today):** Agent Quality white-paper reading (Automated Metrics section) — resumes after
  the course.
- Parked (human): `add_pdf_guided` CLI form pass; Suite A Desktop; glossary Obsidian hand-test.

```
 course ▶ Kaggle 5-Day Agents — Day 1: intro to agents
            │
            ▼
 7/23 ▶ work Day 1 end-to-end → note agent lessons → map onto brain retrieval/MCP path
            │
            ▼
 then ▶ #39 embed-excluded block (queued) · Agent Quality reading (later)
```
