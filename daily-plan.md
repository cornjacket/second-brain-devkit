# Daily plan — 2026-07-08

**Focus:** Yesterday (07-07) shipped **task #6 remote-backed brains** (`create_second_brain.py
--remote` + fail-early preflight + `secondbrain.autosync` + hermetic CI gate 6/6), renamed
`new_brain.py → create_second_brain.py`, added a brain-install-checklist procedure to
CLAUDE.md, and **recreated `~/second-brain` on a real GitHub remote** (SSH creds path
validated end-to-end). Queued the managed-block thread: **#10 splice helper → #8 auto-linking
→ #9 README block**. Today: build that thread bottom-up.

- **▶▶ Build task #10 — the shared "splice a marked block" helper (do first).** One
  `splice_block(text, begin, end, new_body)` (+ `remove_block`/`has_block`), markers as
  arguments. **Prove it by refactoring the existing `--nudge` install/remove onto it** — no
  behavior change (install→idempotent→uninstall round-trip green). Prototype the emitted
  bits in the golden → vendor → template → `ci.py`.
- **Then start #8 auto-linking** (prototype in the golden): embed **substance, not metadata**
  (canonical body view in `embed_staged.py`), `related_auto:` quoted wikilinks, `content_hash`
  no-op gate.
- **Push the 6 pending devkit commits** to `origin/main` early.
- Guards stay green through `tools/ci.py` (6 gates).

```
 07-07 ✅ #6 remote-backed · rename → create_second_brain.py · ~/second-brain on GitHub
          queued: #10 helper → #8 auto-link → #9 README block
                              │
                              ▼
 wed 07-08  ▶▶ build #10 splice helper (refactor --nudge onto it) → start #8 auto-linking
            push devkit (6 commits)
 loop:  golden ─vendor→ tests/golden ─build→ template ─ci.py→ green
```
