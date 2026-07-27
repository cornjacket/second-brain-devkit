# Daily plan — 2026-07-23

**What this repo is (for a newcomer):** `second-brain-devkit` is a *generator*. It builds a personal
"second brain" — a plain-Markdown notes vault a human edits in Obsidian, plus a local SQLite
semantic-search index an AI reads — and ships it as a ready-to-run repo. Every change goes
prototype → vendor → one command, `python3 tools/ci.py` (14 automated gates).

**Last implemented:** #38 (a permission-denied source folder is no longer reported as empty) shipped
2026-07-20. #39 — the *embed-excluded block* (strip decorative ASCII from a note's embedding + content
hash) — is filed but not yet built; it is the next build.

**Focus / plan:**
- **Build #39 — embed-excluded block:** marker (reuse `scripts/marked_block.py`) strips a
  decorative region from `canonical_body()` before embedding **and** from the content hash; prototype
  in golden → `vendor_golden.py` → `build_template.py` → `tools/ci.py` green + a new strip/hash gate.
- Parked (human): `add_pdf_guided` CLI form pass; Suite A Desktop; glossary Obsidian hand-test.

```
 build ▶ #39 embed-excluded block
   golden prototype ──▶ vendor_golden.py ──▶ build_template.py ──▶ tools/ci.py (+ strip/hash gate)
   guardrail: strip the decorative region from BOTH the embedding and the content hash
```
