#!/usr/bin/env python3
"""The generator core — ``generate(target, params)`` writes a brain scaffold.

SPEC §5.1: a **pure function both generation modes call**. It does two things:

  1. copy the tracked ``template/`` tree into ``target`` byte-for-byte (symlinks
     preserved, modes preserved), then
  2. run the seed-vault post-step — the *emitted* ``scripts/seed_vault.py`` copies
     ``seeds/** -> vault/**`` inside the target, exactly as a user would.

The result is the emitted + generated file set defined by ``emit-manifest.toml``
(the 28 template files + the 5 ``vault/**`` files). Nothing is cleaned or embedded
here: cleaning is a once-off build step (``tools/build_template.py``), and the
committed ``test``-backend fixtures ship *pre-embedded* in the template while
live-vault sidecars are git-ignored and never emitted (OQ-3). So the post-step is
just the seed.

Only the target and the surrounding steps differ between modes:

  • Mode A (validation) — ``tools/run_sandbox.py`` wipes ``sandbox/scratch/``,
    calls this, then diffs vs the golden and discards.
  • Mode B (production, G3) — calls this into a user-chosen path, then ``git init``
    + first commit and keeps it.

This core is identical for both, which is what lets Mode A vouch for Mode B.

    python3 tools/generate.py <target>

This is a devkit tool; it is never emitted into a brain.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = REPO_ROOT / "template"


def _copy_template(target: Path) -> None:
    """Copy the whole template tree into ``target`` (symlinks + modes preserved)."""
    if not TEMPLATE.is_dir():
        raise SystemExit(
            f"generate: no template tree at {TEMPLATE} — run tools/build_template.py first"
        )
    shutil.copytree(TEMPLATE, target, symlinks=True, dirs_exist_ok=True)


def _seed_vault(target: Path) -> None:
    """Run the emitted seed_vault.py in the target: seeds/** -> vault/**."""
    script = target / "scripts" / "seed_vault.py"
    if not script.is_file():
        raise SystemExit(f"generate: template is missing {script.relative_to(target)}")
    # -B: don't litter the freshly-generated scaffold with __pycache__ bytecode.
    result = subprocess.run(
        [sys.executable, "-B", str(script)],
        cwd=target, capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit("generate: seed_vault post-step failed")


def generate(target, params: dict | None = None, *, force: bool = False) -> Path:
    """Write a brain scaffold into ``target`` and return the resolved path.

    Refuses a non-empty target unless ``force`` (protects real data — the Mode-B
    concern in PLAN G3; Mode A always hands a freshly-wiped dir). ``params`` is
    accepted for interface stability but unused: the product has no per-brain
    variable yet (SPEC §5.2), so generation is a pure copy + seed.
    """
    target = Path(target).resolve()
    if target.exists() and any(target.iterdir()) and not force:
        raise SystemExit(
            f"generate: target {target} is not empty — refusing to overwrite "
            f"(pass force=True)"
        )
    target.mkdir(parents=True, exist_ok=True)
    _copy_template(target)
    _seed_vault(target)
    return target


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        raise SystemExit("usage: generate.py <target>")
    out = generate(argv[0])
    print(f"generated brain -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
