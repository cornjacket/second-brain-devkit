# Daily plan — 2026-07-06

**Focus:** The **MCP server v1 shipped and is Claude Desktop-verified** (weekend of
07-04), along with OQ-5 **layer 2 in-place hydrate**. Monday shifts from *building* the
server to *hardening the mechanism* and closing the lifecycle gap: add CI coverage for
MCP (byte-diff alone let a real regression through), then `tools/update_brain.py`.
Retrieval quality is designed and queued. Same loop: prototype in golden → vendor →
template → `tools/ci.py` green.

- **CI coverage for MCP (tasks #1, #2).** The Claude Desktop `outputSchema` regression
  proved CI byte-diffs `mcp_server.py` but never *runs* it. Layer 1: `py_compile` every
  emitted script in `tools/ci.py` (hermetic, zero new deps). Layer 2: opt-in
  `tools/check_mcp_server.py` on the `test` backend — assert 2 tools, **no
  `outputSchema`**, `get_note` path-guard, search works; SKIP when `mcp` absent.
- **Lifecycle G4 — `tools/update_brain.py`.** Non-destructive, manifest-driven
  re-emit of tooling only (scripts/README/hooks/requirements), leaving vault/data/
  config/history untouched, `--apply`-gated — so populated brains pull devkit
  improvements (MCP, WAL, fixes) without delete+regenerate.
- **Retrieval quality (designed — `docs/retrieval-quality.md`, task #3).** Hybrid
  lexical+vector via SQLite **FTS5** + Reciprocal Rank Fusion; nomic
  `search_document:`/`search_query:` prefixes. Build only when a *populated* brain shows
  real recall failures — not the "magic number" false alarm.
- Guards stay green (partition, structural diff, forbidden-ref); every change via `ci.py`.

```
 weekend 07-04 ✅  layer 2 in-place hydrate · MCP server v1 (stdio) live in Claude Desktop
                   outputSchema fix · magic-number test note · retrieval-quality design
                                   │
                                   ▼
 mon 07-06   CI coverage for MCP  ──▶  update_brain.py (G4)  ──▶  [backlog: hybrid FTS5]
             #1 py_compile · #2 behavioral    non-destructive upgrade      task #3

 loop:  golden ─vendor→ tests/golden ─build→ template ─ci.py→ green
```
