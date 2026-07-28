# Daily plan — 2026-07-28

**What this repo is (for a newcomer):** `second-brain-devkit` is a *generator*. It builds a personal
"second brain" — a plain-Markdown notes vault a human edits in Obsidian, plus a local SQLite
semantic-search index an AI reads — and ships it as a ready-to-run repo. Every change goes
prototype → vendor → one command, `python3 tools/ci.py` (15 automated gates).

**Last implemented:** #39 — the *embed-excluded block* — shipped 2026-07-28. Decorative regions
fenced in `<!-- second-brain:no-embed:begin/end -->` are cut from `canonical_body()`, so they leave
the embedding **and** the content hash together; redrawing a diagram now costs no re-embed and no
`doctor` staleness. Two advisory pre-commit warnings (unpaired marker, near the context budget)
measure **tokens, not lines**. CI gate 15 added; all 15 green.

**Focus / plan:**
- **Done:** #39 end-to-end — golden prototype → `vendor_golden.py` → `build_template.py` →
  `tools/ci.py` 15/15 → `docs/embed-excluded-block.md`.
- **Pick the next build** from PLAN.md — #8a (turn auto-linking on via `--apply` against a real
  brain) is the one marked *ready now*.
- Parked (human, unchanged): `add_pdf_guided` CLI form pass; Suite A Desktop; glossary Obsidian
  hand-test.

```
 shipped ▶ #39 embed-excluded block
   golden prototype ──▶ vendor_golden.py ──▶ build_template.py ──▶ tools/ci.py 15/15
   guardrail held: the block leaves BOTH the embedding and the content hash;
                   the UNMARKED path is bit-identical, so no existing brain reads stale
 next ▶ choose from PLAN.md (#8a autolink --apply is ready now)
```
