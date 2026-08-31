#!/usr/bin/env python3
"""Gate 21 — a moved note stays in the brain (task #47).

Archiving a note used to remove it from the brain. Three correct-looking pieces:

  1. the pre-commit selector asked git for ``--diff-filter=ACM``. Git labels a staged
     move ``R`` (rename detection is on by default, so it collapses the delete+add into
     one entry), and ``R`` was not in the whitelist — so a moved note was **invisible** and
     nothing re-embedded it at its new path;
  2. sidecars are derived and git-ignored, so the move takes the ``.md`` and leaves the
     vector behind;
  3. ``update_cache --from-commit`` *does* understand renames — it deleted the old row and
     then died in ``upsert()`` on the new path's missing sidecar.

Net: the commit succeeds, the post-commit hook fails after the fact, and the note is gone
from the cache. The fix is one letter (``ACMR``), which is exactly why this gate exists —
a one-character regression restores a bug whose symptom appears one commit later, in a
different tool, as a note that simply is not there any more.

**How the file was moved is not a variable.** ``git mv`` and ``mv`` + ``git rm`` + ``git add``
produce an identical index; git infers the rename at *diff* time. So there is no user-side
workaround to test, and no wrapper script would have helped — Obsidian moves notes through
its own file explorer and never calls anything this brain ships.

Three scenarios, because they run through **different code**:

  • one note moved between PARA roots — the plaintext selector;
  • a whole project folder archived as one unit — the workflow the ``embed: false``
    colocation pattern exists for (task #45), and the first thing that depends on moves;
  • the same move on an **encrypted** brain, where selection does not consult git at all
    (task #42 made it read the working tree). That path was already correct, and pinning it
    is the point: it is correct for a reason, not by luck.

The assertion is the end-user promise — the note is **searchable at its new path** — not
merely that a row exists.

Hermetic: stdlib + git + sqlite-vec, deterministic ``test`` backend, no Ollama, no network.
Devkit tool, never emitted.

    python3 tools/check_note_move.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

sys.path.insert(0, str(REPO_ROOT / "tools"))
from generate import generate  # noqa: E402

PASSPHRASE = "note-move gate passphrase"
KILN = ("---\ntags: [ceramics]\n---\n\n# Kiln\n\n"
        "A bisque firing climbs to cone 06 slowly so trapped water escapes.\n")
GLAZE = ("---\ntags: [ceramics]\n---\n\n# Glaze\n\n"
         "Tenmoku breaks rust where it thins over an edge.\n")

_CACHE_QUERY = (
    "import sys; sys.path.insert(0, 'scripts');"
    "from db import connect;"
    "print('\\n'.join(r[0] for r in "
    "connect('data/brain.db').execute('SELECT source_file FROM notes')))"
)


def _run(argv: list[str], cwd: Path, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run([argv[0], "-B", *argv[1:]], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=600)


def _git(brain: Path, *args: str, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=brain, env=env,
                          capture_output=True, text=True, timeout=120)


def _cached(brain: Path, env: dict) -> set[str]:
    """Note paths the cache would answer with, read through the brain's own db.connect
    (``notes`` is a vec0 virtual table, so a plain sqlite3 connection cannot open it)."""
    r = _run([PY, "-c", _CACHE_QUERY], brain, env)
    if r.returncode != 0:
        raise SystemExit(f"note-move: cannot read the cache: {r.stderr.strip()[-300:]}")
    return {line for line in r.stdout.splitlines() if line}


def _finds(brain: Path, env: dict, query: str) -> str:
    """The top search hit for a query — the end-user promise, not an implementation detail."""
    r = _run([PY, "scripts/search_vault.py", query], brain, env)
    return r.stdout + r.stderr


def _new_brain(brain: Path, env: dict, *, encrypted: bool) -> None:
    generate(brain)
    _git(brain, "init", "-q", env=env)
    _git(brain, "config", "user.email", "move@example.invalid", env=env)
    _git(brain, "config", "user.name", "Move Check", env=env)
    _git(brain, "config", "commit.gpgsign", "false", env=env)
    _git(brain, "config", "core.hooksPath", ".githooks", env=env)
    _git(brain, "add", "-A", env=env)
    _git(brain, "commit", "-q", "-m", "seed brain", env=env)
    if encrypted:
        r = _run([PY, "scripts/encrypt_vault.py", "--enable"], brain, env)
        if r.returncode != 0:
            raise SystemExit(f"note-move: --enable failed: {(r.stderr or r.stdout)[-300:]}")
    # Embed + hydrate the seeded notes, so `doctor` starts CLEAN. Without this it reports the
    # seeds as cache drift and the move assertions cannot tell their own failure from the
    # scaffold's — a dirty baseline makes a green run meaningless in the other direction too.
    for script in ("embed_vault.py", "hydrate_cache.py"):
        r = _run([PY, f"scripts/{script}"], brain, env)
        if r.returncode != 0:
            raise SystemExit(f"note-move: {script} failed: {(r.stderr or r.stdout)[-300:]}")


def _commit(brain: Path, msg: str, env: dict) -> subprocess.CompletedProcess:
    _git(brain, "add", "-A", env=env)
    return _git(brain, "commit", "-q", "--allow-empty", "-m", msg, env=env)


def scenario_one_note(brain: Path, env: dict, fails: list[str], *, label: str) -> None:
    """Write a note, commit it, then archive it. It must survive the move."""
    src = brain / "vault" / "projects" / "kiln.md"
    src.write_text(KILN, encoding="utf-8")
    if _commit(brain, "note: kiln", env).returncode != 0:
        fails.append(f"[{label}] committing the note failed")
        return
    old_rel, new_rel = "vault/projects/kiln.md", "vault/archive/kiln.md"
    if old_rel not in _cached(brain, env):
        fails.append(f"[{label}] the note never reached the cache — the move test below "
                     f"would prove nothing")
        return

    _git(brain, "mv", old_rel, new_rel, env=env)
    c = _commit(brain, "archive the kiln note", env)
    if c.returncode != 0:
        fails.append(f"[{label}] the move commit failed: {c.stderr.strip()[-200:]}")
        return
    # The post-commit hook must not have fallen over. It cannot fail the commit, so its
    # error is the only signal — and the bug's whole shape was "commit fine, brain broken".
    if "cache update failed" in (c.stderr or ""):
        fails.append(f"[{label}] the post-commit cache update FAILED on a move: "
                     f"{c.stderr.strip()[-200:]}")

    if not (brain / "vault" / "archive" / ".kiln.embed.json").exists():
        fails.append(f"[{label}] the moved note was not re-embedded at its new path — "
                     f"nothing selected it, so it has no vector any more")
    if (brain / "vault" / "projects" / ".kiln.embed.json").exists():
        fails.append(f"[{label}] the old sidecar was left behind at the old path")

    cached = _cached(brain, env)
    if new_rel not in cached:
        fails.append(f"[{label}] the moved note is NOT in the cache — archiving a note "
                     f"removed it from the brain")
    if old_rel in cached:
        fails.append(f"[{label}] the cache still answers with the OLD path, which no longer "
                     f"exists — a search hit would point at a missing file")

    if "kiln.md" not in _finds(brain, env, "bisque firing cone temperature"):
        fails.append(f"[{label}] the moved note is not findable by search — the row may "
                     f"exist but the end-user promise is broken")

    d = _run([PY, "scripts/doctor.py"], brain, env)
    if d.returncode != 0:
        fails.append(f"[{label}] doctor is not clean after a move: "
                     f"{(d.stdout + d.stderr)[-300:]}")


def scenario_folder(brain: Path, env: dict, fails: list[str]) -> None:
    """Archive a whole project folder — the #45 colocation workflow, as one `git mv`."""
    folder = brain / "vault" / "projects" / "pottery"
    folder.mkdir(parents=True)
    (folder / "pottery.md").write_text(KILN, encoding="utf-8")
    (folder / "pottery--glaze.md").write_text(GLAZE, encoding="utf-8")
    if _commit(brain, "note: the pottery project", env).returncode != 0:
        fails.append("[folder] committing the project failed")
        return

    _git(brain, "mv", "vault/projects/pottery", "vault/archive/pottery", env=env)
    c = _commit(brain, "archive the pottery project", env)
    if c.returncode != 0:
        fails.append(f"[folder] the move commit failed: {c.stderr.strip()[-200:]}")
        return
    if "cache update failed" in (c.stderr or ""):
        fails.append(f"[folder] the post-commit cache update FAILED: {c.stderr.strip()[-200:]}")

    cached = _cached(brain, env)
    for name in ("pottery.md", "pottery--glaze.md"):
        if f"vault/archive/pottery/{name}" not in cached:
            fails.append(f"[folder] {name} did not follow the folder into archive/ — "
                         f"archiving a project as one unit loses its notes")
        if f"vault/projects/pottery/{name}" in cached:
            fails.append(f"[folder] the cache still holds the old path for {name}")


def scenario_encrypted(brain: Path, env: dict, fails: list[str]) -> None:
    """The same move on an encrypted brain — a genuinely different path, half of it already right.

    Selection here never asks git what changed (task #42 made it read the working tree), so the
    ``ACM``/``R`` bug could not reach it: the moved note was always re-embedded. What it *did*
    get wrong is the other half — nothing removed the vector left at the old path, because the
    post-commit cache update only ever sees an opaque blob and never a PARA note.

    Two further differences are pinned here rather than assumed. ``git mv`` **cannot be used at
    all** (the vault is git-ignored, so the source is not under version control), which is why
    this moves the file plainly. The cache IS asserted below, but only for the dead-path
    resurrection this bug caused; that an encrypted commit reaches the cache at all was a
    separate gap (task #48) and is gate 22's subject, not this one's.
    """
    src = brain / "vault" / "projects" / "kiln.md"
    src.write_text(KILN, encoding="utf-8")
    if _commit(brain, "note: kiln", env).returncode != 0:
        fails.append("[encrypted] committing the note failed")
        return
    old_side = brain / "vault" / "projects" / ".kiln.embed.json"
    if not old_side.exists():
        fails.append("[encrypted] the note was not embedded at all — the move test below "
                     "would prove nothing")
        return
    blobs_before = len(list((brain / "enc").glob("*.md.enc")))

    if _git(brain, "mv", "vault/projects/kiln.md", "vault/archive/kiln.md",
            env=env).returncode == 0:
        fails.append("[encrypted] `git mv` unexpectedly succeeded on a git-ignored vault — if "
                     "that is now possible this scenario is testing the wrong thing")
    (brain / "vault" / "archive" / "kiln.md").parent.mkdir(parents=True, exist_ok=True)
    src.rename(brain / "vault" / "archive" / "kiln.md")
    c = _commit(brain, "archive the kiln note", env)
    if c.returncode != 0:
        fails.append(f"[encrypted] the move commit failed: {c.stderr.strip()[-200:]}")
        return

    if not (brain / "vault" / "archive" / ".kiln.embed.json").exists():
        fails.append("[encrypted] the moved note was not re-embedded at its new path")
    if old_side.exists():
        fails.append("[encrypted] the old sidecar was left behind — the next hydrate_cache "
                     "reads it and inserts a row for a file that no longer exists, so search "
                     "starts answering with a dead path")
    blobs_after = len(list((brain / "enc").glob("*.md.enc")))
    if blobs_after != blobs_before:
        fails.append(f"[encrypted] the old blob was not dropped: {blobs_before} blob(s) before "
                     f"the move, {blobs_after} after")

    # Hydrate is the encrypted brain's only route into the cache, so run it and assert the
    # dead path never appears. This is what the orphan actually costs a user.
    if _run([PY, "scripts/hydrate_cache.py"], brain, env).returncode != 0:
        fails.append("[encrypted] hydrate_cache failed")
        return
    cached = _cached(brain, env)
    if "vault/projects/kiln.md" in cached:
        fails.append("[encrypted] hydrate resurrected the OLD path from the orphaned sidecar — "
                     "search would return a file that is not there")
    if "vault/archive/kiln.md" not in cached:
        fails.append("[encrypted] the moved note is not in the cache after hydrate")


def main() -> int:
    fails: list[str] = []
    base = {**os.environ, "SECOND_BRAIN_EMBEDDER": "test",
            "GIT_AUTHOR_NAME": "Move Check", "GIT_AUTHOR_EMAIL": "move@example.invalid",
            "GIT_COMMITTER_NAME": "Move Check", "GIT_COMMITTER_EMAIL": "move@example.invalid"}

    parent = Path(tempfile.mkdtemp(prefix="note-move-"))
    try:
        brain = parent / "plain"
        _new_brain(brain, base, encrypted=False)
        scenario_one_note(brain, base, fails, label="plaintext")
        scenario_folder(brain, base, fails)
        if not fails:
            print("  ok    a moved note is re-embedded at its new path and stays searchable")
            print("  ok    a whole project folder archives as one unit, notes and all")

        try:
            import cryptography  # noqa: F401
        except ImportError:
            print("        optional 'cryptography' absent — encrypted move not exercised")
        else:
            enc_env = {**base, "SECOND_BRAIN_PASSPHRASE": PASSPHRASE}
            enc = parent / "encrypted"
            before = len(fails)
            _new_brain(enc, enc_env, encrypted=True)
            scenario_encrypted(enc, enc_env, fails)
            if len(fails) == before:
                print("  ok    an encrypted brain re-embeds a moved note, drops the old blob, "
                      "and leaves no orphan vector behind")
    finally:
        shutil.rmtree(parent, ignore_errors=True)

    if fails:
        for f in fails:
            print(f"  FAIL  {f}", file=sys.stderr)
        print(f"\nnote-move FAILED: {len(fails)} assertion(s)", file=sys.stderr)
        return 1

    print("note-move OK: archiving a note or a whole project folder keeps it in the brain — "
          "re-embedded at the new path, old row dropped, still searchable, doctor clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
