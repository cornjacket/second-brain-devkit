# Daily plan — 2026-07-19

**What this repo is (for a newcomer):** `second-brain-devkit` is a *generator*. It builds a personal
"second brain" — a plain-Markdown notes vault a human edits in Obsidian, plus a local SQLite
semantic-search index an AI reads — and ships it as a ready-to-run repo. Work here improves the
generator and the features every generated brain inherits; every change goes prototype → vendor →
one command, `python3 tools/ci.py` (13 automated gates).

**Last implemented:** #7 PDF-ingestion design locked (M0) — `docs/pdf-ingestion.md` captures the
chunk-and-embed plan (bolt-on schema, PDFs stored git-ignored in the vault, `pypdf` optional dep,
a folder-first `add_pdf` with a chat-or-elicitation selection UI). Design only; nothing built yet.

**Focus / plan:**
- Finish the #7 scoping walkthrough — Section 4 (the step-by-step) — and lock the M0 step list.
- Start **M1**: prototype `chunker.py` (text → overlapping token-window chunks with page + char
  spans) and `pdf_extract.py` (`pypdf`, optional dep) against a tiny fixture PDF. Deterministic,
  model-free, unit-tested — the pieces that need no database and no embedding model.
- Guardrail: prototype in the golden → `vendor_golden.py` → `build_template.py` → `tools/ci.py` green.
- Still parked (human-driven, no Claude work): Suite A live Desktop pass; glossary Obsidian hand-test.

```
 done ▶ #7 M0 design doc · both READMEs fixed (hybrid search shipped) · #23 closed · #37 backlogged
          │
          ▼
 7/19 ▶ finish #7 Section-4 walkthrough ──► build M1: chunker.py + pdf_extract.py (+ fixture PDF)
      └─ parked (human): Suite A Desktop pass · glossary Obsidian test
 guardrail: prototype → vendor → tools/ci.py green (13 gates)
```
