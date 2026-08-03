#!/usr/bin/env python3
"""Non-destructively upgrade an existing brain's tooling from this devkit (G4).

``create_second_brain.py`` can only *create* a brain (it refuses a non-empty target), so once a
brain is generated and filled with notes there is no supported way to pull in later
devkit improvements — new scripts, bug fixes, WAL, the MCP server — short of delete +
regenerate, which destroys the vault and git history. This closes that gap.

What it does:
  • Re-emits the **tooling** a brain ships — ``scripts/``, ``skill/``, ``.githooks/``,
    ``requirements*.txt``, ``tests/``, ``seeds/`` … — from the tracked ``template/``
    tree, picking up whatever the manifest now emits (so a new file like
    ``scripts/mcp_server.py`` is added automatically).
  • **``README.md`` and ``CLAUDE.md`` are managed blocks, not wholesale copies (tasks
    #9, #40).** Each is a hybrid: the devkit owns the region between its ``<!-- BEGIN/END
    generated … -->`` markers, the user owns everything outside. So they are **spliced** —
    the fresh devkit body replaces the marked block while the user's preamble/appendix are
    preserved byte-for-byte. Only one marker (malformed) or several regions → SKIP.
    See docs/readme-managed-block.md.
  • **A brain older than the markers (task #40).** Its ``CLAUDE.md`` has no markers at all,
    and the README's answer to that — leave it alone forever — is wrong here: ``CLAUDE.md``
    is the *operating instructions an agent follows*, and the one reader who could notice
    it had gone stale is the one that cannot, since the agent has no other copy to compare
    against. So this reports it loudly and offers ``--adopt``, which writes the devkit block
    **above** the existing file and keeps that file verbatim below. Still opt-in: a
    personalised ``CLAUDE.md`` is indistinguishable from an untouched one, so the tool asks
    rather than guesses. A marker-less README stays SKIP — a human can see a stale README.
  • **Never touches your data:** ``vault/`` (notes), ``data/`` (cache), ``config/``
    (backend choice), or your space outside the managed markers — and never rewrites
    history. **One named exception** (``VAULT_OWNED``): ``vault/templates/new-note.md`` is
    devkit-owned in everything but location — it sits in the vault only because that is
    where Obsidian's Templates plugin can reach it, and it is not a note (``templates/``
    is not a PARA root, so it is never embedded or searched). It also carries the note
    gate CI keeps in sync with ``CLAUDE.md``, so freezing it let an upgraded brain violate
    a build-time invariant. Named as one path rather than by relaxing the ``vault/`` rule,
    so the promise stays auditable.
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

# Reuse the emitted brain's marked-block splice helper (task #10) rather than
# duplicating the logic — the same primitive install_skill.py --nudge uses.
# Importing from the tracked template/ tree must not drop __pycache__/*.pyc into it
# (that would pollute the byte-exact template — and get copied into a brain).
sys.dont_write_bytecode = True
sys.path.insert(0, str(TEMPLATE / "scripts"))
try:
    from marked_block import MarkedBlockError, has_block, splice_block
except ModuleNotFoundError:  # template/ not built yet
    raise SystemExit(
        "update_brain: cannot import marked_block from template/scripts — "
        "run build_template.py first."
    )

# User territory — re-emitting these could clobber notes, the cache, or the chosen
# backend. Never written. (vault/ isn't in template/ anyway.)
PRESERVE_DIRS = ("vault/", "data/", "config/")
PRESERVE_FILES = ("GEMINI.md",)  # a symlink to CLAUDE.md; it follows whatever that file does

# Managed (hybrid) files: the devkit owns the block between these markers and regenerates
# it; the user owns everything outside. Instead of re-emitting the file wholesale (which
# clobbers the user's own preamble/appendix), we splice the fresh devkit body into the
# brain's *existing* markers. The strings must match the markers shipped in template/
# byte-for-byte — they are identical across both files on purpose, so a brain owner learns
# one convention rather than two.
BEGIN = ("<!-- BEGIN generated by second-brain-devkit: do not edit inside; "
         "regenerated by update_brain.py. Put your own notes outside these markers. -->")
END = "<!-- END generated by second-brain-devkit -->"

README = "README.md"
CLAUDE = "CLAUDE.md"

# Both files are spliced identically when marked, and both are **adoptable** when not.
#
# Adoption was first built for CLAUDE.md alone (#40), on the reasoning that a stale README
# is at least *visible* to the human reading it. Dogfooding killed that distinction: the
# real brain's README was missing an entire feature section, and **absence is not visible
# to a reader either** — you cannot see prose that was never written. A marker-less file of
# either kind means the same thing in practice: devkit updates stop arriving, silently.
#
# Adoption never acts on its own. `--adopt` is the consent, because a marker-less file has
# two indistinguishable causes — the brain predates managed blocks, or the user deliberately
# deleted the markers to take ownership. Someone in the second camp simply never passes the
# flag; the report says so in both directions rather than guessing which they are.
ADOPTABLE = (CLAUDE, README)
MANAGED = (README, CLAUDE)


# The ONE exception to "never write into vault/" — dest (brain-relative) → src (template-relative).
#
# `vault/templates/new-note.md` is devkit-owned in everything but location. It has to live
# inside the vault because that is the only place Obsidian's Templates plugin can insert from;
# moving it out would break the editor workflow it exists for. But it is also **not** a note —
# `templates/` is not a PARA root, so it is never embedded, never searched, never returned by
# `get_note`. And it carries the "what earns a note" gate that CI (gate 9) requires to match
# `CLAUDE.md` byte-for-byte, so leaving it frozen let an upgraded brain quietly violate a
# build-time invariant.
#
# Named as a single path rather than by lifting the `vault/` rule. The promise stays auditable —
# "this tool writes exactly one file inside your vault, and here it is" — instead of degrading
# to "it might write anywhere in there". Overwritten wholesale like any other emitted file: a
# user is not expected to customise it, and if they have, the dry run reports it CHANGED before
# anything is written, which is the same protection every other tooling file gets.
VAULT_OWNED = {"vault/templates/new-note.md": "seeds/templates/new-note.md"}


def _is_preserved(rel: str) -> bool:
    if rel in VAULT_OWNED:
        return False
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


def _managed_body(template_text: str) -> str:
    """The devkit body between the managed-block markers, newline-trimmed."""
    after_begin = template_text.split(BEGIN, 1)[1]
    return after_begin.split(END, 1)[0].strip("\n")


def _adopted(template_text: str, existing: str) -> str:
    """A marker-less file, brought under management **without losing a byte** of it.

    The fresh devkit block goes **first** and the user's existing file is kept verbatim
    below it. Order matters: this is an instruction file, and an agent reads top-down, so
    the current directives must precede the copy they supersede. A notice explains the
    duplication, because the honest description of this state is "your old copy is still
    here, prune what you don't want" — not a silent merge that pretends to have understood
    which lines were yours.
    """
    notice = (
        "<!-- The block above was adopted from second-brain-devkit by `update_brain.py --adopt`;\n"
        "     it is now regenerated on every update. Everything BELOW this notice is your\n"
        "     previous copy of this file, kept verbatim and never touched again — it very likely\n"
        "     duplicates the block above, so prune whatever you no longer want. -->"
    )
    return f"{BEGIN}\n{_managed_body(template_text)}\n{END}\n\n{notice}\n\n{existing.lstrip(chr(10))}"


def _managed_target(rel: str, brain: Path, template_text: str,
                    adopt: bool = False) -> tuple[str, str | None, str]:
    """Decide how a managed file should change, preserving the user's space outside the markers.

    Returns ``(verdict, text, reason)``:
      ``new``     — brain lacks the file; ship the template whole (``text`` set).
      ``changed`` — splicing (or adopting) changes it (``text`` = the result).
      ``same``    — already up to date (``text`` None).
      ``skip``    — user-owned or malformed; leave it (``text`` None, ``reason`` set).
    """
    if not has_block(template_text, BEGIN, END):
        raise SystemExit(f"update_brain: template {rel} lacks the managed-block markers "
                         "— rebuild template/ (build_template.py).")
    dst = brain / rel
    if not dst.exists():
        return ("new", template_text, "")  # no file yet → the whole template, markers and all
    existing = dst.read_text()
    # v1 manages exactly one region; refuse to guess a boundary among duplicates.
    if existing.count(BEGIN) > 1 or existing.count(END) > 1:
        return ("skip", None, "multiple devkit markers — left untouched (v1 manages one region)")
    try:
        present = has_block(existing, BEGIN, END)
    except MarkedBlockError:
        return ("skip", None, "one marker without its partner — left untouched")
    if not present:
        if rel not in ADOPTABLE:
            return ("skip", None, f"no devkit markers — {rel} is user-owned, left untouched")
        if not adopt:
            return ("skip", None,
                    "no devkit markers — user-owned, left untouched. Either it predates managed "
                    "blocks or you removed them; both mean devkit updates (this one and every "
                    "future one) will NOT reach it. Re-run with --adopt to bring it under "
                    "management — your current file is kept verbatim below the block — or "
                    "ignore this if you meant to own the file outright")
        return ("changed", _adopted(template_text, existing), "")
    spliced = splice_block(existing, BEGIN, END, _managed_body(template_text))
    if spliced == existing:
        return ("same", None, "")
    return ("changed", spliced, "")


def plan(brain: Path, adopt: bool = False) -> tuple[list[str], list[str], list[tuple[str, str]]]:
    """Return (new, changed, skipped) — tooling paths (rel), skipping preserved files.

    ``skipped`` carries ``(rel, reason)`` for files intentionally left alone (a user-owned
    or malformed managed file); preserved data files are not listed here.
    """
    if not TEMPLATE.is_dir():
        raise SystemExit(f"update_brain: no template at {TEMPLATE} — run build_template.py")
    new: list[str] = []
    changed: list[str] = []
    skipped: list[tuple[str, str]] = []
    for src in sorted(TEMPLATE.rglob("*")):
        if src.is_dir() and not src.is_symlink():
            continue
        rel = src.relative_to(TEMPLATE).as_posix()
        # Never emit Python bytecode caches — they are machine/version-specific build artifacts
        # that can leak into template/ if a tool imports from it, and must never reach a brain.
        if "__pycache__/" in rel or rel.endswith(".pyc"):
            continue
        if _is_preserved(rel):
            continue
        if rel in MANAGED:
            verdict, _, reason = _managed_target(rel, brain, src.read_text(), adopt)
            if verdict == "skip":
                skipped.append((rel, reason))
            elif verdict in ("new", "changed"):
                (new if verdict == "new" else changed).append(rel)
            continue
        verdict = _differs(src, brain / rel)
        if verdict == "new":
            new.append(rel)
        elif verdict == "changed":
            changed.append(rel)

    # The vault-owned exception: sourced from a DIFFERENT template path than where it lands
    # (the vault is generated from seeds/), so it cannot come out of the walk above.
    for dest, source in VAULT_OWNED.items():
        src = TEMPLATE / source
        if not src.is_file():
            continue
        verdict = _differs(src, brain / dest)
        if verdict == "new":
            new.append(dest)
        elif verdict == "changed":
            changed.append(dest)
    return new, changed, skipped


def update_brain(target, *, apply: bool = False, adopt: bool = False) -> int:
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

    new, changed, skipped = plan(brain, adopt)
    devkit_sha = _git(REPO_ROOT, "rev-parse", "--short", "HEAD", check=False).stdout.strip()

    print(f"update_brain: {brain}")
    if devkit_sha:
        print(f"  from devkit {devkit_sha}")
    print()
    for rel in new:
        print(f"  NEW      {rel}")
    for rel in changed:
        print(f"  CHANGED  {rel}")
    for rel, reason in skipped:
        print(f"  SKIP     {rel} — {reason}")
    print("\npreserved (never touched): vault/ (except the devkit-owned note template), "
          "data/, config/,\n   your space outside the CLAUDE.md/README.md markers, git history")

    # Migration notice (#30). These files define the *embed input* — what a note's vector is
    # computed over. If one of them changes, every existing vector was produced by the OLD
    # definition, but this tool never re-embeds (vault/ + data/ are preserved). Search still
    # works, so the staleness is silent. Tell the user to re-embed once; doctor --repair does it.
    EMBED_INPUT_FILES = {"scripts/note_view.py", "scripts/embedder.py"}
    view_changed = sorted(EMBED_INPUT_FILES.intersection(new + changed))
    if view_changed:
        # Deliberately says MAY, not WILL: some changes to these files alter the embedding output
        # (a new canonical view, a new model) and make every vector stale; others don't (a timeout,
        # an error message). update_brain can't tell which — so it points at doctor, which recomputes
        # each note's content_hash and reports the truth. Overclaiming "stale" here would cry wolf.
        print(f"\n⚠  NOTE — this update touches how notes embed ({', '.join(view_changed)}).")
        print("   IF it changed the embedding itself (a new view or model), your existing vectors")
        print("   are now stale — search still works, but they no longer match. To be sure, run:")
        print("       python3 scripts/doctor.py           # reports 'stale embedding' if so")
        print("       python3 scripts/doctor.py --repair  # re-embeds only what actually changed")

    # An adoptable file skipped for want of markers is NOT "up to date" — the tooling is
    # current and the directives are not, which is exactly the #40 failure. Saying "up to
    # date" here would restore the silence this feature exists to end.
    unmanaged = [rel for rel, _ in skipped if rel in ADOPTABLE]
    if not (new or changed):
        if unmanaged:
            print(f"\n⚠  tooling is up to date, but {', '.join(unmanaged)} is NOT under "
                  "management —\n   this brain will keep missing devkit updates to "
                  f"{'those files' if len(unmanaged) > 1 else 'that file'} until you run:"
                  "\n       python3 tools/update_brain.py <brain> --apply --adopt"
                  "\n   (ignore this if you meant to own "
                  f"{'them' if len(unmanaged) > 1 else 'it'} outright)")
            return 0
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
        if rel in MANAGED:
            # Splice the fresh devkit body into the brain's existing markers,
            # keeping the user's preamble/appendix byte-for-byte.
            _, text, _ = _managed_target(rel, brain, (TEMPLATE / rel).read_text(), adopt)
            (brain / rel).write_text(text)
        elif rel in VAULT_OWNED:
            _write(TEMPLATE / VAULT_OWNED[rel], brain / rel)
        else:
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
    ap.add_argument("--adopt", action="store_true",
                    help="bring a marker-less CLAUDE.md under management: the devkit block is "
                         "written above your existing file, which is kept verbatim below it")
    args = ap.parse_args(argv)
    return update_brain(args.target, apply=args.apply, adopt=args.adopt)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
