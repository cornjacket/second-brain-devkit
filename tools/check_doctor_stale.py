#!/usr/bin/env python3
"""Gate 11 — doctor.py detects a STALE embedding (task #30).

The honest completion of #26. Changing the canonical view (`note_view.canonical_body`) changes
what every note *would* embed to — but `update_brain.py` ships the new code and **never
re-embeds** (it deliberately never touches `vault/` or `data/`). So an upgraded brain silently
holds vectors from the *old* view: not broken — search still works — but stale, and that is
exactly the failure that produces no signal. The user's real brain was correct only because the
#26 migration was run *by hand*.

`doctor.py` is the "is my brain ready?" preflight and already walks vault ↔ sidecar ↔ cache. This
asserts the one check it was missing: recompute each note's `content_hash` and compare it to the
hash **stored in the sidecar**. A mismatch means the sidecar's vector was produced from a
different input than the note now has — stale, and repairable.

Two faithful triggers, both deterministic (the `test` backend, no Ollama):

  1. **Substance edited, not re-embedded** — edit a note's prose on disk without committing, so
     the hook never re-embeds. The recomputed hash moves; the sidecar's does not.
  2. **The view moved under it** — a sidecar whose stored `content_hash` no longer matches the
     current view (simulated by corrupting the stored hash — byte-identical to what a canonical
     view change does to every note at once).

Both must be reported as stale, `--repair` must clear them, and — the anti-false-green — a clean
brain must NOT report stale. Without the check, doctor says "healthy & consistent" while holding
vectors from a view that no longer exists, which is the lie this gate exists to kill.

    python3 tools/check_doctor_stale.py

Hermetic; stdlib + git. Devkit tool, never emitted.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import generate  # noqa: E402


def _run(cmd: list[str], cwd: Path, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)


def _doctor(brain: Path, env: dict, repair: bool = False) -> tuple[int, str]:
    cmd = [sys.executable, "scripts/doctor.py"] + (["--repair"] if repair else [])
    p = _run(cmd, brain, env)
    return p.returncode, p.stdout + p.stderr


def main() -> int:
    env = {**os.environ, "SECOND_BRAIN_EMBEDDER": "test"}
    parent = Path(tempfile.mkdtemp(prefix="doctor-stale-"))
    brain = parent / "brain"
    fails: list[str] = []
    try:
        generate(brain)
        note = brain / "vault" / "resources" / "stale-probe.md"
        note.write_text("---\ntags: [t]\n---\n\n# Stale Probe\n\nA probe note about vectors.\n",
                        encoding="utf-8")
        if _run([sys.executable, "scripts/embed_vault.py"], brain, env).returncode != 0:
            raise SystemExit("doctor-stale: embed_vault failed")
        if _run([sys.executable, "scripts/hydrate_cache.py"], brain, env).returncode != 0:
            raise SystemExit("doctor-stale: hydrate_cache failed")

        # 1. clean brain must be green and NOT report stale (the anti-false-green baseline)
        rc, out = _doctor(brain, env)
        if rc != 0 or "healthy & consistent" not in out:
            fails.append(f"clean brain not healthy: {out.strip().splitlines()[-1:]}")
        if "stale embedding" in out:
            fails.append("clean brain wrongly reported a stale embedding")

        # 2a. edit the prose without re-embedding -> doctor must flag it stale
        note.write_text("---\ntags: [t]\n---\n\n# Stale Probe\n\nRewritten prose, never embedded.\n",
                        encoding="utf-8")
        rc, out = _doctor(brain, env)
        if "stale embedding" not in out or "stale-probe.md" not in out:
            fails.append(f"an edited-but-unembedded note was NOT flagged stale: "
                         f"{[l for l in out.splitlines() if 'stale' in l.lower()]}")
        if rc == 0:
            fails.append("doctor exited 0 despite a stale embedding (must be non-zero)")

        # 2b. --repair must re-embed it and go green
        rc, out = _doctor(brain, env, repair=True)
        if rc != 0 or "healthy & consistent" not in out:
            fails.append(f"--repair did not clear the stale embedding: "
                         f"{out.strip().splitlines()[-1:]}")

        # 3. corrupt a sidecar's stored hash (what a canonical-view change does to every note) ->
        #    stale again, proving the check keys on the stored hash, not on an mtime or a guess
        sc = brain / "vault" / "resources" / ".stale-probe.embed.json"
        payload = json.loads(sc.read_text(encoding="utf-8"))
        payload["content_hash"] = "sha256:0000stale"
        sc.write_text(json.dumps(payload), encoding="utf-8")
        rc, out = _doctor(brain, env)
        if "stale embedding" not in out:
            fails.append("a sidecar whose stored content_hash no longer matches the view was NOT "
                         "flagged stale (this is the #26 upgrade case)")
    finally:
        shutil.rmtree(parent, ignore_errors=True)

    if fails:
        for f in fails:
            print(f"  FAIL  {f}")
        print(f"\ndoctor-stale FAILED: {len(fails)} assertion(s)")
        return 1
    print("  ok    clean brain reports no stale embedding")
    print("  ok    an edited-but-unembedded note is flagged stale (and exits non-zero)")
    print("  ok    --repair re-embeds it and the brain goes green")
    print("  ok    a sidecar whose stored hash predates the current view is flagged stale (#26)")
    print("\ndoctor-stale OK: stale embeddings are detected and repairable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
