# Daily plan — 2026-07-28

**What this repo is (for a newcomer):** `second-brain-devkit` is a *generator*. It builds a personal
"second brain" — a plain-Markdown notes vault a human edits in Obsidian, plus a local SQLite
semantic-search index an AI reads — and ships it as a ready-to-run repo. Every change goes
prototype → vendor → one command, `python3 tools/ci.py` (16 automated gates).

**Last implemented:** #40 — an upgraded brain now receives its *documentation*, not just its code.
`CLAUDE.md` and `README.md` are both managed blocks now; a brain that predates the markers is
named loudly and adoptable via `--adopt`, which keeps the old file verbatim. Dogfooded on
`~/second-brain`: adoption surfaced a local `task-system` block a wholesale replace would have
deleted, and the README turned out to be 142 lines behind — which is what corrected the design.
**"A human will notice" guards against wrong content, never against missing content.**

**Focus / plan (all three shipped today):**
- **#39** embed-excluded block → CI gate 15; dogfooded (the exiled `career-plan.roadmap.txt`
  diagram is back inside its note, fenced).
- **#8a** auto-link refresh across all 29 notes → 16 new blocks, 7 revised, **zero** re-embeds.
- **#40** managed `CLAUDE.md` **and `README.md`** + `--adopt` → CI gate 16.

**Next candidates:**
- **Re-examine whether #8b is still blocked.** It is parked behind the "#12/#13/#15 diverse
  corpus", but #13 is done and **#15 is BUILT** — and its acceptance run already produced the
  signal #8b wants (`separation +0.136`, a confident `t_max ≈ 0.30`). #8a also handed it a real
  reproduction: an edge that *dissolved* as the corpus grew, which is what hysteresis damps.
- **The #40 follow-on:** `vault/templates/new-note.md` still lives under the preserved `vault/`
  while duplicating the note gate CI enforces — reported today, not yet fixed.
- Human-gated, unchanged: `add_pdf_guided` CLI form pass; Suite A Desktop; glossary Obsidian
  hand-test.

```
 shipped ▶ #39 embed-excluded block ─▶ #8a auto-link refresh ─▶ #40 managed CLAUDE.md
   each dogfooded on ~/second-brain, which is now at devkit HEAD and doctor-green
 next ▶ is #8b actually still gated? (#15 corpus is built and already yields t_max ~= 0.30)
```
