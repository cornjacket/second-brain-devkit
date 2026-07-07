# Daily plan — 2026-07-07

**Focus:** A hardening + design stretch landed (07-05→07): MCP **CI coverage** (compile
gate + opt-in behavioral test), **`update_brain.py`** (G4 non-destructive upgrade), and a
wave of design docs (source-map, Claude-Desktop workflow, retrieval-quality, big-brain,
remote-backed-brains). Next is the queued **task #6 — remote-backed brains**: give a new
brain an *opt-in* git remote at creation. Same loop: prototype emitted bits in the golden
→ vendor → template → `tools/ci.py` green.

- **▶▶ Build task #6 — `new_brain.py --remote <URL>`.** After init/first-commit/hooks:
  `git remote add origin` + `git push -u origin HEAD`. **Preflight (detect + instruct, no
  credential installer):** git identity, `git ls-remote` auth+reachable, remote empty —
  fail early, leave the local brain intact. **State:** `secondbrain.autosync` git config
  **ON by default** (`--no-autosync` overrides); sync scripts gate on *remote-exists AND
  autosync-not-false*. **CI test with no creds:** `tools/check_remote_sync.py` against a
  local **bare repo** (`file://`) — connect → push → clone-as-peer → pull. README prereqs.
- **Then:** #3 hybrid FTS5 search (emits into brains → prototype in golden first) and #5
  `add_note` write tool (design-first).
- Guards stay green; everything lands through `tools/ci.py` (now 5 gates incl. compile).

```
 07-05→07 ✅  CI coverage (#1 compile · #2 behavioral) · update_brain.py (G4)
              docs: source-map · desktop-workflow · retrieval · big-brain · remote-backed
                                   │
                                   ▼
 tue 07-07  ▶▶ task #6 remote-backed brains (new_brain --remote + preflight + autosync state)
            then ▸ #3 hybrid FTS5 · #5 add_note

 loop:  golden ─vendor→ tests/golden ─build→ template ─ci.py→ green
```
