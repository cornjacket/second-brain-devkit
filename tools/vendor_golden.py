#!/usr/bin/env python3
"""Vendor the live golden's tracked files into the devkit as ``tests/golden/``.

OQ-1 (Option A): the devkit must be **self-sustaining** — the regression baseline
lives *inside* this repo so CI checks out only the devkit and never reaches the
external golden. This tool snapshots the live golden (``../second-brain-test``)
into a devkit-tracked ``tests/golden/`` tree that the harness diffs against.

It copies **only the golden's git-tracked files** (``git ls-files``) — so no
``.git``, no git-ignored live-vault sidecars, no ``__pycache__``. Symlinks
(``GEMINI.md`` → ``CLAUDE.md``) and executable bits are preserved. The dest is
wiped and rebuilt each run, so a deleted golden file disappears from the snapshot.

**This is a dev-machine step, run by hand when the live golden changes — CI never
runs it.** The committed ``tests/golden/`` snapshot is what CI diffs against. As a
guard against a bad sync, this runs the manifest-partition check over the fresh
snapshot and fails loudly if the golden no longer partitions the manifest (i.e.
the golden gained/lost a file the manifest doesn't account for).

    python3 tools/vendor_golden.py

This is a devkit tool; it is never emitted into a brain.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LIVE_GOLDEN = REPO_ROOT.parent / "second-brain-test"
VENDORED = REPO_ROOT / "tests" / "golden"
PARTITION = REPO_ROOT / "tools" / "check_manifest_partition.py"


def tracked_files(golden: Path) -> list[str]:
    """Golden-relative POSIX paths of every git-tracked file in the live golden."""
    out = subprocess.run(
        ["git", "-C", str(golden), "ls-files"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def vendor(src_root: Path, dst_root: Path, rels: list[str]) -> int:
    if dst_root.exists():
        shutil.rmtree(dst_root)
    dst_root.mkdir(parents=True)
    for rel in rels:
        src, dst = src_root / rel, dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_symlink():
            os.symlink(os.readlink(src), dst)          # preserve the link, don't follow
        elif src.is_file():
            shutil.copy2(src, dst)                      # bytes + mode (exec bits)
        else:
            raise SystemExit(f"vendor_golden: tracked path is neither file nor symlink: {rel}")
    return len(rels)


def main() -> int:
    if not (LIVE_GOLDEN / ".git").exists():
        raise SystemExit(
            f"vendor_golden: no live golden repo at {LIVE_GOLDEN} — this sync runs "
            f"on a dev machine that has the golden checked out (CI never runs it)."
        )
    rels = tracked_files(LIVE_GOLDEN)
    n = vendor(LIVE_GOLDEN, VENDORED, rels)
    print(f"vendored {n} tracked file(s) from {LIVE_GOLDEN} -> {VENDORED.relative_to(REPO_ROOT)}/")

    # Guard: the fresh snapshot must still partition the manifest exactly.
    print("verifying the snapshot partitions the manifest …")
    result = subprocess.run(
        [sys.executable, str(PARTITION), "--golden", str(VENDORED)],
        capture_output=True, text=True,
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if result.returncode != 0:
        raise SystemExit(
            "vendor_golden: the vendored snapshot does not partition the manifest — "
            "the golden changed; update emit-manifest.toml before committing tests/golden/."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
