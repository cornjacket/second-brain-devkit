# Daily plan — 2026-07-16

**Focus:** Wed 07-15 cleared the heavy items — **#25** (`add_glossary_term`, validated live from
Desktop with the RRF term), **#30** (doctor detects a stale embedding, CI gate 11), and **#24**
(the four server hang vectors, CI gate 12) — all shipped to the real brain. What's left is lighter
and mostly about the *edges* of the tool surface, not new machinery.

- **▶▶ #27 — bounded, filterable list tools + the missing `list_tags`.** The list tools return
  *everything*; unusable at scale. Filter/rank, **not** pagination (an agent handed "page 1 of 12"
  treats it as the whole truth). No silent truncation — every capped reply says what it omitted.
  And expose the **tag vocabulary** a Desktop assistant is currently blind to (it invents
  near-miss tags today). Prototype in the golden → vendor → mcp tier.
- **Then #23 — investigate the Claude Code *plugin* path** (docs/research, no code): can one plugin
  ship the skill + MCP server as a single installable unit? Key unknown: does a plugin-bundled MCP
  server reach Claude *Desktop*, or only Claude Code? Decide, write it down; "not worth it" is a
  valid outcome.
- **Human-blocked (carry):** the **#28 review** (§6 — judgement calls) and the glossary
  flashcard/graph **Obsidian hand-test** (see the golden/brain plan).
- **Loop:** prototype-first → `tools/ci.py` (**12** gates) + mcp tier. Every assertion
  negative-tested.

```
 wed 07-15 ✅ #25 (glossary write, live) · #30 (doctor stale, gate 11) · #24 (hang, gate 12)
                 │
                 ▼
 thu 07-16  ▶▶ #27 list tools + list_tags ──► #23 plugin investigation (docs only)
            ‖ human-blocked: #28 review · glossary flashcard/graph Obsidian test
 guards: tools/ci.py (12) + mcp tier green · prototype-first in second-brain-test/
```
