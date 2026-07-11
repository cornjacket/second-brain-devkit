#!/usr/bin/env python3
"""Seed a target brain with a devkit test corpus, or tear it down — tasks #16 / #15.

The corpora live under ``tests/`` and are **devkit-internal, never emitted** into a
generated brain. This tool copies one *into* a brain you point at, and removes it
cleanly afterward — for exercising a brain at realistic scale (auto-link thresholds,
retrieval, benchmarking, CI, dogfooding) without hand-authoring notes.

Two corpora are available (``--corpus``):

- ``test``  — ``tests/seed-corpus/`` (task #16): 100 notes, 10 IT topics, ``seed_*.md``.
              The everything-adjacent stress corpus. **Default.**
- ``bench`` — ``tests/bench-corpus/`` (task #15): 200 notes, 10 far-apart domains,
              ``bench_*.md``. The topically-diverse benchmark / calibration corpus.

    python3 tools/test_corpus.py install <brain>                 # seed corpus (default)
    python3 tools/test_corpus.py install <brain> --corpus bench  # benchmark corpus
    python3 tools/test_corpus.py remove  <brain> --corpus bench

The **target is a path argument**, so the same tool serves CI, the internal
``sandbox/``, or an external/real brain. ``install`` also backs
``create_second_brain --seed-test-corpus`` / ``--seed-bench-corpus``. Both operations
are **idempotent**, and the two corpora are independent (distinct ``seed_``/``bench_``
prefixes), so installing/removing one never touches the other.

- **install** copies every ``<prefix>_*.md`` into ``<brain>/vault/resources/`` and
  commits them; the brain's own pre/post-commit hooks then embed + hydrate them (so the
  target needs a working embedder — real Ollama, or ``SECOND_BRAIN_EMBEDDER=test``).
- **remove** deletes each note (git rm) *and* its derived ``.embed.json`` sidecar
  (git-ignored, so unlinked directly), then commits the removal; the brain's post-commit
  hook drops the corresponding cache rows — leaving no remnant.

This is a devkit tool; it is never emitted into a brain.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Each corpus: the source dir under tests/ and its identifying filename prefix glob.
CORPORA = {
    "test":  {"dir": "seed-corpus",  "glob": "seed_*.md",  "label": "test corpus"},
    "bench": {"dir": "bench-corpus", "glob": "bench_*.md", "label": "benchmark corpus"},
}
DEFAULT_CORPUS = "test"
RESOURCES = ("vault", "resources")  # PARA root the corpus installs into


def _corpus(corpus: str) -> dict:
    if corpus not in CORPORA:
        raise SystemExit(
            f"test_corpus: unknown corpus {corpus!r} (choose from {', '.join(CORPORA)})"
        )
    return CORPORA[corpus]


def corpus_notes(corpus: str = DEFAULT_CORPUS) -> list[Path]:
    spec = _corpus(corpus)
    src = REPO_ROOT / "tests" / spec["dir"]
    notes = sorted(src.rglob(spec["glob"]))
    if not notes:
        raise SystemExit(f"test_corpus: no {spec['glob']} found under {src}")
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


def install_corpus(brain: Path, *, corpus: str = DEFAULT_CORPUS, commit: bool = True) -> int:
    """Copy ``corpus`` into ``<brain>/vault/resources/`` (flat) and optionally commit.

    Idempotent — copying overwrites, and re-committing an unchanged set is a no-op.
    Returns the number of notes installed.
    """
    label = _corpus(corpus)["label"]
    res = _resources_dir(brain)
    rels = []
    for src in corpus_notes(corpus):
        shutil.copyfile(src, res / src.name)
        rels.append("/".join(RESOURCES) + "/" + src.name)
    if commit:
        _git(brain, "add", "--", *rels)
        if _git(brain, "status", "--porcelain", "--", *rels).stdout.strip():
            _git(brain, "commit", "-q", "-m", f"test: seed {len(rels)} {label} note(s)")
    return len(rels)


def remove_corpus(brain: Path, *, corpus: str = DEFAULT_CORPUS, commit: bool = True) -> int:
    """Remove every note of ``corpus`` + its sidecar from ``<brain>``; optionally commit.

    git-removes the tracked notes and unlinks their git-ignored ``.embed.json``
    sidecars; the removal commit fires the brain's post-commit hook, which drops the
    matching cache rows — so no remnant is left. Idempotent. Returns the count removed.
    """
    spec = _corpus(corpus)
    res = _resources_dir(brain)
    notes = sorted(res.glob(spec["glob"]))
    if not notes:
        print(f"test_corpus: no {spec['label']} notes present — nothing to remove")
        return 0
    rels = ["/".join(RESOURCES) + "/" + n.name for n in notes]
    _git(brain, "rm", "-q", "--ignore-unmatch", "--", *rels)
    for note in notes:  # sidecars are git-ignored, so git rm won't touch them
        (note.parent / f".{note.stem}.embed.json").unlink(missing_ok=True)
    if commit and _git(brain, "status", "--porcelain").stdout.strip():
        _git(brain, "commit", "-q", "-m", f"test: remove {len(notes)} {spec['label']} note(s)")
    return len(notes)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Seed or tear down a brain's test corpus.")
    ap.add_argument("action", choices=("install", "remove"))
    ap.add_argument("brain", help="path to the target brain")
    ap.add_argument(
        "--corpus", choices=tuple(CORPORA), default=DEFAULT_CORPUS,
        help=f"which corpus to act on (default: {DEFAULT_CORPUS}). "
             "test = seed-corpus (IT, task #16); bench = bench-corpus (diverse, task #15).",
    )
    args = ap.parse_args(argv)
    brain = Path(args.brain).expanduser().resolve()
    label = CORPORA[args.corpus]["label"]

    if args.action == "install":
        n = install_corpus(brain, corpus=args.corpus)
        print(f"✅ installed {n} {label} note(s) into {brain}/{'/'.join(RESOURCES)} and committed")
    else:
        n = remove_corpus(brain, corpus=args.corpus)
        if n:
            print(f"✅ removed {n} {label} note(s) (+ sidecars) from {brain} and committed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
