# Daily plan — 2026-07-28

**What this repo is (for a newcomer):** `second-brain-devkit` is a *generator*. It builds a personal
"second brain" — a plain-Markdown notes vault a human edits in Obsidian, plus a local SQLite
semantic-search index an AI reads — and ships it as a ready-to-run repo. Every change goes
prototype → vendor → one command, `python3 tools/ci.py` (15 automated gates).

**Last implemented:** #8a — auto-linking is on across the whole vault of `~/second-brain` (16 new
`related_auto:` blocks, 7 revised, re-run clean, **zero** re-embeds). Earlier today #39 shipped the
*embed-excluded block* and was dogfooded on the same brain: the exiled `career-plan.roadmap.txt`
diagram is back inside its note, fenced.

**Focus / plan:**
- **Done:** #39 (embed-excluded block, CI gate 15) · brain upgraded to devkit `9d2f255` ·
  #40 filed (an upgraded brain never receives a documentation update) · #8a (auto-link refresh).
- **Next candidate:** #40 — it now has a concrete reproduction from the #39 upgrade, and the
  task-#9 README managed-block pattern is the proposed fix.
- Parked: #8b (calibration deriver + hysteresis) behind the #12/#13/#15 corpus — now with real
  evidence, an edge that dissolved as the corpus grew. Human-gated: `add_pdf_guided` CLI form
  pass; Suite A Desktop; glossary Obsidian hand-test.

```
 shipped ▶ #39 embed-excluded block ──▶ dogfooded on ~/second-brain (roadmap restored)
 shipped ▶ #8a auto-link refresh ──▶ 29 notes, mutual-KNN alone chose every link
             t_max never fired · clusters stayed disjoint · 23 edits moved 0 vectors
 filed   ▶ #40 upgraded brains get the code but never the prose that says it exists
```
