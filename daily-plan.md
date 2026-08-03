# Daily plan — 2026-08-04

**What this repo is (for a newcomer):** `second-brain-devkit` is a *generator*. It builds a personal
"second brain" — a plain-Markdown notes vault a human edits in Obsidian, plus a local SQLite
semantic-search index an AI reads — and ships it as a ready-to-run repo. Every change goes
prototype → vendor → one command, `python3 tools/ci.py` (16 automated gates).

**Where things stand:** the backlog is clear of code debt. #39 (embed-excluded block), #8a
(auto-linking on), and #40 (managed `CLAUDE.md`/`README.md`, plus the note-template carve-out)
all shipped and were dogfooded on `~/second-brain`, which is current and doctor-green. **#8b was
closed rather than built** — running the corpus it had been parked behind refuted its premise
(`t_max` never binds; nothing to derive). Nothing is broken; CI is 16/16.

**Focus / plan — what is left is human-gated, not code-gated:**
- **Suite A Desktop e2e** (#33/#35) — paste the 5 canned prompts in Claude Desktop, run the
  verifiers. Ships in every brain at `<brain>/desktop-e2e/`; never yet run by a human.
- **Pure-client cross-session test** (#36) — seed canaries in one Desktop chat, delete it,
  retrieve in a fresh one. Proves retrieval rather than conversation memory.
- **Glossary Obsidian hand-tests** — install the Spaced Repetition plugin and confirm a term
  renders as a card; add the graph colour group and **settle whether `path:glossary/` or
  `tag:#glossary` is the query that actually works** — the docs contradict each other, which is
  proof nobody has run it.
- **`add_pdf_guided` CLI form pass** — elicitation is confirmed on Claude Code CLI 2.1.215, but
  the form-by-form walkthrough has never been reviewed by a human.

**If a code session happens instead**, the honest list is *strategic*, not urgent — nothing below
blocks anything:
- **OQ-7** — can the brain be reached from a phone / the Claude mobile app?
- **Mothball `second-brain-test`** (G4) once generation + harness are trusted; promote the
  product spec into the devkit (OQ-4).
- **Task #14** — the "how to build your own second brain" post.

```
 code debt ▶ none. #39 · #8a · #40 shipped; #8b closed on evidence; CI 16/16
 blocked   ▶ everything left needs a human at an Obsidian / Claude Desktop window
 decide    ▶ mothball the golden? phone access (OQ-7)? write the post (#14)?
```
