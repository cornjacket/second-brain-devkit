# Daily plan — 2026-07-12

**Focus:** Sat landed **#3 increment 1** — hybrid FTS5 + RRF fusion in the one shared
`search_vault.search()` (CI 8/8, semantic tier 5/5 incl. an exact-token case). Today wires the
**config surface** and **measures the payoff**, finishing the #3 arc.

- **▶▶ #3 increment 2 — `config/features.toml` toggle** (`hybrid_search`, `rrf_k`) + `scripts/features.py`,
  env > config > default like `embedder.py`. Emitted → manifest/vendor/template/CI. This is the
  **deferred #12 Half-B config surface**, now justified by a genuinely *situational* query-time toggle.
- **#3 increment 3 — ablate hybrid vs vector-only** on the **hardened IT query set** (`tools/ablation.py` §4),
  where exact-token queries are dense search's blind spot — the payoff measurement.
- **Loop:** prototype in `../second-brain-test/` → `vendor_golden.py` → `build_template.py` → `tools/ci.py` (8 gates).
- **Stretch / parallel:** start **#19 glossary namespace** (unblocks #20/#21 glossary-over-MCP), or run
  the calibrated **#8 auto-link `--apply`** on the real brain (`t_max ≈ 0.30`).

```
 sat 07-11 ✅ #3 inc1  hybrid FTS5 + RRF  (CI 8/8 · semantic 5/5)
                 │
                 ▼
 sun 07-12  ▶▶ #3 inc2 features.toml toggle ──► #3 inc3 ablate hybrid vs vector-only (IT set)
            ‖ stretch: #19 glossary namespace  ·  #8 auto-link --apply (real brain)
 guards: tools/ci.py (8) green · prototype-first in second-brain-test/
```
