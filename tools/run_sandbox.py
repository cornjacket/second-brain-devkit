#!/usr/bin/env python3
"""Mode-A harness — wipe ``sandbox/scratch/``, regenerate, and gate the output.

SPEC §5: **never test against stale state.** Every run wipes ``sandbox/scratch/``,
regenerates a brain into it via the generator core (``tools/generate.py``), then
runs the acceptance gates:

  1. **Forbidden-reference guard** (``tools/check_no_forbidden_refs.py``) over the
     generated tree — the hard invariant that no emitted file names a
     devkit-internal dependency (SPEC §5.3).
  2. **The brain's own self-test** (``scripts/self_test.py``) *inside* the freshly
     generated scaffold — proves the emitted embed pipeline is wired and
     reproduces the committed ``test``-backend fixtures byte-for-byte (OQ-3).
  3. **Structural diff** (``tools/check_structural_diff.py``) vs the golden — the
     G2 acceptance oracle: the generated tree must be exactly the manifest's
     emitted set, byte-for-byte (verbatim + vault vs the golden, cleaned vs the
     template), with no stray files (SPEC §5.2).

``sandbox/`` is git-ignored — it is regenerated output, never committed.

    python3 tools/run_sandbox.py

This is a devkit tool; it is never emitted into a brain.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import generate  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SANDBOX = REPO_ROOT / "sandbox" / "scratch"
GUARD = REPO_ROOT / "tools" / "check_no_forbidden_refs.py"
DIFF = REPO_ROOT / "tools" / "check_structural_diff.py"


def wipe(path: Path) -> None:
    """Remove the target tree so generation always starts from nothing."""
    if path.exists():
        shutil.rmtree(path)


def _run(cmd: list[str], cwd: Path | None = None) -> bool:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result.returncode == 0


def main() -> int:
    print(f"wipe-and-regenerate {SANDBOX.relative_to(REPO_ROOT)}/ …")
    wipe(SANDBOX)
    generate(SANDBOX)
    print(f"generated brain -> {SANDBOX.relative_to(REPO_ROOT)}/\n")

    print("gate 1/3 — forbidden-reference guard")
    guard_ok = _run([sys.executable, str(GUARD), str(SANDBOX)])

    print("\ngate 2/3 — self-test inside the generated brain")
    # -B: keep the generated scaffold free of __pycache__ bytecode.
    self_test_ok = _run(
        [sys.executable, "-B", str(SANDBOX / "scripts" / "self_test.py")], cwd=SANDBOX
    )

    print("\ngate 3/3 — structural diff vs the golden (G2 acceptance oracle)")
    diff_ok = _run([sys.executable, str(DIFF), str(SANDBOX)])

    print()
    if guard_ok and self_test_ok and diff_ok:
        print("Mode A OK — generated brain passes the guard + self-test + structural diff")
        return 0
    print("Mode A FAILED — "
          f"guard={'ok' if guard_ok else 'FAIL'}, "
          f"self_test={'ok' if self_test_ok else 'FAIL'}, "
          f"diff={'ok' if diff_ok else 'FAIL'}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
