#!/usr/bin/env python3
"""Gate 22 — committing a note makes it searchable, in BOTH modes (task #48).

This is the product's central promise. The README and the emitted ``CLAUDE.md`` both say a
committed note is searchable immediately — no manual step — and until this gate nobody had
ever asserted it end to end on an **encrypted** brain, where it was false.

The failure was silent in the worst way: every visible signal said success. The pre-commit
hook really did embed the note and write its sidecar. The commit really did land. The
post-commit hook really did run, print ``no PARA-note changes in HEAD``, and **exit 0**. The
note simply was not in the cache, and stayed invisible to search until someone ran
``hydrate_cache`` by hand.

The cause is the shape this repo keeps rediscovering: **a component asking git a question a
git-ignored vault cannot answer.** An encrypted commit contains ``enc/<opaque>.md.enc`` and
nothing else, so ``git diff-tree`` truthfully reports no PARA notes. Task #42 fixed four
selectors this way, #47 a fifth; this was the last one, and the audit that found it
(grepping every ``git diff``-shaped call in the emitted scripts) found no others.

So the assertion here is deliberately the **user-visible** one — `search_vault` returns the
note — not "a row exists". A row is an implementation detail; being findable is the promise.

The full lifecycle, in each mode, because each step goes through different code:

    create → search finds it
    edit   → search finds the NEW wording (the row was replaced, not just present)
    move   → search finds it at the new path and not the old
    delete → search stops finding it

Hermetic: stdlib + git + sqlite-vec, deterministic ``test`` backend, no Ollama, no network.
The encrypted half skips cleanly when the optional ``cryptography`` dep is absent — and says
so, rather than counting a skip as coverage.

    python3 tools/check_commit_indexes.py

Devkit tool; never emitted.
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

PASSPHRASE = "commit-index gate passphrase"
# Two bodies with disjoint vocabulary, so "the edit landed" is a real question: the second
# search term does not occur in the first version at all.
V1 = ("---\ntags: [ceramics]\n---\n\n# Kiln\n\n"
      "A bisque firing climbs to cone 06 so trapped water escapes before vitrification.\n")
V2 = ("---\ntags: [ceramics]\n---\n\n# Kiln\n\n"
      "Tenmoku glaze breaks rust coloured where it thins over a sharp throwing rib.\n")
Q1 = "bisque firing trapped water vitrification"
Q2 = "tenmoku glaze breaks rust throwing rib"


def _run(argv: list[str], cwd: Path, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run([argv[0], "-B", *argv[1:]], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=600)


def _git(brain: Path, *args: str, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=brain, env=env,
                          capture_output=True, text=True, timeout=120)


def _commit(brain: Path, msg: str, env: dict) -> subprocess.CompletedProcess:
    _git(brain, "add", "-A", env=env)
    return _git(brain, "commit", "--allow-empty", "-m", msg, env=env)


def _search(brain: Path, env: dict, query: str) -> str:
    r = _run([PY, "scripts/search_vault.py", query], brain, env)
    return r.stdout + r.stderr


# Search always returns the top k, because a KNN ranks every row no matter what was asked —
# so "is it absent from the results?" is only meaningful for a row that is genuinely GONE,
# never for one that merely should not rank. To assert an EDIT landed, read the lexical row
# itself: that is the concrete claim (the row was replaced), and it is deterministic.
_FTS_QUERY = (
    "import sys; sys.path.insert(0, 'scripts');"
    "from db import connect;"
    "print(next((r[0] for r in connect('data/brain.db').execute("
    "'SELECT body FROM notes_fts WHERE source_file = ?', (sys.argv[1],))), ''))"
)


def _fts_body(brain: Path, env: dict, rel: str) -> str:
    r = _run([PY, "-c", _FTS_QUERY, rel], brain, env)
    return r.stdout


def _setup(brain: Path, env: dict, *, encrypted: bool) -> None:
    generate(brain)
    _git(brain, "init", "-q", env=env)
    _git(brain, "config", "user.email", "idx@example.invalid", env=env)
    _git(brain, "config", "user.name", "Index Check", env=env)
    _git(brain, "config", "commit.gpgsign", "false", env=env)
    _git(brain, "config", "core.hooksPath", ".githooks", env=env)
    _git(brain, "add", "-A", env=env)
    _git(brain, "commit", "-q", "-m", "seed brain", env=env)
    if encrypted:
        r = _run([PY, "scripts/encrypt_vault.py", "--enable"], brain, env)
        if r.returncode != 0:
            raise SystemExit(f"commit-index: --enable failed: {(r.stderr or r.stdout)[-300:]}")
    # Embed + hydrate the seeded notes so `doctor` starts CLEAN. A dirty baseline would make
    # this gate's own failures indistinguishable from the scaffold's, in both directions.
    for script in ("embed_vault.py", "hydrate_cache.py"):
        r = _run([PY, f"scripts/{script}"], brain, env)
        if r.returncode != 0:
            raise SystemExit(f"commit-index: {script} failed: {(r.stderr or r.stdout)[-300:]}")


def lifecycle(brain: Path, env: dict, fails: list[str], label: str) -> None:
    note = brain / "vault" / "projects" / "kiln.md"
    archived = brain / "vault" / "archive" / "kiln.md"

    # --- create ---------------------------------------------------------------------
    note.write_text(V1, encoding="utf-8")
    c = _commit(brain, "note: kiln", env)
    if c.returncode != 0:
        fails.append(f"[{label}] committing a new note failed: {c.stderr.strip()[-200:]}")
        return
    # The hook cannot fail the commit, so its own report is the only signal it went wrong.
    if "NOT in the search cache" in (c.stderr or ""):
        fails.append(f"[{label}] the post-commit cache update went blind: "
                     f"{c.stderr.strip()[-200:]}")
    if "kiln.md" not in _search(brain, env, Q1):
        fails.append(f"[{label}] a COMMITTED note is not searchable — the promise the README "
                     f"and CLAUDE.md both make ('searchable immediately, no manual step')")
        return

    # --- edit -----------------------------------------------------------------------
    note.write_text(V2, encoding="utf-8")
    if _commit(brain, "note: rewrite kiln", env).returncode != 0:
        fails.append(f"[{label}] committing an edit failed")
        return
    if "kiln.md" not in _search(brain, env, Q2):
        fails.append(f"[{label}] an EDITED note is not findable by its new wording")
    body = _fts_body(brain, env, "vault/projects/kiln.md")
    if "tenmoku" not in body.lower():
        fails.append(f"[{label}] the lexical row still does not hold the EDITED text — the "
                     f"commit did not refresh it, so search answers from the old wording")
    if "bisque" in body.lower():
        fails.append(f"[{label}] the lexical row still holds the text the note no longer "
                     f"contains — the row was added beside the old one, not replaced")

    # --- move -----------------------------------------------------------------------
    archived.parent.mkdir(parents=True, exist_ok=True)
    note.rename(archived)
    if _commit(brain, "archive kiln", env).returncode != 0:
        fails.append(f"[{label}] committing a move failed")
        return
    hit = _search(brain, env, Q2)
    if "archive/kiln.md" not in hit:
        fails.append(f"[{label}] a MOVED note is not searchable at its new path")
    if "projects/kiln.md" in hit:
        fails.append(f"[{label}] search still answers with the OLD path, which is now a file "
                     f"that does not exist")

    # --- delete ---------------------------------------------------------------------
    archived.unlink()
    if _commit(brain, "delete kiln", env).returncode != 0:
        fails.append(f"[{label}] committing a deletion failed")
        return
    if "kiln.md" in _search(brain, env, Q2):
        fails.append(f"[{label}] a DELETED note is still returned by search")

    d = _run([PY, "scripts/doctor.py"], brain, env)
    if d.returncode != 0:
        fails.append(f"[{label}] doctor is not clean after the lifecycle: "
                     f"{(d.stdout + d.stderr)[-300:]}")


def check_blind_is_loud(brain: Path, env: dict, fails: list[str]) -> None:
    """With the keys unavailable, the updater must SAY so and fail — never report success.

    Returning "nothing changed" here is the #48 bug itself: an empty answer that is
    indistinguishable from a quiet, correct no-op. Reachable in practice only sideways (the
    pre-commit hook refuses the commit outright without a passphrase), but it is the exact
    behaviour the fix turns on, so it is asserted rather than assumed.
    """
    blind = {k: v for k, v in env.items() if k != "SECOND_BRAIN_PASSPHRASE"}
    r = _run([PY, "scripts/update_cache.py", "--from-commit", "HEAD"], brain, blind)
    out = r.stdout + r.stderr
    if r.returncode == 0:
        fails.append("update_cache exited 0 with no way to read the commit — a cache it "
                     "could not update must never report success")
    if "doctor.py --repair" not in out:
        fails.append(f"the blind-cache message does not name the command that fixes it: "
                     f"{out.strip()[-200:]}")


def main() -> int:
    fails: list[str] = []
    base = {**os.environ, "SECOND_BRAIN_EMBEDDER": "test",
            "GIT_AUTHOR_NAME": "Index Check", "GIT_AUTHOR_EMAIL": "idx@example.invalid",
            "GIT_COMMITTER_NAME": "Index Check", "GIT_COMMITTER_EMAIL": "idx@example.invalid"}
    parent = Path(tempfile.mkdtemp(prefix="commit-index-"))
    try:
        plain = parent / "plain"
        _setup(plain, base, encrypted=False)
        before = len(fails)
        lifecycle(plain, base, fails, "plaintext")
        if len(fails) == before:
            print("  ok    plaintext: create/edit/move/delete each reach search on commit")

        try:
            import cryptography  # noqa: F401
        except ImportError:
            print("        optional 'cryptography' absent — the ENCRYPTED half, which is the "
                  "half that was broken, was NOT exercised")
        else:
            enc_env = {**base, "SECOND_BRAIN_PASSPHRASE": PASSPHRASE}
            enc = parent / "encrypted"
            _setup(enc, enc_env, encrypted=True)
            before = len(fails)
            lifecycle(enc, enc_env, fails, "encrypted")
            if len(fails) == before:
                print("  ok    encrypted: the same, though the commit holds only opaque blobs")
            before = len(fails)
            check_blind_is_loud(enc, enc_env, fails)
            if len(fails) == before:
                print("  ok    an unreadable encrypted commit fails loudly instead of "
                      "reporting 'nothing changed'")
    finally:
        shutil.rmtree(parent, ignore_errors=True)

    if fails:
        for f in fails:
            print(f"  FAIL  {f}", file=sys.stderr)
        print(f"\ncommit-index FAILED: {len(fails)} assertion(s)", file=sys.stderr)
        return 1

    print("commit-index OK: a committed note is searchable immediately in both modes — "
          "created, edited, moved and deleted — and a cache that cannot be read says so")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
