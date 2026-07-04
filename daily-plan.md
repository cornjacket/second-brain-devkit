# Daily plan — 2026-07-06

**Focus:** Start building the **MCP server** (G6 secondary path) from Friday's
scoping — but land its hard prerequisite first: **OQ-5 layer 2, the in-place
hydrate**, since the server is the long-lived reader that makes the current
`unlink()`+rebuild a real hazard. Same loop: prototype in the golden → vendor →
template → `tools/ci.py` green.

- **Layer 2 — in-place hydrate (do first):** replace `hydrate_cache.py`'s
  `unlink()`+rebuild with an in-transaction rebuild (`DELETE FROM notes` / temp-table
  swap) so a live reader sees old rows until commit, then new, atomically.
  `doctor --repair` inherits the fix.
- **MCP server v1 (stdio + Claude Desktop):** refactor `search_vault.py` to expose a
  reusable `search()`, then a thin `scripts/mcp_server.py` exposing
  `search_second_brain` (+ maybe `get_note`). Reuse `embedder`/`db`/`search`.
  Prototype live against Claude Desktop before productizing.
- **Settle OQ-6 as they come up:** MCP SDK/version, get_note in v1?, registration
  (detect+instruct, `--apply`-gated). Keep the SDK an isolated optional dep — core +
  CI stay lean/stdlib-only.
- Guards stay green (manifest partition, structural diff, forbidden-ref); every
  change lands through `tools/ci.py`.

```
 fri 07-03 ✅  doctor.py (live-verified) · WAL layer 1 · --nudge/--uninstall
               real brain rebuilt + nudge installed · MCP scoped (docs/mcp-server.md)
                                   │
                                   ▼
 mon 07-06   layer 2 (in-place hydrate)  ──▶  mcp_server.py v1 (stdio, Claude Desktop)
             (unblocks the long-lived reader)     search_second_brain [+ get_note]

 loop:  golden ─vendor→ tests/golden ─build→ template ─ci.py→ green
```
