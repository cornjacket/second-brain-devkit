# Daily plan — 2026-07-20

**What this repo is (for a newcomer):** `second-brain-devkit` is a *generator*. It builds a personal
"second brain" — a plain-Markdown notes vault a human edits in Obsidian, plus a local SQLite
semantic-search index an AI reads — and ships it as a ready-to-run repo. Work here improves the
generator and the features every generated brain inherits; every change goes prototype → vendor →
one command, `python3 tools/ci.py` (14 automated gates).

**Last implemented:** #7 PDF ingestion **shipped** (M1–M6) and its interactive follow-up vendored —
`add_pdf_guided` walks folder → PDF → PARA as client-rendered MCP elicitation forms, falling back to
the `list_inbox_pdfs`/`add_pdf` chat flow where the client can't render them.

**Focus / plan:**
- **Fix the source-folder permission bug (task #1):** `list_pdfs` reports an unreadable folder as
  empty — `is_dir()` is True but `glob` swallows `PermissionError` and yields `[]`. Surface a
  `readable` signal through `list_inbox_pdfs`, preflight it in `doctor.py`.
- Found by dogfooding, not by a test: ingesting a real PDF hit macOS TCC on `~/Downloads` (a default
  source folder), and the silent empty listing read as "no PDFs here". Worth a regression test that
  a denied folder is distinguishable from an empty one.
- Guardrail: prototype in the golden → `vendor_golden.py` → `build_template.py` → `tools/ci.py` green.
- Still parked (human-driven, no Claude work): `add_pdf_guided` live-CLI elicitation pass — today's
  client fell back, so the form path remains unexercised; Suite A live Desktop pass; glossary
  Obsidian hand-test.

```
 done ▶ #7 PDF ingestion SHIPPED (M1-M6) · add_pdf_guided vendored · 14 CI gates green
          │
          ▼
 7/20 ▶ task #1: permission-denied ≠ empty ──► list_pdfs + list_inbox_pdfs + doctor preflight
      └─ parked (human): guided-picker CLI form pass · Suite A Desktop · glossary Obsidian
 guardrail: prototype → vendor → tools/ci.py green (14 gates)
```
