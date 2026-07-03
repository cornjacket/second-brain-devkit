# Daily plan — 2026-07-03

**Focus:** Make the brain *trustworthy to rely on*. Headline is G5 `doctor.py` — a
health + **consistency** check, directly motivated by today's cache drift (a note
present on disk but missing from the db). Then tighten the AI interface. Same loop:
prototype in the golden → vendor → template → `tools/ci.py` green.

- **`doctor.py` (emitted):** one "is my brain ready & consistent?" command — deps
  (sqlite-vec/apsw), Ollama reachable + `nomic-embed-text` pulled, and **vault
  notes ↔ sidecars ↔ db rows in sync**, with `--repair` (re-embed / `update_cache`
  / `hydrate`). Closes the drift gap seen today.
- **Skill reflexive trigger:** add the user-level `~/.claude/CLAUDE.md` nudge so the
  AI consults the brain *before designing* — the mechanism ships, make it fire.
- **Stretch — scope the MCP server:** the web/desktop-chat path a skill can't serve
  (stdio server + registration); design only, build later.
- Keep the guards green (manifest partition + structural diff); every change lands
  through `tools/ci.py`.

```
 today ✅  skill (any project) · auto-hydrate on commit · incremental cache
                                   │  (drift observed → motivates doctor.py)
                                   ▼
 fri 07-03   doctor.py  ──▶  reflexive skill trigger  ──▶  MCP scoping (stretch)
  (health + vault↔sidecar↔db consistency + --repair)

 loop:  golden ─vendor→ tests/golden ─build→ template ─ci.py→ green
```
