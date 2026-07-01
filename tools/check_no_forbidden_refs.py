#!/usr/bin/env python3
"""Forbidden-reference guard (devkit tool, SPEC.md §5.3).

Scan a generated brain tree for a denylist of tokens that must never leak into
it — seeded with ``ai-project-status`` (the devkit's own dev-process tooling, a
hard non-goal per SPEC.md §7). Prints ``path:line`` for every hit and exits
non-zero if any are found, so the Mode-A validation harness can gate on it
deterministically rather than trusting a manual cleanup.

This tool is part of the devkit and is NEVER emitted into a generated brain.

Usage:
    python3 tools/check_no_forbidden_refs.py <target-dir> [--deny TOKEN ...]

Exit codes:
    0  clean — no forbidden token found
    1  one or more forbidden references found
    2  usage / bad target
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Tokens that must never appear in a generated brain. Extend as new
# devkit-internal dependencies appear; keep each lowercase (matching is
# case-insensitive).
DEFAULT_DENYLIST = ("ai-project-status",)

# Directories that are never part of a brain's tracked source and would only
# produce noise (VCS internals, caches, virtualenvs, the derived cache/build).
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", "data"}


def iter_text_files(root: Path):
    """Yield files under ``root``, skipping VCS/cache dirs and binary blobs."""
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def scan(root: Path, denylist) -> list[tuple[Path, int, str, str]]:
    """Return (path, lineno, token, line) for every denylisted hit."""
    needles = [t.lower() for t in denylist]
    hits: list[tuple[Path, int, str, str]] = []
    for path in iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary or unreadable — not a source file we vet
        for lineno, line in enumerate(text.splitlines(), start=1):
            low = line.lower()
            for needle in needles:
                if needle in low:
                    hits.append((path, lineno, needle, line.strip()))
    return hits


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="directory to scan (a generated brain)")
    parser.add_argument(
        "--deny",
        action="append",
        metavar="TOKEN",
        help="add a forbidden token (repeatable); defaults apply if omitted",
    )
    args = parser.parse_args(argv)

    root = Path(args.target)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    denylist = tuple(args.deny) if args.deny else DEFAULT_DENYLIST
    hits = scan(root, denylist)

    if hits:
        print(f"FORBIDDEN references found in {root} ({len(hits)}):", file=sys.stderr)
        for path, lineno, token, line in hits:
            rel = path.relative_to(root)
            print(f"  {rel}:{lineno}: [{token}] {line}", file=sys.stderr)
        return 1

    print(f"OK: no forbidden references in {root} (denylist: {', '.join(denylist)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
