# Daily plan — 2026-07-01

**Focus:** The brain's core pipeline is now proven & committed
(`../second-brain-test` finished M1a→M1b: embed→hydrate→search works, sidecars
committed). The G1 gate is lifting — start generator planning against the now
stable, known-good golden reference.

- Decide the G1 **template strategy**: how to productize the brain's `SPEC.md` /
  `CLAUDE.md` / `scripts/` / hook / PARA roots + `seeds/` into emitted templates.
- Sketch the G2 **validation loop** early: generate → diff vs `../second-brain-test`
  → clean diff = acceptance. This leans on the deterministic `test` embedder
  (semantic/Ollama quality is a *separate*, later check — not needed for the diff).
- Track what's still open in the brain before a full G1: `register.py` (M2) and
  semantic validation (Ollama, blocked) — plan around them, don't block on them.
- Keep generator *code* deferred until the template strategy is chosen (avoid rework).

```
 brain (second-brain-test):  0001–0003 ✅  ·  M1b plumbing ✅   →  G1 gate lifting
                                                                       │
 devkit today ▸ G1 template strategy  ──►  sketch G2 diff-vs-golden harness
                                                                       │
                              (brain M2 register + Ollama semantic still pending)
```
