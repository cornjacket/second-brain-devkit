# Daily plan — 2026-07-15

**Focus:** Tue 07-14 was heavy — shipped the full write path (**#5** `add_note`, **#25**
`add_glossary_term`), **#26** (wikilink-invariant embedding), **#28** (index-poison bug),
**#29** (config-matrix gate 10), **#31** (score-labelling), and validated the glossary write
path live from Claude Desktop (RRF term, committed + pushed + link-cascaded). Wed 07-15 pays
down the debt the feature work left behind, then hardens the server.

- **▶▶ #30 — stale-vector detection in `doctor` (do first).** The honest completion of #26:
  `update_brain` ships a new canonical view but never re-embeds, so an upgraded brain silently
  holds vectors from the old view. `doctor` should recompute each note's `content_hash`, compare
  to the sidecar's, and `--repair` the mismatch. Negative-test it (today `doctor` says "healthy"
  while holding stale vectors — the false-green to kill).
- **#24 — MCP hang vectors.** The live one: `embedder.urlopen()` has **no timeout**, so a cold
  Ollama load can hang the server forever (reachable from search AND `git commit`). Plus
  `stdin=DEVNULL`, ssh `BatchMode`, and catch `TimeoutExpired`. → docs/mcp-hardening.md.
- **#27 — bounded list tools + `list_tags`** if time: filter/rank not pagination; no silent
  truncation; expose the tag vocabulary a Desktop assistant is currently blind to.
- **Carrying (need a human):** the **#28 review** (§6 — judgement calls, not code) and the
  glossary flashcard/graph tail (Obsidian hand-test — see the brain's plan).
- **Loop:** prototype-first in `second-brain-test/` → vendor → `tools/ci.py` (**10** gates) +
  the mcp tier. Every new assertion negative-tested.

```
 tue 07-14 ✅ #5 · #25 · #26 · #28 · #29(gate10) · #31 · RRF term live from Desktop
                 │
                 ▼
 wed 07-15  ▶▶ #30 stale-vector doctor ──► #24 hang vectors (urlopen timeout) ──► #27 list tools
            ‖ carrying (human): #28 review · glossary flashcard/graph tail (Obsidian)
 guards: tools/ci.py (10) + mcp tier green · prototype-first in second-brain-test/
```
