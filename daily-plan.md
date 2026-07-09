# Daily plan — 2026-07-09

**Focus:** 07-08 shipped the whole managed-block thread — **#10 splice helper** and **#8
auto-linking end-to-end**: canonical-body embedding, nomic task-prefixes (#3), the read-only
KNN calibration tool, the `related_auto:` **write path** (mutual-KNN + top-N + `t_max`, dry-run
verified), the **Obsidian-format CI gate** (§5), and the **skip-unchanged `content_hash` gate**
— all green through `ci.py` (7/7). #8 is feature-complete except corpus-dependent tuning.
Today: **close the thread with #9**, then start the corpus that unblocks everything downstream.

- **▶▶ Build task #9 — the README managed block (do first).** A devkit-owned region in the
  brain `README.md` (`<!-- BEGIN/END generated -->`) spliced via the **#10 helper**, so
  `update_brain` refreshes it without clobbering the user's own preamble/appendix. Prototype
  in the golden README → vendor → template → `ci.py`. Closes the #10→#8→#9 thread.
- **Then start task #15 — the topically-diverse test corpus.** Seed a brain with many
  distinct-topic notes so the embedding space has real cluster structure. This is the rock
  that unblocks the deferred auto-link `--apply`, real `t_max`/topic-count calibration
  (§2.2/§2.3), and the #12/#13 ablation benchmark.
- Guards stay green through `tools/ci.py` (**7 gates** now).

```
 wed 07-08 ✅ #10 splice helper · #8 auto-linking (calibrate→write→Obsidian gate→content_hash)
             CI 7/7 · auto-link --apply deferred to #15
                              │
                              ▼
 thu 07-09  ▶▶ build #9 README managed block (via #10 helper) → start #15 diverse corpus
            #15 unblocks: auto-link --apply · t_max calibration · #12/#13 benchmark
 loop:  golden ─vendor→ tests/golden ─build→ template ─ci.py(7)→ green
```
