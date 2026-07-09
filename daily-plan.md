# Daily plan — 2026-07-09

**Focus:** 07-08 shipped the managed-block thread (**#10** splice helper + **#8** auto-linking
end-to-end). Today is test-corpus day: **#16** landed the seed/teardown utility (100 notes,
install/remove + `--seed-test-corpus`) and **#17** raised its clustering — rewrote all 100 note
bodies ~3× longer and topic-anchored (purity@1 69%→79%, @5 55%→75%; 84% under the `clustering:`
prefix), with the `clustering:`-prefix reasoning captured in the retrieval docs. Both committed,
CI 7/7. Remaining: **close the managed-block thread with #9**, then the light #18 checkpoint and
start the diverse corpus #15.

- **▶▶ Build task #9 — the README managed block (do first).** A devkit-owned region in the brain
  `README.md` (`<!-- BEGIN/END generated -->`) spliced via the **#10 helper**, so `update_brain`
  refreshes it without clobbering the user's own preamble/appendix. Prototype in the golden README
  → vendor → template → `ci.py`. Closes the #10→#8→#9 thread.
- **Then #18 — review the corpus separation (light checkpoint).** #17 already lifted purity; decide
  whether it's enough for the #12/#13 benchmark or whether to lean on the ground-truth topic labels
  (the reframe). A decision, not new code.
- **Then start task #15 — the topically-diverse benchmark corpus.** Can reuse the #16/#17 corpus;
  unblocks the deferred auto-link `--apply`, real `t_max`/topic-count calibration, and #12/#13.
- Guards stay green through `tools/ci.py` (**7 gates**).

```
 wed 07-08 ✅ #10 splice helper · #8 auto-linking
                              │
                              ▼
 thu 07-09 ✅ #16 test-corpus utility · #17 clustering improvement (purity 69→79% / 84%)
            ▶▶ close #9 README managed block (via #10 helper)
            → #18 review corpus separation (checkpoint) → start #15 diverse corpus
 loop:  golden ─vendor→ tests/golden ─build→ template ─ci.py(7)→ green
```
