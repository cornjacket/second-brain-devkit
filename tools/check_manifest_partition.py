#!/usr/bin/env python3
"""Manifest partition check (devkit tool, SPEC.md §5.2).

Verify that emit-manifest.toml PARTITIONS the golden's files: every file in the
vendored golden (`tests/golden/`) appears in exactly one of the manifest's
`verbatim` / `cleaned` / `generated` / `exclude` path sets — none missing, none
duplicated, none referring to a file the golden no longer contains.

This makes "what a brain contains" auditable and keeps the manifest honest as the
golden evolves: add or remove a golden file and this check fails until the
manifest is updated to match.

The golden is the in-repo `tests/golden/` snapshot (OQ-1 Option A), enumerated by
a filesystem walk — no external repo, no `git ls-files`, so this runs
self-contained in CI (and before the snapshot is even committed, during a
`vendor_golden` sync).

Usage:
    python3 tools/check_manifest_partition.py [--golden DIR] [--manifest FILE]

Exit codes:
    0  the manifest exactly partitions the golden's files
    1  mismatch (missing, extra, or duplicated paths) — details printed
    2  usage / IO error
"""
from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

BUCKETS = ("verbatim", "cleaned", "generated", "exclude")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GOLDEN = REPO_ROOT / "tests" / "golden"
DEFAULT_MANIFEST = REPO_ROOT / "emit-manifest.toml"


def golden_tracked(golden: Path) -> set[str]:
    """Files + symlinks under the vendored golden, as golden-relative POSIX paths."""
    return {
        p.relative_to(golden).as_posix()
        for p in golden.rglob("*")
        if p.is_symlink() or p.is_file()
    }


def manifest_paths(manifest: Path) -> tuple[dict[str, list[str]], list[str]]:
    """Return (bucket -> paths) and the flat list of every declared path (with dups)."""
    with manifest.open("rb") as fh:
        data = tomllib.load(fh)
    per_bucket: dict[str, list[str]] = {}
    flat: list[str] = []
    for bucket in BUCKETS:
        paths = data.get(bucket, {}).get("paths", [])
        per_bucket[bucket] = paths
        flat += paths
    return per_bucket, flat


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args(argv)

    if not args.golden.is_dir():
        print(f"error: no vendored golden at {args.golden} "
              f"(run tools/vendor_golden.py)", file=sys.stderr)
        return 2
    if not args.manifest.is_file():
        print(f"error: no manifest at {args.manifest}", file=sys.stderr)
        return 2

    tracked = golden_tracked(args.golden)

    per_bucket, flat = manifest_paths(args.manifest)
    declared = set(flat)

    # Duplicates: a path in two buckets (or twice in one) breaks the partition.
    dups = sorted({p for p in flat if flat.count(p) > 1})
    missing = sorted(tracked - declared)   # tracked in golden, absent from manifest
    extra = sorted(declared - tracked)     # in manifest, not tracked by golden

    if not (dups or missing or extra):
        counts = ", ".join(f"{b}={len(per_bucket[b])}" for b in BUCKETS)
        print(f"OK: manifest partitions {len(tracked)} golden files ({counts})")
        return 0

    if dups:
        print(f"DUPLICATED across/within buckets ({len(dups)}):", file=sys.stderr)
        for p in dups:
            print(f"  {p}", file=sys.stderr)
    if missing:
        print(f"MISSING from manifest — golden tracks but manifest omits ({len(missing)}):",
              file=sys.stderr)
        for p in missing:
            print(f"  {p}", file=sys.stderr)
    if extra:
        print(f"EXTRA in manifest — not tracked by golden ({len(extra)}):", file=sys.stderr)
        for p in extra:
            print(f"  {p}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
