# experiments/ — dated experiment records

A lab notebook. One dated Markdown file per **major feature or investigation**, capturing what was
done and what was found at a point in time. This is the human-first, immutable record that sits
between the two other tiers:

- **git history / commit messages** — the fine-grained telemetry (per-task).
- **`docs/`** — the *evergreen* reference (kept current as the design evolves).
- **`experiments/`** — a *point-in-time snapshot* of an experiment: purpose, method, results, decision.

## The pattern (for a major feature)

1. **This repo — a dated experiment file.** `experiments/YYYY-MM-DD-<slug>.md`, written as a
   **snapshot that links into the living docs** (don't restate evergreen detail — link to it, so the
   two can't drift). It must carry:
   - a **Summary** at the top (purpose + headline result in a few sentences);
   - the **experiment** below in sufficient detail (increments / method / results table);
   - **backlinks** to the feature spec (its `PLAN.md` section) and to the **commits** that built it.
2. **Personal second-brain — one abstracted lesson note.** In the brain's `resources/`, capture the
   *transferable* lesson (the principle that helps a **different** project six months later), **not**
   the project detail. Lesson + a one-line headline number + links back here. Tag it with the repo
   name (`create_second_brain`) so a repo's lessons cluster — but **file by topic, tag by repo**.
   Extract, don't copy: the brain holds *what was learned*; this repo holds *the proof*.

Rule of thumb for what goes where: if it answers *"will this help me in a different repo?"* it's a
lesson (→ brain). If it's a recall@k number, a commit SHA, or a corpus specific — it's evidence
(→ this repo).

## Index

- [2026-07-12 — Hybrid lexical + vector search (FTS5 + RRF)](2026-07-12-hybrid-search-fts5-rrf.md) —
  task #3; hybrid is *situational* (helps adjacent corpora, hurts far-apart ones) → ship as a toggle.
