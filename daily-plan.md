# Daily plan — 2026-07-21

**What this repo is (for a newcomer):** `second-brain-devkit` is a *generator*. It builds a personal
"second brain" — a plain-Markdown notes vault a human edits in Obsidian, plus a local SQLite
semantic-search index an AI reads — and ships it as a ready-to-run repo. Every change goes
prototype → vendor → one command, `python3 tools/ci.py` (14 automated gates).

**Last implemented:** #38 (a permission-denied source folder is no longer reported as empty) shipped
2026-07-20; and #39 filed — an *embed-excluded block* to keep decorative text (ASCII diagrams) out of
a note's embedding, surfaced by dogfooding the real brain.

**Focus / plan:**
- **Build #39 — the embed-excluded block:** a marker (reuse `scripts/marked_block.py`) that strips a
  decorative region from `canonical_body()` before embedding **and** from the content hash — so ASCII
  diagrams live in a note without polluting its vector or tripping stale-embedding detection.
- Provenance: dogfooding a large college-planning note in the real brain, an ASCII roadmap overflowed
  nomic's 2048-token context (500 on commit); token-dense notes also repeatedly hit the ceiling and
  needed splitting. Line-count is the wrong proxy — measure tokens.
- Guardrail: prototype in the golden → `vendor_golden.py` → `build_template.py` → `tools/ci.py` green;
  add a CI gate for strip-before-embed + hash invariance.
- Parked (human): `add_pdf_guided` CLI form pass; Suite A Desktop; glossary Obsidian hand-test.

```
 done ▶ #38 permission-denied ≠ empty (7/20) · #39 filed (embed-excluded block)
          │
          ▼
 7/21 ▶ #39: marker → strip decorative text from embedding + hash (marked_block.py)
      guardrail: prototype → vendor → tools/ci.py green + new gate
```
