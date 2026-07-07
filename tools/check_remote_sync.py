#!/usr/bin/env python3
"""Behavioral check for remote-backed brains (task #6) — connect → push → clone-peer.

``create_second_brain.py --remote`` attaches a git remote and pushes the scaffold at creation.
CI byte-diffs the *emitted brain* but never exercises the remote flow, so this check
drives it end-to-end against a **local bare repo** (``git init --bare`` addressed by a
``file://`` URL) — a fully-functional git remote that needs **no network and no
credentials**. Only the auth layer (SSH/HTTPS) is skipped; that is a per-machine
runtime concern the preflight covers, not something CI should carry secrets for.

What it asserts:
  1. ``--remote`` into an empty bare repo succeeds, and the push lands the scaffold
     (the bare repo gains refs).
  2. Auto-sync default: a plain ``--remote`` brain has **no** ``secondbrain.autosync``
     key (absent ⇒ ON); ``--no-autosync`` writes an explicit ``false``.
  3. A ``git clone`` of the bare repo (an Approach-A peer) receives the vault notes
     and has ``origin`` wired, with no autosync key (peers auto-sync by default).
  4. Preflight refuses a **non-empty** remote and an **unreachable** remote, and in
     both cases creates **nothing** (non-destructive fail-early).

Hermetic (git + stdlib only — no Ollama, no ``mcp``, no network), so it runs in the
CI gate. Also runnable on demand:

    python3 tools/check_remote_sync.py

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
CREATE_SECOND_BRAIN = REPO_ROOT / "tools" / "create_second_brain.py"
PY = sys.executable

# A self-contained git identity so the brain's first commit (and the preflight
# identity probe) pass on a bare runner with no global git config. Only fills gaps.
GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "devkit-ci",
    "GIT_AUTHOR_EMAIL": "ci@second-brain-devkit.local",
    "GIT_COMMITTER_NAME": "devkit-ci",
    "GIT_COMMITTER_EMAIL": "ci@second-brain-devkit.local",
}
ENV = {**os.environ, **{k: v for k, v in GIT_IDENTITY.items() if k not in os.environ}}

# A note the seeded vault is known to contain — used to prove a cloned peer got the
# content, not just the refs.
SEED_NOTE = "vault/projects/second-brain.md"


class CheckError(Exception):
    """A failed assertion, reported with context."""


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, env=ENV, capture_output=True, text=True)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return _run(["git", "-C", str(repo), *args])


def _bare_remote(root: Path, name: str) -> str:
    """Create an empty bare repo under ``root`` and return its ``file://`` URL."""
    bare = root / name
    r = _run(["git", "init", "--bare", "-q", str(bare)])
    if r.returncode != 0:
        raise CheckError(f"git init --bare failed: {r.stderr.strip()}")
    return bare.as_uri()  # file:///abs/path/name.git


def _create_second_brain(target: Path, *remote_args: str) -> subprocess.CompletedProcess:
    return _run([PY, str(CREATE_SECOND_BRAIN), str(target), *remote_args])


def _autosync(repo: Path) -> str | None:
    """The brain's ``secondbrain.autosync`` value, or None if absent (⇒ ON)."""
    r = _git(repo, "config", "--get", "secondbrain.autosync")
    return r.stdout.strip() if r.returncode == 0 else None


def check_connect_and_push(work: Path) -> None:
    url = _bare_remote(work, "origin.git")
    brain = work / "brain"
    r = _create_second_brain(brain, "--remote", url)
    if r.returncode != 0:
        raise CheckError(f"--remote into an empty bare repo failed:\n{r.stderr}")
    if not brain.exists():
        raise CheckError("brain dir was not created despite success")

    # The push landed: the bare remote now advertises refs.
    ls = _run(["git", "ls-remote", url])
    if ls.returncode != 0 or not ls.stdout.strip():
        raise CheckError(f"remote has no refs after push (push didn't land):\n{ls.stderr}")

    # origin + upstream wired.
    origin = _git(brain, "remote", "get-url", "origin").stdout.strip()
    if origin != url:
        raise CheckError(f"origin is {origin!r}, expected {url!r}")
    upstream = _git(brain, "rev-parse", "--abbrev-ref", "@{u}")
    if upstream.returncode != 0:
        raise CheckError("no upstream set (push -u didn't track)")

    # Auto-sync ON by default ⇒ no explicit key written.
    if (val := _autosync(brain)) is not None:
        raise CheckError(f"expected no autosync key (ON by default), found {val!r}")
    print("  ok  connect + push: scaffold pushed, origin+upstream set, autosync default ON")


def check_no_autosync(work: Path) -> None:
    url = _bare_remote(work, "manual.git")
    brain = work / "manual-brain"
    r = _create_second_brain(brain, "--remote", url, "--no-autosync")
    if r.returncode != 0:
        raise CheckError(f"--remote --no-autosync failed:\n{r.stderr}")
    if (val := _autosync(brain)) != "false":
        raise CheckError(f"expected secondbrain.autosync=false, found {val!r}")
    print("  ok  --no-autosync: secondbrain.autosync=false recorded")


def check_clone_peer(work: Path) -> None:
    url = _bare_remote(work, "shared.git")
    brain = work / "author-brain"
    r = _create_second_brain(brain, "--remote", url)
    if r.returncode != 0:
        raise CheckError(f"author brain --remote failed:\n{r.stderr}")

    peer = work / "peer"
    clone = _run(["git", "clone", "-q", url, str(peer)])
    if clone.returncode != 0:
        raise CheckError(f"cloning the peer failed:\n{clone.stderr}")

    # The peer received the actual note content, not just refs.
    if not (peer / SEED_NOTE).exists():
        raise CheckError(f"peer clone is missing {SEED_NOTE}")
    # A cloned peer wires origin automatically and has no autosync key ⇒ syncs by default.
    if _git(peer, "remote", "get-url", "origin").stdout.strip() != url:
        raise CheckError("peer origin not wired to the shared remote")
    if (val := _autosync(peer)) is not None:
        raise CheckError(f"peer should have no autosync key (default ON), found {val!r}")
    print("  ok  clone-as-peer: received notes + origin wired, autosync default ON")


def check_preflight_non_empty(work: Path) -> None:
    # Populate a remote by connecting one brain, then aim a second brain at it.
    url = _bare_remote(work, "populated.git")
    first = work / "first"
    if _create_second_brain(first, "--remote", url).returncode != 0:
        raise CheckError("setup: seeding the populated remote failed")

    second = work / "second"
    r = _create_second_brain(second, "--remote", url)
    if r.returncode == 0:
        raise CheckError("preflight accepted a NON-EMPTY remote (should refuse)")
    if second.exists():
        raise CheckError("non-empty preflight failed but still created the brain dir")
    if "not empty" not in (r.stderr + r.stdout):
        raise CheckError(f"non-empty rejection lacked a clear message:\n{r.stderr}")
    print("  ok  preflight: refuses a non-empty remote, creates nothing")


def check_preflight_unreachable(work: Path) -> None:
    url = (work / "does-not-exist.git").as_uri()  # valid file:// URL, no repo there
    brain = work / "unreachable-brain"
    r = _create_second_brain(brain, "--remote", url)
    if r.returncode == 0:
        raise CheckError("preflight accepted an UNREACHABLE remote (should refuse)")
    if brain.exists():
        raise CheckError("unreachable preflight failed but still created the brain dir")
    print("  ok  preflight: refuses an unreachable remote, creates nothing")


CHECKS = [
    ("connect + push", check_connect_and_push),
    ("--no-autosync toggle", check_no_autosync),
    ("clone-as-peer (Approach A)", check_clone_peer),
    ("preflight: non-empty remote", check_preflight_non_empty),
    ("preflight: unreachable remote", check_preflight_unreachable),
]


def main() -> int:
    print("remote-sync check — local bare repo, no network/credentials\n")
    failures = 0
    for name, fn in CHECKS:
        work = Path(tempfile.mkdtemp(prefix="remote-sync-"))
        try:
            fn(work)
        except CheckError as exc:
            print(f"  FAIL  {name}: {exc}")
            failures += 1
        finally:
            shutil.rmtree(work, ignore_errors=True)

    total = len(CHECKS)
    print()
    if failures:
        print(f"remote-sync FAILED: {failures}/{total} check(s) regressed")
        return 1
    print(f"remote-sync OK: {total}/{total} checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
