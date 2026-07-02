#!/usr/bin/env python3
"""The full devkit acceptance gate — one entry point for local **and** CI.

``.github/workflows/ci.yml`` runs exactly this, so a green ``python3 tools/ci.py``
locally predicts a green CI run (local ≡ CI). Everything here is self-contained:
it uses only the in-repo vendored golden (``tests/golden/``, OQ-1 Option A) and the
deterministic ``test`` embedder, so it needs no external golden, no network, and
no third-party packages — just Python 3.11+.

Gate (fail-fast on any red):
  1. **Manifest partition** — emit-manifest.toml partitions the vendored golden.
  2. **Template in sync** — rebuild ``template/`` from the golden and assert the
     committed tree is byte-identical (catches a stale template after a golden
     change). Mutates ``template/`` in place; a clean rebuild leaves it unchanged.
  3. **Mode-A harness** — wipe-regenerate ``sandbox/scratch/`` + guard + in-scaffold
     self-test + structural diff vs the golden (``tools/run_sandbox.py``).
  4. **Mode-B smoke** — ``new_brain.py`` into a throwaway temp path, then the same
     structural-diff oracle on it (proves production output ≡ the validated Mode-A
     output).

    python3 tools/ci.py

This is a devkit tool; it is never emitted into a brain.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS = REPO_ROOT / "tools"
PY = sys.executable

# A self-contained git identity so new_brain's first commit works even in a bare
# CI runner with no global git config. Only set if the environment lacks one.
GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "devkit-ci",
    "GIT_AUTHOR_EMAIL": "ci@second-brain-devkit.local",
    "GIT_COMMITTER_NAME": "devkit-ci",
    "GIT_COMMITTER_EMAIL": "ci@second-brain-devkit.local",
}


def _run(cmd: list[str], *, cwd: Path | None = None, env: dict | None = None) -> bool:
    result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode == 0


def step_partition() -> bool:
    return _run([PY, str(TOOLS / "check_manifest_partition.py")])


def step_template_in_sync() -> bool:
    # Build a throwaway copy from the golden and compare it to the on-disk
    # template/ — git-state-independent (works whether or not template/ is
    # committed), so this catches a stale template without false-flagging
    # legitimate uncommitted rebuilds.
    tmp = Path(tempfile.mkdtemp(prefix="template-check-"))
    fresh = tmp / "template"
    try:
        if not _run([PY, str(TOOLS / "build_template.py"), str(fresh)]):
            return False
        # -r recursive, --no-dereference compares symlinks by target not content.
        if _run(["diff", "-r", "--no-dereference", str(fresh), str(REPO_ROOT / "template")]):
            print("template/ is in sync with the vendored golden")
            return True
        print("FAIL: template/ differs from a fresh rebuild — run "
              "tools/build_template.py and commit the result", file=sys.stderr)
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def step_mode_a() -> bool:
    return _run([PY, str(TOOLS / "run_sandbox.py")])


def step_mode_b_smoke() -> bool:
    env = {**os.environ, **{k: v for k, v in GIT_IDENTITY.items() if k not in os.environ}}
    parent = Path(tempfile.mkdtemp(prefix="brain-smoke-"))
    target = parent / "brain"
    try:
        if not _run([PY, str(TOOLS / "new_brain.py"), str(target)], env=env):
            return False
        return _run([PY, str(TOOLS / "check_structural_diff.py"), str(target)])
    finally:
        shutil.rmtree(parent, ignore_errors=True)


STEPS = [
    ("1/4 manifest partition", step_partition),
    ("2/4 template in sync with golden", step_template_in_sync),
    ("3/4 Mode-A harness (generate + guard + self-test + diff)", step_mode_a),
    ("4/4 Mode-B smoke (new_brain ≡ Mode-A)", step_mode_b_smoke),
]


def main() -> int:
    results: list[tuple[str, bool]] = []
    for name, fn in STEPS:
        print(f"\n=== {name} ===")
        ok = fn()
        results.append((name, ok))
        if not ok:
            print(f"\n✗ CI FAILED at step: {name}")
            # Fail fast: later steps assume earlier ones held.
            for n, r in results:
                print(f"  {'✓' if r else '✗'} {n}")
            return 1

    print("\n✓ CI PASSED — all gates green")
    for n, _ in results:
        print(f"  ✓ {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
