#!/usr/bin/env python3
"""Seed a target brain with the test corpus, or tear it down — task #16.

The corpus (``tests/seed-corpus/``) is devkit-internal and never emitted into a
generated brain. This tool copies it *into* a brain you point at, and removes it
cleanly afterward — for exercising a brain at realistic scale (auto-link thresholds,
retrieval, benchmarking, CI, dogfooding) without hand-authoring notes.

    python3 tools/test_corpus.py install <brain>   # copy the notes in + commit them
    python3 tools/test_corpus.py remove  <brain>   # delete the notes (+ remnants) + commit

The **target is a path argument**, so the same tool serves CI, the internal
``sandbox/``, or an external/real brain. ``install`` also backs
``create_second_brain --seed-test-corpus``. Both operations are **idempotent**.

- **install** copies every ``seed_*.md`` into ``<brain>/vault/resources/`` and commits
  them; the brain's own pre/post-commit hooks then embed + hydrate them (so the target
  needs a working embedder — real Ollama, or ``SECOND_BRAIN_EMBEDDER=test``).
- **remove** deletes each ``seed_*.md`` note (git rm) *and* its derived ``.embed.json``
  sidecar (git-ignored, so unlinked directly), then commits the removal; the brain's
  post-commit hook drops the corresponding cache rows — leaving no remnant.

This is a devkit tool; it is never emitted into a brain.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS = REPO_ROOT / "tests" / "seed-corpus"
SEED_GLOB = "seed_*.md"
RESOURCES = ("vault", "resources")  # PARA root the corpus installs into


def corpus_notes() -> list[Path]:
    notes = sorted(CORPUS.rglob(SEED_GLOB))
    if not notes:
        raise SystemExit(f"test_corpus: no {SEED_GLOB} found under {CORPUS}")
    return notes


def _resources_dir(brain: Path) -> Path:
    res = brain.joinpath(*RESOURCES)
    if not res.is_dir() or not (brain / ".git").exists():
        raise SystemExit(
            f"test_corpus: {brain} is not a brain "
            f"(need {'/'.join(RESOURCES)}/ and a git repo)."
        )
    return res


def _git(brain: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", str(brain), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.stderr.write(r.stdout)
        sys.stderr.write(r.stderr)
        raise SystemExit(f"test_corpus: `git {' '.join(args)}` failed in {brain}")
    return r


def install_corpus(brain: Path, *, commit: bool = True) -> int:
    """Copy the corpus into ``<brain>/vault/resources/`` (flat) and optionally commit.

    Idempotent — copying overwrites, and re-committing an unchanged set is a no-op.
    Returns the number of notes installed.
    """
    res = _resources_dir(brain)
    rels = []
    for src in corpus_notes():
        shutil.copyfile(src, res / src.name)
        rels.append("/".join(RESOURCES) + "/" + src.name)
    if commit:
        _git(brain, "add", "--", *rels)
        if _git(brain, "status", "--porcelain", "--", *rels).stdout.strip():
            _git(brain, "commit", "-q", "-m", f"test: seed {len(rels)} test-corpus note(s)")
    return len(rels)


def remove_corpus(brain: Path, *, commit: bool = True) -> int:
    """Remove every ``seed_*.md`` note + its sidecar from ``<brain>``; optionally commit.

    git-removes the tracked notes and unlinks their git-ignored ``.embed.json``
    sidecars; the removal commit fires the brain's post-commit hook, which drops the
    matching cache rows — so no remnant is left. Idempotent. Returns the count removed.
    """
    res = _resources_dir(brain)
    notes = sorted(res.glob(SEED_GLOB))
    if not notes:
        print("test_corpus: no test-corpus notes present — nothing to remove")
        return 0
    rels = ["/".join(RESOURCES) + "/" + n.name for n in notes]
    _git(brain, "rm", "-q", "--ignore-unmatch", "--", *rels)
    for note in notes:  # sidecars are git-ignored, so git rm won't touch them
        (note.parent / f".{note.stem}.embed.json").unlink(missing_ok=True)
    if commit and _git(brain, "status", "--porcelain").stdout.strip():
        _git(brain, "commit", "-q", "-m", f"test: remove {len(notes)} test-corpus note(s)")
    return len(notes)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Seed or tear down a brain's test corpus.")
    ap.add_argument("action", choices=("install", "remove"))
    ap.add_argument("brain", help="path to the target brain")
    args = ap.parse_args(argv)
    brain = Path(args.brain).expanduser().resolve()

    if args.action == "install":
        n = install_corpus(brain)
        print(f"✅ installed {n} test-corpus note(s) into {brain}/{'/'.join(RESOURCES)} and committed")
    else:
        n = remove_corpus(brain)
        if n:
            print(f"✅ removed {n} test-corpus note(s) (+ sidecars) from {brain} and committed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
