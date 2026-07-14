# Daily plan — 2026-07-14

**Focus:** Mon 07-13 closed the MCP arc — **#21** (negative/security suite), **#5** (`add_note`:
write a note from Claude Desktop, commit + push), and the note-quality gate (CI gate 9). It also
burned an hour on a "server hang" that turned out to be an **unclicked approval dialog** in Desktop.
Tue 07-14 makes the *glossary* writable from Desktop — but builds the cheap enabler first.

- **▶▶ #26 — wikilink-invariant embed input** (do first; it is what makes #25 sane): strip `[[…]]`
  markup from `note_view.canonical_body` so a link insertion leaves the embed input byte-identical
  and the **existing** `content_hash` gate skips the re-embed. A prose edit still re-embeds. Also
  closes a feedback loop the design already claimed: the system's own auto-links currently enter
  its own vectors. Migration: every `content_hash` changes → one full re-embed + regenerate the
  committed `test` fixtures.
- **#25 — `add_glossary_term` MCP tool:** scaffold the term **and** run the whole-vault auto-link
  sweep — the cascade **is the feature**. Stage only what the sweep itself touched (never `-A`), so
  a user's in-progress work still can't ride along. Needs `aliases`, collision refusal, and a
  "what earns a term" bar — a controlled vocabulary an LLM can mint into freely isn't controlled.
- **Carrying:** **#24** (four real hang vectors — the embedder's `urlopen()` has **no timeout**;
  a cold Ollama load can hang the server forever). Not the cause of yesterday's stall, but live.
- **Loop:** prototype-first in `second-brain-test/` → vendor → `tools/ci.py` (**9** gates) + the
  mcp tier. Every new assertion negative-tested — a test that can't go red is decoration.

```
 mon 07-13 ✅ #21 negative suite · #5 add_note (commit+push) · note-gate (CI 9/9)
            └─ detour: "server hang" = Desktop approval dialog nobody clicked
                 │
                 ▼
 tue 07-14  ▶▶ #26 wikilink-invariant view ──► #25 add_glossary_term (cascade = feature)
            ‖ carrying: #24 hang vectors (urlopen has no timeout)
 guards: tools/ci.py (9) + mcp tier green · prototype-first in second-brain-test/
```
