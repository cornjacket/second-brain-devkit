#!/usr/bin/env python3
"""Non-destructively upgrade an existing brain's tooling from this devkit (G4).

``new_brain.py`` can only *create* a brain (it refuses a non-empty target), so once a
brain is generated and filled with notes there is no supported way to pull in later
devkit improvements — new scripts, bug fixes, WAL, the MCP server — short of delete +
regenerate, which destroys the vault and git history. This closes that gap.

What it does:
  • Re-emits the **tooling** a brain ships — ``scripts/``, ``skill/``, ``.githooks/``,
    ``requirements*.txt``, ``tests/``, ``seeds/``, ``README.md`` … — from the tracked
    ``template/`` tree, picking up whatever the manifest now emits (so a new file like
    ``scripts/mcp_server.py`` is added automatically).
  • **Never touches your data:** ``vault/`` (notes), ``data/`` (cache), ``config/``
    (backend choice), or the personalizable ``CLAUDE.md`` / ``GEMINI.md`` — and never
    rewrites history.
  • **Dry-run by default** (shows NEW / CHANGED / preserved). ``--apply`` writes the
    files and records a single, git-revertable commit in the brain's own repo.

    python3 tools/update_brain.py ~/my-brain            # preview
    python3 tools/update_brain.py ~/my-brain --apply     # write + commit

Limits (MVP): additive — it adds/updates tooling but never *deletes* a file the devkit
no longer emits, and it can't tell a user-edited tooling file from an old version
(everything is git-revertable, and ``--apply`` refuses a dirty tree so the update lands
as an isolated commit). This is a devkit tool; it is never emitted into a brain.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = REPO_ROOT / "template"

# User territory — re-emitting these could clobber notes, the cache, the chosen
# backend, or personal memory. Never written. (vault/ isn't in template/ anyway.)
PRESERVE_DIRS = ("vault/", "data/", "config/")
PRESERVE_FILES = ("CLAUDE.md", "GEMINI.md")


def _is_preserved(rel: str) -> bool:
    return rel in PRESERVE_FILES or rel.startswith(PRESERVE_DIRS)


def _git(brain: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", str(brain), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit(f"update_brain: `git {' '.join(args)}` failed in {brain}")
    return r


def _differs(src: Path, dst: Path) -> str:
    """Classify src vs dst: 'new' | 'changed' | 'same' (symlink- and mode-aware)."""
    if not dst.exists() and not dst.is_symlink():
        return "new"
    if src.is_symlink() or dst.is_symlink():
        s = os.readlink(src) if src.is_symlink() else None
        d = os.readlink(dst) if dst.is_symlink() else None
        return "same" if s == d else "changed"
    if src.read_bytes() != dst.read_bytes():
        return "changed"
    return "same"


def _write(src: Path, dst: Path) -> None:
    """Replace dst with src, preserving symlinks and modes."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    if src.is_symlink():
        os.symlink(os.readlink(src), dst)
    else:
        shutil.copy2(src, dst)  # bytes + mode (exec bits)


def _looks_like_brain(brain: Path) -> bool:
    return (brain / "scripts" / "embedder.py").is_file() and (brain / ".git").exists()


def plan(brain: Path) -> tuple[list[str], list[str]]:
    """Return (new, changed) tooling paths (rel), skipping preserved files."""
    if not TEMPLATE.is_dir():
        raise SystemExit(f"update_brain: no template at {TEMPLATE} — run build_template.py")
    new: list[str] = []
    changed: list[str] = []
    for src in sorted(TEMPLATE.rglob("*")):
        if src.is_dir() and not src.is_symlink():
            continue
        rel = src.relative_to(TEMPLATE).as_posix()
        if _is_preserved(rel):
            continue
        verdict = _differs(src, brain / rel)
        if verdict == "new":
            new.append(rel)
        elif verdict == "changed":
            changed.append(rel)
    return new, changed


def update_brain(target, *, apply: bool = False) -> int:
    brain = Path(target).expanduser().resolve()
    if not brain.is_dir():
        raise SystemExit(f"update_brain: {brain} is not a directory")
    if brain == REPO_ROOT:
        raise SystemExit("update_brain: that's the devkit itself, not a brain")
    if not _looks_like_brain(brain):
        raise SystemExit(
            f"update_brain: {brain} doesn't look like a generated brain "
            "(needs scripts/embedder.py and its own .git)"
        )

    new, changed = plan(brain)
    devkit_sha = _git(REPO_ROOT, "rev-parse", "--short", "HEAD", check=False).stdout.strip()

    print(f"update_brain: {brain}")
    if devkit_sha:
        print(f"  from devkit {devkit_sha}")
    print()
    for rel in new:
        print(f"  NEW      {rel}")
    for rel in changed:
        print(f"  CHANGED  {rel}")
    print(f"\npreserved (never touched): vault/, data/, config/, CLAUDE.md, "
          "GEMINI.md, git history")

    if not (new or changed):
        print("\n✅ already up to date — nothing to do.")
        return 0

    if not apply:
        print(f"\nDry run — re-run with --apply to write {len(new) + len(changed)} "
              "file(s) and commit them in the brain.")
        return 0

    # --apply: refuse a dirty tree so the update lands as an isolated, revertable commit.
    if _git(brain, "status", "--porcelain").stdout.strip():
        raise SystemExit(
            "update_brain: brain has uncommitted changes — commit or stash them first, "
            "so this update lands as its own commit."
        )

    for rel in new + changed:
        _write(TEMPLATE / rel, brain / rel)
        print(f"  wrote {rel}")

    _git(brain, "add", "--", *(new + changed))
    msg = "chore: update tooling from second-brain-devkit"
    if devkit_sha:
        msg += f" ({devkit_sha})"
    # --no-verify: this is tooling, not a note commit; skip the embed/line-count hook.
    _git(brain, "commit", "-q", "--no-verify", "-m", msg)
    head = _git(brain, "rev-parse", "--short", "HEAD").stdout.strip()
    print(f"\n✅ updated {len(new) + len(changed)} file(s); committed {head} in {brain}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Non-destructively upgrade an existing brain's tooling (G4).",
    )
    ap.add_argument("target", help="path to an existing brain (e.g. ~/my-brain)")
    ap.add_argument("--apply", action="store_true",
                    help="write the files and commit (default: dry-run preview)")
    args = ap.parse_args(argv)
    return update_brain(args.target, apply=args.apply)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
