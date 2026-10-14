#!/usr/bin/env python3
"""Gate 27 — upgrading an encrypted brain must not un-ignore its plaintext vault (task #62).

Gates 17 and 19 prove encryption works for a brain encrypted by the *current* devkit. Neither
ever upgraded one, and that is where it broke: ``update_brain.py`` re-emitted ``.gitignore``
from the template, the template carries no encryption block, and the block — the only thing
keeping plaintext notes out of git — vanished. Every note was then one ``git add -A`` from the
remote. A second, quieter facet: the upgrade delivered ``vault/templates/not-a-note.md``, which
``encrypt_vault.MACHINERY`` did not name, so ``doctor.py`` reported it as a PLAINTEXT note.

What it does, hermetically::

    generate → git init → --enable → write a note → commit
             → age it: the ignore block's body as an OLDER devkit wrote it, and the
               not-a-note template missing, as in a brain encrypted before it shipped
             → update_brain --apply
             → assert: update succeeded, block present with the CURRENT body, the note is
               ignored and untracked, only MACHINERY is tracked under vault/, doctor reports
               no PLAINTEXT, and a second run is a no-op

Plus the converse, so the fix cannot over-reach: a **plaintext** brain's upgrade must not grow
an encryption block it never asked for.

Hermetic: git + stdlib + the optional ``cryptography`` (skipped without it, like gate 19).
Devkit tool, never emitted.

    python3 tools/check_encrypted_upgrade.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO_ROOT = TOOLS.parent
PY = sys.executable
sys.path.insert(0, str(TOOLS))
from generate import generate  # noqa: E402
import update_brain as ub  # noqa: E402  (also puts template/scripts on sys.path)
import encrypt_vault as ev  # noqa: E402

PASSPHRASE = "encrypted upgrade gate passphrase"
NOTE = "vault/projects/upgrade-canary.md"
# The block body as the devkit wrote it before #62: only new-note.md allow-listed.
OLD_BODY = "\n".join([
    "# Every note is content — default-deny, so a new file type cannot leak.",
    "# No directory under vault/ is committed: a folder name is a tell on its own.",
    "/vault/**",
    "# The devkit-owned note template is machinery, not content, and must stay readable.",
    "!/vault/templates/",
    "!/vault/templates/new-note.md",
])


def run(cmd: list[str], cwd: Path, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=600)


def git(root: Path, *args: str, env: dict) -> subprocess.CompletedProcess:
    return run(["git", *args], root, env)


def seed(brain: Path, env: dict) -> None:
    generate(brain)
    git(brain, "init", "-q", env=env)
    git(brain, "config", "commit.gpgsign", "false", env=env)
    git(brain, "config", "core.hooksPath", ".githooks", env=env)
    git(brain, "add", "-A", env=env)
    git(brain, "commit", "-q", "-m", "seed", env=env)


def update(brain: Path, env: dict) -> subprocess.CompletedProcess:
    return run([PY, "-B", str(TOOLS / "update_brain.py"), str(brain), "--apply"], REPO_ROOT, env)


def main() -> int:
    fails: list[str] = []

    def ok(msg): print(f"  ok    {msg}")

    def fail(msg): fails.append(msg); print(f"  FAIL  {msg}")

    if set(ev.MACHINERY) != set(ub.VAULT_OWNED):
        fail(f"encrypt_vault.MACHINERY {sorted(ev.MACHINERY)} != update_brain.VAULT_OWNED "
             f"{sorted(ub.VAULT_OWNED)} — a template the devkit overwrites but encryption treats "
             f"as content gets committed in the clear by every upgrade")
    else:
        ok("MACHINERY names exactly the vault files update_brain owns")

    try:
        import cryptography  # noqa: F401
    except ImportError:
        print("  note: optional 'cryptography' absent — skipping the encrypted upgrade")
        return 1 if fails else 0

    env = {**os.environ,
           "SECOND_BRAIN_EMBEDDER": "test",
           "SECOND_BRAIN_PASSPHRASE": PASSPHRASE,
           "GIT_AUTHOR_NAME": "Upgrade", "GIT_AUTHOR_EMAIL": "up@example.invalid",
           "GIT_COMMITTER_NAME": "Upgrade", "GIT_COMMITTER_EMAIL": "up@example.invalid"}

    parent = Path(tempfile.mkdtemp(prefix="enc-upgrade-"))
    try:
        # --- an encrypted brain, as an older devkit left it ------------------------------
        brain = parent / "encrypted"
        seed(brain, env)
        r = run([PY, "scripts/encrypt_vault.py", "--enable"], brain, env)
        if r.returncode != 0:
            fail(f"--enable failed: {(r.stderr or r.stdout).strip()[:200]}")
            return 1
        (brain / NOTE).parent.mkdir(parents=True, exist_ok=True)
        (brain / NOTE).write_text("---\ntags: [t]\n---\n\n# Canary\n\nPrivate.\n", encoding="utf-8")
        c = git(brain, "commit", "-q", "--allow-empty", "-m", "a note", env=env)
        if c.returncode != 0:
            fail(f"committing the note failed: {(c.stderr or c.stdout).strip()[:200]}")
            return 1

        gi = brain / ".gitignore"
        gi.write_text(ub.splice_block(gi.read_text(), ev.IGNORE_BEGIN, ev.IGNORE_END, OLD_BODY))
        git(brain, "rm", "-q", "--cached", "--ignore-unmatch", "vault/templates/not-a-note.md",
            env=env)
        (brain / "vault/templates/not-a-note.md").unlink(missing_ok=True)
        git(brain, "add", ".gitignore", env=env)
        git(brain, "commit", "-q", "--no-verify", "-m", "age the brain", env=env)

        # --- upgrade it ------------------------------------------------------------------
        u = update(brain, env)
        if u.returncode != 0:
            fail(f"update_brain --apply failed on an encrypted brain: "
                 f"{(u.stderr or u.stdout).strip()[-300:]}")
            return 1
        ok("update_brain --apply succeeded on an encrypted brain")

        text = gi.read_text()
        if ev.IGNORE_BEGIN not in text or ev.IGNORE_END not in text:
            fail("the upgrade DROPPED the encryption block from .gitignore — plaintext notes "
                 "are one `git add -A` from the remote")
        elif f"{ev.IGNORE_BEGIN}\n{ev.IGNORE_BODY}\n{ev.IGNORE_END}" not in text:
            fail("the encryption block survived but kept its OLD body — newly allow-listed "
                 "templates never reach a brain encrypted before them")
        else:
            ok("the encryption block survived, refreshed to the current body")

        if git(brain, "check-ignore", "-q", NOTE, env=env).returncode != 0:
            fail(f"{NOTE} is NOT ignored after the upgrade")
        else:
            ok("a plaintext note is still git-ignored")

        status = git(brain, "status", "--porcelain", "--", "vault", env=env).stdout.strip()
        if status:
            fail(f"git sees vault/ content after the upgrade: {status.splitlines()[:5]}")
        else:
            ok("git status shows nothing under vault/")

        tracked = sorted(git(brain, "ls-files", "vault", env=env).stdout.split())
        if tracked != sorted(ev.MACHINERY):
            fail(f"tracked under vault/ after the upgrade: {tracked}, expected exactly "
                 f"{sorted(ev.MACHINERY)}")
        else:
            ok("only the devkit-owned templates are tracked under vault/")

        d = run([PY, "scripts/doctor.py"], brain, env)
        if "PLAINTEXT" in d.stdout + d.stderr:
            fail("doctor reports a PLAINTEXT note after the upgrade: "
                 + next(ln for ln in (d.stdout + d.stderr).splitlines() if "PLAINTEXT" in ln))
        else:
            ok("doctor reports no PLAINTEXT note")

        again = run([PY, "-B", str(TOOLS / "update_brain.py"), str(brain)], REPO_ROOT, env)
        if "already up to date" not in again.stdout:
            fail("a second upgrade is not a no-op:\n" + again.stdout[-400:])
        else:
            ok("a second upgrade is a no-op")

        # --- the converse: a plaintext brain must not gain a block ----------------------
        plain = parent / "plaintext"
        seed(plain, env)
        pg = plain / ".gitignore"
        pg.write_text(pg.read_text() + "\n# stale\n")
        git(plain, "commit", "-qam", "stale gitignore", "--no-verify", env=env)
        u = update(plain, env)
        if u.returncode != 0:
            fail(f"update_brain --apply failed on a plaintext brain: {u.stdout[-300:]}")
        elif ev.IGNORE_BEGIN in pg.read_text():
            fail("a PLAINTEXT brain's upgrade added an encryption block — its notes would stop "
                 "being committed")
        else:
            ok("a plaintext brain's upgrade adds no encryption block")
    finally:
        shutil.rmtree(parent, ignore_errors=True)

    if fails:
        print(f"\nencrypted-upgrade FAILED: {len(fails)} assertion(s)", file=sys.stderr)
        return 1
    print("\nencrypted-upgrade OK: an upgraded encrypted brain keeps its vault ignored, receives "
          "the current allow-list, and doctor finds nothing in the clear")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
