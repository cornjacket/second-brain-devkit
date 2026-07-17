"""Shared helpers for the Desktop e2e verifiers — brain location + side-effect checks.

The verifiers assert what the fixture brain LOOKS LIKE after a human ran a prompt in Desktop —
a note that exists with the right frontmatter and is committed. They import the brain's own
stdlib modules (note_view, tag_hygiene, glossary_new), so they need no third-party packages and
work against any generated brain.

Devkit tool; never emitted into a brain.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def brain_from_argv(argv: list[str] | None = None) -> Path:
    ap = argparse.ArgumentParser(description="Verify a Desktop e2e scenario against a fixture brain.")
    ap.add_argument("--brain", required=True, type=Path, help="path to the fixture brain")
    args, _ = ap.parse_known_args(argv)
    brain = args.brain.resolve()
    if not (brain / "vault").is_dir() or not (brain / "scripts").is_dir():
        sys.exit(f"not a brain: {brain} (expected vault/ and scripts/)")
    return brain


def load(brain: Path, name: str):
    """Import a module from the brain's scripts/ (stdlib-only modules)."""
    p = str(brain / "scripts")
    if p not in sys.path:
        sys.path.insert(0, p)
    return __import__(name)


def find_note_by_title(brain: Path, para: str, title: str) -> Path | None:
    """The note whose H1 is exactly ``# <title>`` under ``vault/<para>/`` — how add_note names it."""
    base = brain / "vault" / para
    if not base.is_dir():
        return None
    heading = f"# {title}"
    for md in sorted(base.rglob("*.md")):
        for line in md.read_text(encoding="utf-8").splitlines():
            if line.strip() == heading:
                return md
    return None


def is_tracked(brain: Path, path: Path) -> bool:
    """True iff ``path`` is committed (git-tracked) in the brain — proves add_note committed it."""
    rel = path.relative_to(brain).as_posix()
    r = subprocess.run(["git", "-C", str(brain), "ls-files", "--error-unmatch", "--", rel],
                       capture_output=True, text=True)
    return r.returncode == 0


class Checker:
    """Accumulates deterministic PASS/FAIL and prints human-observed MANUAL reminders."""

    def __init__(self, scenario: str):
        self.scenario = scenario
        self.failed = 0
        print(f"scenario {scenario}")

    def check(self, cond: bool, msg: str) -> bool:
        print(f"  {'PASS' if cond else 'FAIL'}  {msg}")
        if not cond:
            self.failed += 1
        return cond

    def manual(self, msg: str) -> None:
        print(f"  MANUAL  confirm in Desktop's reply: {msg}")

    def skip(self, msg: str) -> None:
        print(f"  SKIP  {msg}")

    def done(self) -> int:
        verdict = "OK" if not self.failed else f"{self.failed} FAILED"
        print(f"  -> {self.scenario}: {verdict} (MANUAL items, if any, are confirmed by eye)")
        return 1 if self.failed else 0
