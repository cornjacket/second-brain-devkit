#!/usr/bin/env python3
"""Mirror a real brain into an encrypted twin, so a human can look at what the remote holds.

The hermetic gates prove the mechanism on throwaway fixtures. They cannot answer the
question the owner of a brain actually has — *"is MY content absent from MY git history?"* —
because a fixture contains nothing he would recognise. This builds a **twin**: the same
notes, encryption on, so every note has a plaintext original to compare against.

    ~/second-brain/            the real brain — plaintext, READ ONLY here, never modified
    ~/second-brain-encrypt/    the twin — same notes, encrypted, disposable

Not a CI gate. A person runs it, reads the output, and looks at the repository themselves;
``--verify`` does the mechanical half so that "I looked and it seemed fine" is not the whole
check.

    python3 tools/mirror_brain.py --setup     # scaffold the twin and encrypt it FIRST
    python3 tools/mirror_brain.py --mirror    # copy the real notes in, encrypted
    python3 tools/mirror_brain.py --verify    # the mechanical half of the comparison
    python3 tools/mirror_brain.py --teardown  # delete the twin's contents

**Order matters, and ``--setup`` enforces it.** Encryption governs future commits only, so a
note mirrored in *before* the twin is encrypted stays in its history as plaintext forever.
The twin is therefore encrypted while it is still empty of real content, which makes a much
stronger claim checkable afterwards: **no note has ever been committed in the clear, in any
commit, anywhere in this repository's history.**

The twin **does** get a remote, deliberately — a leak that only ever existed in a local
``.git`` is not the failure this feature guards against, and what a *server* ends up holding
is the thing being tested. The risk is bounded by disposability: a private repo, deleted when
the run is done, never anything's only copy.

Devkit tool. Never emitted into a brain.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO_ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

DEFAULT_REAL = Path.home() / "second-brain"
DEFAULT_TWIN = Path.home() / "second-brain-encrypt"
SKILL_LINK = Path.home() / ".claude" / "skills" / "second-brain"
NOTE_TEMPLATE = "vault/templates/new-note.md"


def git(root: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                          check=check, timeout=300)


def git_bytes(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=300).stdout


def brain_notes(root: Path) -> list[str]:
    """Every note in a brain's vault, brain-relative and sorted."""
    base = root / "vault"
    return sorted(p.relative_to(root).as_posix() for p in base.rglob("*.md")
                  if p.relative_to(root).as_posix() != NOTE_TEMPLATE
                  and not p.relative_to(root).as_posix().startswith("vault/templates/"))


def load_encrypt_vault(twin: Path):
    """Import the twin's OWN encrypt_vault, not the devkit's copy.

    The twin is the artefact under test; reading its modules from anywhere else would test
    a version it is not running.
    """
    sys.path.insert(0, str(twin / "scripts"))
    for stale in ("encrypt_vault", "features", "passphrase", "note_selection"):
        sys.modules.pop(stale, None)
    import encrypt_vault as ev
    return ev


# --------------------------------------------------------------------------- #
# setup
# --------------------------------------------------------------------------- #

def setup(real: Path, twin: Path, passphrase: str) -> int:
    if not (twin / ".git").exists():
        print(f"error: {twin} is not a git repository — clone your disposable remote there "
              f"first", file=sys.stderr)
        return 2
    if (twin / "enc" / "keyfile.json").exists():
        print(f"error: {twin} is already encrypted — use --mirror, or --teardown first",
              file=sys.stderr)
        return 2
    existing = [p for p in twin.iterdir() if p.name != ".git"]
    if existing:
        print(f"error: {twin} is not empty ({len(existing)} entries) — --setup wants a bare "
              f"clone so nothing predates encryption", file=sys.stderr)
        return 2

    from generate import generate
    staging = Path(tempfile.mkdtemp(prefix="twin-scaffold-"))
    try:
        generate(staging / "brain")
        for item in (staging / "brain").iterdir():
            dest = twin / item.name
            shutil.copytree(item, dest) if item.is_dir() else shutil.copy2(item, dest)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    # Remove the seeded notes BEFORE the first commit. They are public devkit boilerplate,
    # so committing them would leak nothing — but removing them buys a far stronger property
    # to verify later: no note, of any kind, has ever been committed in the clear here.
    for rel in brain_notes(twin):
        (twin / rel).unlink()

    git(twin, "config", "core.hooksPath", ".githooks")
    git(twin, "add", "-A")
    git(twin, "commit", "-q", "-m", "scaffold: an empty brain, before any note exists")

    env = {**os.environ, "SECOND_BRAIN_PASSPHRASE": passphrase}
    r = subprocess.run([sys.executable, "scripts/encrypt_vault.py", "--enable",
                        "--hint", "the devkit twin"], cwd=twin, env=env,
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"error: --enable failed:\n{r.stderr or r.stdout}", file=sys.stderr)
        return 1
    print(f"twin ready at {twin} — encrypted while empty, so nothing predates it")
    print(f"  next: python3 tools/mirror_brain.py --mirror")
    return 0


# --------------------------------------------------------------------------- #
# mirror
# --------------------------------------------------------------------------- #

def mirror(real: Path, twin: Path, passphrase: str, *, push: bool) -> int:
    if not (twin / "enc" / "keyfile.json").exists():
        print(f"error: {twin} is not encrypted yet — run --setup first, or every note you "
              f"copy in lands in its history as plaintext", file=sys.stderr)
        return 2

    notes = brain_notes(real)
    if not notes:
        print(f"error: no notes found under {real}/vault", file=sys.stderr)
        return 2

    copied = 0
    for rel in notes:
        dest = twin / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        body = (real / rel).read_bytes()
        if not dest.exists() or dest.read_bytes() != body:
            dest.write_bytes(body)
            copied += 1

    # Anything the real brain no longer has, the twin should not either — otherwise the two
    # drift and "the counts agree" stops meaning anything.
    live = set(notes)
    removed = 0
    for rel in brain_notes(twin):
        if rel not in live:
            (twin / rel).unlink()
            removed += 1

    env = {**os.environ, "SECOND_BRAIN_PASSPHRASE": passphrase}
    r = subprocess.run([sys.executable, "scripts/encrypt_vault.py", "--sync"],
                       cwd=twin, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"error: --sync failed:\n{r.stderr or r.stdout}", file=sys.stderr)
        return 1

    git(twin, "add", "-A", "--", "enc")
    if git(twin, "diff", "--cached", "--quiet").returncode != 0:
        git(twin, "commit", "-q", "-m", f"mirror: {len(notes)} note(s)")
        print(f"mirrored {len(notes)} note(s) ({copied} new/changed, {removed} removed)")
    else:
        print(f"mirrored {len(notes)} note(s) — nothing changed, no commit")

    if push:
        p = git(twin, "push", "origin", "HEAD")
        print("pushed" if p.returncode == 0 else f"push failed: {p.stderr.strip()[:200]}")
    return 0


# --------------------------------------------------------------------------- #
# verify
# --------------------------------------------------------------------------- #

def all_history_text(twin: Path) -> str:
    """Every object in the repository, decoded leniently. Ciphertext is binary."""
    objects = git_bytes(twin, "cat-file", "--batch-all-objects", "--batch")
    log = git_bytes(twin, "log", "--all", "--format=%H %s%n%b", "--name-only")
    return (objects + b"\n" + log).decode("utf-8", "replace")


def baseline_text(twin: Path) -> str:
    """Everything the twin already contained BEFORE any real note was mirrored in.

    Without this, the canary checks below are unusable. A brain's scaffold ships
    ``seeds/`` — which holds the very notes a real brain was seeded from — plus docs and
    e2e prompts using ordinary words like "corpus" and "ablation". A plain substring
    search over the object store therefore reports the scaffold's own vocabulary as a leak
    of the user's, and drowns a real finding in noise.

    ``--setup`` encrypts the twin while it is still empty, which is what makes a clean
    baseline definable at all: everything reachable from the pre-mirror commits predates
    every real note, so it cannot be evidence of one escaping.

    **The limit this leaves, stated rather than hidden:** a note whose filename or wording
    genuinely coincides with the scaffold's boilerplate cannot be distinguished from it.
    That text is the devkit's, not yours, so the trade is the right way round — but it is
    a blind spot, not a proof.
    """
    root = git(twin, "rev-list", "--max-parents=0", "HEAD").stdout.split()
    if not root:
        return ""
    # The scaffold commit and the migration that follows it, and nothing after.
    pre = git(twin, "rev-list", "--reverse", "HEAD").stdout.split()[:2]
    oids = []
    for ref in pre:
        oids += [line.split()[0] for line in
                 git(twin, "rev-list", "--objects", ref).stdout.splitlines() if line]
    if not oids:
        return ""
    proc = subprocess.run(["git", "cat-file", "--batch"], cwd=twin,
                          input="\n".join(sorted(set(oids))).encode(),
                          capture_output=True, timeout=300)
    log = git_bytes(twin, "log", "--format=%s%n%b", *pre[-1:])
    return (proc.stdout + b"\n" + log).decode("utf-8", "replace")


def verify(real: Path, twin: Path, passphrase: str) -> int:
    ev = load_encrypt_vault(twin)
    fails: list[str] = []

    def ok(msg): print(f"  ok    {msg}")

    def fail(msg): fails.append(msg); print(f"  FAIL  {msg}")

    keys = ev.keys_from_keyfile(ev.load_keyfile(twin / "enc" / "keyfile.json"), passphrase)

    # 1. Every real note is present in the twin and decrypts byte-identically.
    real_notes = brain_notes(real)
    mismatched, missing = [], []
    for rel in real_notes:
        blob = twin / "enc" / ev.blob_name(keys, rel)
        if not blob.exists():
            missing.append(rel)
            continue
        _, body = ev.decrypt_note(keys, blob.read_bytes())
        if body != (real / rel).read_bytes():
            mismatched.append(rel)
    if missing:
        fail(f"{len(missing)} note(s) have no blob in the twin: {missing[:5]}")
    elif mismatched:
        fail(f"{len(mismatched)} note(s) decrypt to something else: {mismatched[:5]}")
    else:
        ok(f"all {len(real_notes)} note(s) decrypt byte-identically from the twin")

    # 2. Counts agree — a twin missing half the brain could still pass check 1 vacuously
    #    if the notes it does have are correct.
    twin_blobs = list((twin / "enc").glob(f"*{ev.SUFFIX}"))
    if len(twin_blobs) != len(real_notes):
        fail(f"the twin has {len(twin_blobs)} blob(s) for {len(real_notes)} real note(s)")
    else:
        ok(f"note counts agree ({len(real_notes)})")

    # 3. Nothing but the note template is tracked under vault/.
    tracked = git(twin, "ls-files", "vault").stdout.split()
    if tracked != [NOTE_TEMPLATE]:
        fail(f"tracked under vault/ in the twin: {tracked} — expected only {NOTE_TEMPLATE}")
    else:
        ok("nothing under vault/ is tracked except the note template")

    # 4. THE POINT. No real filename, folder name, or line of content anywhere in the whole
    #    history — not just HEAD, because --setup guarantees nothing predates encryption.
    history = all_history_text(twin)
    baseline = baseline_text(twin)

    def leaked(term: str) -> bool:
        """In the history, and NOT already in the scaffold that predates every real note."""
        return bool(term) and term in history and term not in baseline

    stems = {Path(rel).stem for rel in real_notes}
    leaked_names = sorted(s for s in stems if leaked(s))
    if leaked_names:
        fail(f"{len(leaked_names)} note filename(s) appear in the twin's history: "
             f"{leaked_names[:5]}")
    else:
        ok(f"none of the {len(stems)} note filenames appear anywhere in the history "
           f"(beyond the scaffold's own vocabulary)")

    folders = {part for rel in real_notes for part in Path(rel).parent.parts
               if part not in ("vault",) + tuple(ev.CONTENT_ROOTS)}
    leaked_dirs = sorted(f for f in folders if leaked(f))
    if leaked_dirs:
        fail(f"subfolder name(s) appear in the twin's history: {leaked_dirs[:5]}")
    else:
        ok(f"none of the {len(folders)} subfolder names appear anywhere in the history")

    # Sample content: every note contributes its longest line, which is the one most likely
    # to be distinctive and the least likely to collide with boilerplate.
    leaked_lines = []
    for rel in real_notes:
        lines = [ln.strip() for ln in (real / rel).read_text(encoding="utf-8",
                                                             errors="replace").splitlines()]
        candidate = max((ln for ln in lines if len(ln) > 40), key=len, default="")
        if leaked(candidate):
            leaked_lines.append(rel)
    if leaked_lines:
        fail(f"{len(leaked_lines)} note(s) have content in the twin's history: "
             f"{leaked_lines[:5]}")
    else:
        ok(f"no sampled content line from {len(real_notes)} note(s) appears in the history")

    # 5. No plaintext note was EVER committed — the property --setup exists to buy.
    ever = git(twin, "log", "--all", "--name-only", "--format=", "--", "vault/**/*.md").stdout
    ever_paths = {p for p in ever.split() if p != NOTE_TEMPLATE}
    if ever_paths:
        fail(f"plaintext note(s) were committed at some point in this twin: "
             f"{sorted(ever_paths)[:5]} — its history is not clean, tear it down and redo "
             f"--setup before mirroring")
    else:
        ok("no plaintext note has ever been committed, in any commit")

    # 6. The real brain is untouched, and the global skill still points at it.
    if git(real, "status", "--porcelain").stdout.strip():
        fail(f"the REAL brain at {real} has uncommitted changes — this tool must never "
             f"write to it; check what changed before trusting anything above")
    else:
        ok(f"the real brain at {real} is clean (never written to)")

    if SKILL_LINK.is_symlink():
        target = Path(os.readlink(SKILL_LINK)).resolve()
        if real.resolve() not in target.parents and target != real.resolve():
            fail(f"the global second-brain skill points at {target}, not {real} — something "
                 f"repointed it (running install_skill.py from the twin does this)")
        else:
            ok("the global second-brain skill still points at the real brain")

    print()
    if fails:
        print(f"verify: {len(fails)} problem(s)")
        return 1
    print("verify: the twin holds your notes, and its history holds none of them")
    return 0


def teardown(twin: Path) -> int:
    for item in twin.iterdir():
        if item.name == ".git":
            continue
        shutil.rmtree(item) if item.is_dir() else item.unlink()
    print(f"emptied {twin} (its .git kept — delete the directory, and the remote, when done)")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--setup", action="store_true", help="scaffold the twin and encrypt it")
    g.add_argument("--mirror", action="store_true", help="copy the real notes in, encrypted")
    g.add_argument("--verify", action="store_true", help="check what the twin's history holds")
    g.add_argument("--teardown", action="store_true", help="empty the twin")
    ap.add_argument("--real", type=Path, default=DEFAULT_REAL)
    ap.add_argument("--twin", type=Path, default=DEFAULT_TWIN)
    ap.add_argument("--push", action="store_true", help="with --mirror: push to the remote")
    args = ap.parse_args(argv)

    real, twin = args.real.expanduser(), args.twin.expanduser()
    if args.teardown:
        return teardown(twin)
    if not real.is_dir():
        print(f"error: no brain at {real}", file=sys.stderr)
        return 2

    passphrase = os.environ.get("SECOND_BRAIN_PASSPHRASE", "")
    if not passphrase.strip():
        print("error: set SECOND_BRAIN_PASSPHRASE — the twin is disposable, so its "
              "passphrase can be anything you like", file=sys.stderr)
        return 2

    if args.setup:
        return setup(real, twin, passphrase)
    if args.mirror:
        return mirror(real, twin, passphrase, push=args.push)
    return verify(real, twin, passphrase)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
