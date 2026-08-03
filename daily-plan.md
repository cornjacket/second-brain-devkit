# Daily plan — 2026-08-03

**What this repo is (for a newcomer):** `second-brain-devkit` is a *generator*. It builds a personal
"second brain" — a plain-Markdown notes vault a human edits in Obsidian, plus a local SQLite
semantic-search index an AI reads — and ships it as a ready-to-run repo. Every change goes
prototype → vendor → one command, `python3 tools/ci.py` (16 automated gates).

**Last implemented:** the #8b gate was tested rather than assumed — and the premise **failed**.
Running the #15 diverse corpus (200 notes, 10 domains, real Ollama) shows `t_max` never binds at
any scale: the largest neighbour distance is 0.3848, under the 0.45 default, and tightening it
destroys 60% of the links without improving precision. There is nothing for the calibration
deriver to derive, so that half of #8b is **closed, not unblocked**.

**Shipped 2026-07-28:**
- **#39** embed-excluded block → CI gate 15; dogfooded (the exiled `career-plan.roadmap.txt`
  diagram is back inside its note, fenced).
- **#8a** auto-link refresh across all 29 notes → 16 new blocks, 7 revised, **zero** re-embeds.
- **#40** managed `CLAUDE.md` **and `README.md`** + `--adopt` → CI gate 16.

**Next candidates:**
- **Rescope #8b's surviving half.** Hysteresis was aimed at a distance band; #8a's dissolving
  edge was a **top-N membership** change, so the band damps nothing. Membership hysteresis on
  top-N is the real design — and §2.1b shows `top-N` is also the parameter that actually moves
  the graph (3→12: links 348→1802, isolated 25→0).
- ~~The #40 follow-on~~ — **closed 2026-08-03.** `vault/templates/new-note.md` is now the one
  named exception to the preserved `vault/` and refreshes on every upgrade; gate 16 asserts it
  is the *only* file written in there.
- Human-gated, unchanged: `add_pdf_guided` CLI form pass; Suite A Desktop; glossary Obsidian
  hand-test.

```
 shipped ▶ #39 embed-excluded block · #8a auto-link refresh · #40 managed CLAUDE.md + README
 tested  ▶ #8b gate — the corpus was already built; running it REFUTED the premise
             t_max never binds (max 0.3848 < 0.45 default); top-N is the real lever
 next    ▶ rescope #8b as membership hysteresis on top-N, or close it outright
```
