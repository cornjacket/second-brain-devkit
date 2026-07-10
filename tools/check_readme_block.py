#!/usr/bin/env python3
"""Behavioral check for the README managed block (task #9) — splice, don't clobber.

A generated brain's ``README.md`` is a **hybrid**: the devkit owns the region between
its ``<!-- BEGIN/END generated … -->`` markers and regenerates it on ``update_brain``,
while the user owns everything outside. This check drives the whole flow end-to-end on a
throwaway ``test``-backend brain and asserts the contract holds.

What it asserts:
  1. A freshly created brain ships with both markers, and ``update_brain`` reports it
     already up to date (a create ≡ template no-op).
  2. After the user adds a preamble + appendix and the managed body goes stale,
     ``update_brain --apply`` **splices**: the user's preamble/appendix survive
     byte-for-byte, the managed body is regenerated to match ``template/README.md``,
     and it lands as one commit.
  3. Re-running ``--apply`` is idempotent (already up to date).
  4. A README with **no** markers (user took ownership) is left untouched — reported
     SKIP, byte-unchanged.
  5. A README with only one of the two markers is malformed — reported SKIP, not guessed.

Hermetic (git + stdlib only — no Ollama, no ``mcp``, no network), so it runs in the CI
gate. Also runnable on demand:

    python3 tools/check_readme_block.py

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
TOOLS = REPO_ROOT / "tools"
TEMPLATE_README = REPO_ROOT / "template" / "README.md"
PY = sys.executable

# Single source of truth for the marker strings: import them from update_brain so this
# check can never drift from the tool it exercises (or from template/README.md, which
# update_brain asserts carries the same markers).
sys.path.insert(0, str(TOOLS))
from update_brain import README_BEGIN, README_END, _managed_body  # noqa: E402

GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "devkit-ci",
    "GIT_AUTHOR_EMAIL": "ci@second-brain-devkit.local",
    "GIT_COMMITTER_NAME": "devkit-ci",
    "GIT_COMMITTER_EMAIL": "ci@second-brain-devkit.local",
}
ENV = {**os.environ, **{k: v for k, v in GIT_IDENTITY.items() if k not in os.environ}}


class CheckError(Exception):
    """A failed assertion, reported with context."""


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, env=ENV, capture_output=True, text=True)


def _git(repo: Path, *args: str) -> None:
    r = _run(["git", "-C", str(repo), *args])
    if r.returncode != 0:
        raise CheckError(f"git {' '.join(args)} failed: {r.stderr.strip()}")


def _update(brain: Path, *flags: str) -> str:
    r = _run([PY, str(TOOLS / "update_brain.py"), str(brain), *flags])
    if r.returncode != 0:
        raise CheckError(f"update_brain {' '.join(flags)} failed: {r.stdout}{r.stderr}")
    return r.stdout


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise CheckError(msg)


def _commit_all(brain: Path, msg: str) -> None:
    _git(brain, "add", "README.md")
    # --no-verify: not a note commit; skip the brain's embed/line-count hooks.
    _git(brain, "commit", "-q", "--no-verify", "-m", msg)


def run_checks() -> None:
    parent = Path(tempfile.mkdtemp(prefix="readme-block-"))
    brain = parent / "brain"
    try:
        # 1. create + pristine no-op --------------------------------------------------
        r = _run([PY, str(TOOLS / "create_second_brain.py"), str(brain)])
        if r.returncode != 0:
            raise CheckError(f"create_second_brain failed: {r.stdout}{r.stderr}")
        readme = brain / "README.md"
        text = readme.read_text()
        _require(README_BEGIN in text and README_END in text,
                 "fresh brain README is missing the managed-block markers")
        out = _update(brain)
        _require("already up to date" in out,
                 f"a pristine brain should be up to date, got:\n{out}")
        print("  ok: fresh brain ships with markers and is a create-time no-op")

        # 2. user edits + stale body -> splice preserves user space -------------------
        preamble = "# My personal brain\n\nwater the plants\n\n"
        appendix = "\n## My own section\n\nkeep this\n"
        # A sentence known to live in the managed body; mangling it forces a splice diff.
        canary = "no cloud, no external services."
        _require(canary in text, "test canary sentence not found in the brain README")
        stale = preamble + text.replace(canary, "STALE OLD TEXT.") + appendix
        readme.write_text(stale)
        _commit_all(brain, "user edits README")

        out = _update(brain, "--apply")
        _require("CHANGED  README.md" in out, f"expected README CHANGED, got:\n{out}")
        got = readme.read_text()
        _require(got.startswith("# My personal brain\n\nwater the plants\n\n"),
                 "user preamble was not preserved")
        _require(got.endswith("## My own section\n\nkeep this\n"),
                 "user appendix was not preserved")
        _require("STALE OLD TEXT." not in got, "stale managed-body text survived the splice")
        _require(canary in got, "managed body was not regenerated from the template")
        # the spliced managed body must byte-match the template's managed body
        _require(_managed_body(got) == _managed_body(TEMPLATE_README.read_text()),
                 "spliced managed body does not byte-match template/README.md")
        # it landed as a commit (working tree clean for README)
        st = _run(["git", "-C", str(brain), "status", "--porcelain", "README.md"])
        _require(st.stdout.strip() == "", "README update was not committed")
        print("  ok: --apply splices fresh body, preserves user preamble/appendix, commits")

        # 3. idempotency --------------------------------------------------------------
        out = _update(brain, "--apply")
        _require("already up to date" in out, f"second --apply should be a no-op, got:\n{out}")
        print("  ok: re-running --apply is idempotent")

        # 4. no markers -> SKIP, byte-unchanged ---------------------------------------
        nomarkers = got.replace(README_BEGIN, "").replace(README_END, "")
        readme.write_text(nomarkers)
        _commit_all(brain, "user removes markers")
        before = readme.read_bytes()
        out = _update(brain)
        _require("SKIP" in out and "README.md" in out and "user-owned" in out,
                 f"a marker-less README should be reported SKIP, got:\n{out}")
        _require(readme.read_bytes() == before, "a user-owned README must be left byte-unchanged")
        print("  ok: marker-less README is left to the user (SKIP, unchanged)")

        # 5. one marker only -> SKIP (malformed) --------------------------------------
        readme.write_text(README_BEGIN + "\n" + nomarkers)  # begin, no end
        _commit_all(brain, "malformed: one marker")
        out = _update(brain)
        _require("SKIP" in out and "one marker" in out,
                 f"a half-marked README should be reported SKIP, got:\n{out}")
        print("  ok: half-marked README is reported malformed, not guessed")

        print("\nreadme-block OK: 5/5 checks pass")
    finally:
        shutil.rmtree(parent, ignore_errors=True)


def main() -> int:
    try:
        run_checks()
    except CheckError as exc:
        print(f"\nreadme-block FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
