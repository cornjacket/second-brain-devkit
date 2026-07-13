# Daily plan — 2026-07-13

**Focus:** Sun 07-12 closed the glossary arc — **#19** (namespace + scan + auto-linking, inc 1–3)
and **#20** (glossary-over-MCP tools) shipped, alongside the **#3** hybrid-search toggle; the real
brain was upgraded live via `update_brain`. Mon 07-13 closes the **MCP coverage** arc with **#21**,
then mops up the small glossary tail.

- **▶▶ #21 — MCP negative/security tests** (`check_mcp_server.py`, mcp-gated): `get_note`
  path-traversal refusals (absolute-outside, `..`-escape — but a `..` that stays inside is allowed),
  plus the now-unblocked glossary isolation — search-excludes-glossary end-to-end, glossary tools are
  embedding-free (work with `data/brain.db` removed), and substrate disjointness.
- **Glossary tail (mostly free):** a short flashcards + graph-color closeout in `glossary/README.md`
  (Spaced Repetition plugin + a `path:glossary/` color group) — docs, no code.
- **Stretch:** #5 `add_note` MCP write tool, or #8 auto-link `--apply` calibration on the real brain.
- **Loop:** anything emitted goes prototype-first in `second-brain-test/` → vendor → `tools/ci.py`
  (8 gates) + the mcp tier; #21 is harness-side (devkit-only).

```
 sun 07-12 ✅ #19 glossary (namespace·scan·autolink) + #20 glossary-MCP  ·  real brain upgraded
                 │
                 ▼
 mon 07-13  ▶▶ #21 MCP negative/security (traversal + glossary isolation) ──► glossary flashcard/graph tail
            ‖ stretch: #5 add_note  ·  #8 auto-link --apply (real brain)
 guards: tools/ci.py (8) + mcp tier green · prototype-first in second-brain-test/
```
