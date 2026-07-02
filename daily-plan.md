# Daily plan — 2026-07-02

**Focus:** G1's last piece — make the generator actually *emit* a brain. The
`template/` tree is built and guard-clean; now write `generate()` and prove it by
regenerating into `sandbox/scratch/` (Mode A), then start the manifest-aware diff
against the golden (G2 structural tier).

- Write `generate(target, params)`: copy `template/` → target, then the post-steps
  (seed `vault/` from `seeds/` via `seed_vault.py`; embed the `test` fixtures).
- Wire the **Mode-A runner**: wipe-and-regenerate `sandbox/scratch/` every run
  (never stale); run `check_no_forbidden_refs.py` over the output.
- Start the **G2 structural diff**: compare only the emitted set (manifest-driven),
  `cleaned` files vs their `template/` variants — a clean diff is acceptance.
- Keep the guards green (forbidden-ref + manifest partition); the brain's
  `self_test.py` should pass *inside* the freshly generated scaffold.

```
 template/ ─generate()─▶ sandbox/scratch/ ─manifest-diff─▶ golden   (Mode A)
  (28 files)              wipe + regen            clean = G2 pass

 G1: [x]strategy [x]manifest [x]golden-rework [x]templatize · [ ]generate ← today
```
