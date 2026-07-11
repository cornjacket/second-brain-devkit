# Daily plan — 2026-07-13

**Focus:** Fri 07-10 landed **#15** — the 200-note topically-diverse benchmark corpus + a
30-query labeled eval set + corpus-driven tooling, with acceptance **passed on real Ollama**
(purity@1 98%, separation +0.136, a confident `t_max ≈ 0.30`, retrieval top-5 30/30). With the
dataset **and** the method now in hand, Monday opens the benchmarking thread and the top
IT-separation lever.

- **▶▶ Start #13 — catalog the quality-enhancement features** (docs-only; the input to #12 and
  the tutorial outline): each retrieval/graph feature with its mechanism, index- vs query-time,
  config toggle, and status.
- **Then #12 — the ablation harness** scaffold: run `queries.jsonl` against the #15 corpus under
  each toggle, reporting recall@k / MRR / separation. Also the vehicle to **compare embedders**.
- **Parallel lever — #3 hybrid FTS5/BM25:** highest-ROI for the IT-heavy real brain (exact tokens
  dense vectors blur). See `docs/embedding-separation.md §1`.
- **Optional:** run the now-unblocked auto-link `--apply` calibration on the real brain (derive
  its own `t_max` — IT-heavy, so expect a looser cut than the diverse corpus).
- Guards stay green via `tools/ci.py` (8 gates).

```
 fri 07-10 ✅ #15 corpus + eval set + tooling · acceptance PASS (98% purity, t_max≈0.30)
                              │
                              ▼
 mon 07-13  ▶▶ #13 feature catalog ──► #12 ablation harness  (consumes #15 corpus + queries)
            ‖ parallel: #3 hybrid FTS5/BM25 (IT-separation lever)
            → optional: real-brain auto-link --apply calibration
 guards: tools/ci.py (8) green
```
