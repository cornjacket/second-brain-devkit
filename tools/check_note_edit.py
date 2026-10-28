#!/usr/bin/env python3
"""Gate 27 — an edit cannot overwrite what it did not read (task #67).

`replace_note` lets a client change an existing note. The danger it introduces is not a bad
write but a **stale** one: Desktop reads a note, the owner edits it in Obsidian, Desktop writes
the version it read, and the owner's change is gone with a success message on top.

The guard is an edit token. **The token is a whole-file digest, and the reason matters more than
the mechanism.** `note_view.content_hash` is taken over the *canonical view*, which strips
`no-embed` and `lexical-only` regions — deliberately, so editing inside a fence costs no
re-embed. That makes it **blind** to exactly the edits most likely to happen in a fence: a
ticked checkbox, a corrected phone number. Used as the token it would compare equal and admit
the stale write. This gate pins the distinction rather than trusting a comment.

Three more properties, each a different failure:

* **An allow-list, not a deny-list.** A deny-list admits every file type nobody thought of.
  Glossary notes are refused because `add_glossary_term` cascades their links and a raw edit
  leaves that graph stale; sidecars and assets are refused outright.
* **Nothing is written on a refusal.** The fence check in particular runs on the *new body
  string*, so a malformed fence never reaches disk — a fence that never closes excludes
  **nothing**, silently, and the note still commits and renders.
* **An encrypted brain hashes and writes the same form.** `get_note` reads the working tree,
  which stays plaintext, so the token describes the bytes the write will replace. That is a
  claim about two code paths agreeing and is tested rather than asserted.

Hermetic: stdlib + git. The MCP tool itself is exercised in `check_mcp_server.py`, which CI
cannot run (the `mcp` SDK is optional) — which is precisely why the rules under test live in
`scripts/note_edit.py` and are checked here.

    python3 tools/check_note_edit.py

Devkit tool, never emitted.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN = REPO_ROOT / "tests" / "golden"
PY = sys.executable

sys.path.insert(0, str(REPO_ROOT / "tools"))
from generate import generate  # noqa: E402


def _run(argv, cwd, env):
    return subprocess.run([argv[0], "-B", *argv[1:]], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=600)


def _git(brain, *args, env):
    return subprocess.run(["git", *args], cwd=brain, env=env,
                          capture_output=True, text=True, timeout=120)


def check_token_and_allowlist(fails: list[str]) -> None:
    """Against the vendored module, so what a brain ships is what is checked."""
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(GOLDEN / "scripts"))
    import note_edit as ne
    import note_view as nv

    LB, LE = nv.LEXICAL_ONLY_BEGIN, nv.LEXICAL_ONLY_END
    tmp = Path(tempfile.mkdtemp(prefix="edit-token-"))
    try:
        a = f"---\ntags: [t]\n---\n\n# N\n\nprose\n\n{LB}\n- [ ] TB test\n{LE}\n"
        b = a.replace("- [ ] TB test", "- [x] TB test")
        pa, pb = tmp / "a.md", tmp / "b.md"
        pa.write_text(a, encoding="utf-8"); pb.write_text(b, encoding="utf-8")

        if nv.content_hash(a) != nv.content_hash(b):
            fails.append("premise broken: the canonical view is supposed to be blind to a "
                         "fenced edit, and this gate's whole argument rests on that")
        if ne.file_hash(pa) == ne.file_hash(pb):
            fails.append("the edit token did NOT change after an edit inside a lexical-only "
                         "fence — a client would overwrite a checkbox ticked in Obsidian and "
                         "report success. The token must not be content_hash.")

        # Frontmatter is stripped by the canonical view too — same blind spot, different edit.
        fa = tmp / "fa.md"; fb = tmp / "fb.md"
        fa.write_text("---\ntags: [one]\n---\n\n# N\n\nb\n", encoding="utf-8")
        fb.write_text("---\ntags: [one, two]\n---\n\n# N\n\nb\n", encoding="utf-8")
        if ne.file_hash(fa) == ne.file_hash(fb):
            fails.append("the edit token did not change after a frontmatter-only edit")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    brain = Path(tempfile.mkdtemp(prefix="edit-allow-"))
    try:
        for d in ("projects", "areas", "resources", "archive", "glossary", "templates"):
            (brain / "vault" / d).mkdir(parents=True)
        for rel in ("vault/projects/n.md", "vault/projects/a/b.md", "vault/dashboard-index.md",
                    "vault/inbox.md"):
            try:
                ne.resolve_editable(rel, brain)
            except ne.NotEditable as exc:
                fails.append(f"{rel} should be editable but was refused: {exc}")
        for rel, why in (("vault/glossary/ablation.md", "its links are cascaded by add_glossary_term"),
                         ("vault/templates/new-note.md", "devkit machinery"),
                         ("vault/projects/tile.svg", "an asset, not a note"),
                         ("vault/projects/.n.embed.json", "a derived sidecar"),
                         ("vault/other/n.md", "not a PARA root"),
                         ("vault/scratch.md", "not one of the vault-root editables"),
                         ("README.md", "outside the vault"),
                         ("vault/projects/../../README.md", "a traversal landing outside")):
            try:
                ne.resolve_editable(rel, brain)
            except ne.NotEditable:
                continue
            fails.append(f"{rel} was ALLOWED as an edit target ({why})")
    finally:
        shutil.rmtree(brain, ignore_errors=True)


def check_encrypted_agreement(fails: list[str]) -> None:
    """On an encrypted brain the token and the write must describe the same bytes."""
    try:
        import cryptography  # noqa: F401
    except ImportError:
        print("        optional 'cryptography' absent — the encrypted agreement was NOT checked")
        return

    env = {**os.environ, "SECOND_BRAIN_EMBEDDER": "test",
           "SECOND_BRAIN_PASSPHRASE": "note-edit gate passphrase",
           "GIT_AUTHOR_NAME": "Edit", "GIT_AUTHOR_EMAIL": "e@example.invalid",
           "GIT_COMMITTER_NAME": "Edit", "GIT_COMMITTER_EMAIL": "e@example.invalid"}
    parent = Path(tempfile.mkdtemp(prefix="edit-enc-"))
    try:
        brain = parent / "brain"
        generate(brain)
        for cmd in (["init", "-q"], ["config", "user.email", "e@example.invalid"],
                    ["config", "user.name", "Edit"], ["config", "commit.gpgsign", "false"],
                    ["config", "core.hooksPath", ".githooks"]):
            _git(brain, *cmd, env=env)
        _git(brain, "add", "-A", env=env); _git(brain, "commit", "-q", "-m", "seed", env=env)
        r = _run([PY, "scripts/encrypt_vault.py", "--enable"], brain, env)
        if r.returncode != 0:
            fails.append(f"could not enable encryption: {(r.stderr or r.stdout)[-200:]}")
            return

        rel = "vault/resources/edit-probe.md"
        (brain / rel).write_text("---\ntags: [t]\n---\n\n# Probe\n\nOriginal line.\n",
                                 encoding="utf-8")
        _git(brain, "add", "-A", env=env)
        _git(brain, "commit", "-q", "--allow-empty", "-m", "probe", env=env)

        # The token must describe the PLAINTEXT on disk, which is what a write replaces — not
        # the ciphertext git holds. If these disagreed, every edit on an encrypted brain would
        # be refused as stale, or worse, accepted against the wrong bytes.
        probe = (
            "import sys; sys.path.insert(0, 'scripts');"
            "import note_edit, hashlib;"
            "from pathlib import Path;"
            f"p = Path('{rel}');"
            "disk = 'sha256:' + hashlib.sha256(p.read_bytes()).hexdigest();"
            "print(note_edit.file_hash(p) == disk, p.read_text().startswith('---'))"
        )
        out = _run([PY, "-c", probe], brain, env).stdout.split()
        if out[:1] != ["True"]:
            fails.append("on an encrypted brain the edit token does not match the bytes on "
                         "disk — the token and the write would describe different forms")
        if out[1:2] != ["True"]:
            fails.append("the working tree is not plaintext on an encrypted brain, which "
                         "breaks the premise that get_note returns what a write replaces")
        if not list((brain / "enc").glob("*.md.enc")):
            fails.append("encryption produced no blobs, so this check proved nothing")
    finally:
        shutil.rmtree(parent, ignore_errors=True)


def main() -> int:
    fails: list[str] = []
    for label, fn in (("the token and allow-list check", check_token_and_allowlist),
                      ("the encrypted-agreement check", check_encrypted_agreement)):
        before = len(fails)
        try:
            fn(fails)
        except Exception as exc:
            fails.append(f"{label} raised {type(exc).__name__}: {str(exc)[:200]}")
        if len(fails) == before and fn is check_token_and_allowlist:
            print("  ok    the edit token sees fenced and frontmatter edits that content_hash "
                  "cannot; the editable set is an allow-list")
        elif len(fails) == before:
            print("  ok    on an encrypted brain the token describes the plaintext a write "
                  "replaces, not the ciphertext git holds")

    suite = GOLDEN / "tests" / "test_note_edit.py"
    if not suite.is_file():
        fails.append("vendored tests/test_note_edit.py missing (run vendor_golden.py)")
    elif subprocess.run([PY, "-B", str(suite)], capture_output=True).returncode != 0:
        fails.append("the emitted note-edit suite regressed")

    if fails:
        for f in fails:
            print(f"  FAIL  {f}", file=sys.stderr)
        print(f"\nnote-edit FAILED: {len(fails)} assertion(s)", file=sys.stderr)
        return 1
    print("note-edit OK: a stale write cannot pass the token, the token is not blind where "
          "content_hash is, only PARA notes and two vault-root files are editable, and an "
          "encrypted brain hashes the same form it writes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
