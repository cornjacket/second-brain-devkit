# Daily plan — 2026-07-23

**What this repo is (for a newcomer):** `second-brain-devkit` is a *generator*. It builds a personal
"second brain" — a plain-Markdown notes vault a human edits in Obsidian, plus a local SQLite
semantic-search index an AI reads — and ships it as a ready-to-run repo. Every change goes
prototype → vendor → one command, `python3 tools/ci.py` (14 automated gates).

**Last implemented:** #38 (a permission-denied source folder is no longer reported as empty) shipped
2026-07-20. #39 — the *embed-excluded block* (strip decorative ASCII from a note's embedding + content
hash) — is filed but not yet built; it stays queued behind today's reading.

**Focus / plan:**
- **Reading — Agent Quality:** through pg 21, now at the **Automated Metrics** section. Continue from
  there; capture the transferable eval lessons (what an automated metric buys vs. what it misses) for
  the second-brain's own retrieval-quality work.
- **Tie-back:** map the Automated Metrics ideas onto the brain — how would we score retrieval/answer
  quality here, and does it sharpen the #8b auto-link calibration or a doctor-style eval gate.
- **Queued build — #39 embed-excluded block:** marker (reuse `scripts/marked_block.py`) strips a
  decorative region from `canonical_body()` before embedding **and** from the content hash; prototype
  in golden → `vendor_golden.py` → `build_template.py` → `tools/ci.py` green + a new strip/hash gate.
- Parked (human): `add_pdf_guided` CLI form pass; Suite A Desktop; glossary Obsidian hand-test.

```
 read ▶ Agent Quality — pg 21, at "Automated Metrics"
          │
          ▼
 7/23 ▶ finish Automated Metrics → note eval lessons → map onto brain retrieval quality
          │
          ▼
 then ▶ #39 embed-excluded block (queued): strip decorative text from embedding + hash
```
