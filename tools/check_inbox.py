#!/usr/bin/env python3
"""Gate 28 — the inbox is seeded once, never overwritten, read first, and counted (task #64).

`vault/inbox.md` is where a brain's owner leaves messages for the next agent session. It has
the dashboard's delivery rule (``VAULT_SEEDED``: created if absent, the user's forever after),
so it has the dashboard's two silent failure modes — an upgrade that clobbers waiting messages,
and an existing brain that never receives the file. Gate 25 pins those for the dashboard; this
pins them for the inbox rather than trusting that a second entry in the same dict behaves.

Two more things only matter for the inbox:

* **An agent must be told to read it.** A message nobody reads is worse than no inbox — the
  owner believes it was delivered. So the emitted CLAUDE.md block must name the file and the
  read-first rule.
* **doctor counts what is waiting**, and the seed itself counts as empty — its explanatory
  bullets sit under other headings. A seed that reported "3 messages waiting" in every new
  brain would teach the owner to ignore the line.

Hermetic: stdlib + git. Devkit tool, never emitted.

    python3 tools/check_inbox.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS = REPO_ROOT / "tools"
PY = sys.executable
REL = "vault/inbox.md"

sys.path.insert(0, str(TOOLS))
from generate import generate  # noqa: E402
import update_brain as ub  # noqa: E402


def _git(brain: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=brain, capture_output=True, text=True, timeout=120)


def _init(brain: Path) -> None:
    _git(brain, "init", "-q")
    _git(brain, "config", "user.email", "inbox@example.invalid")
    _git(brain, "config", "user.name", "Inbox")
    _git(brain, "config", "commit.gpgsign", "false")
    _git(brain, "add", "-A")
    _git(brain, "commit", "-q", "-m", "seed brain")


def _commit(brain: Path, msg: str) -> None:
    _git(brain, "add", "-A")
    _git(brain, "commit", "-q", "-m", msg)


def _update(brain: Path) -> str:
    r = subprocess.run([PY, "-B", str(TOOLS / "update_brain.py"), str(brain), "--apply"],
                       capture_output=True, text=True, timeout=600)
    return r.stdout + r.stderr


def _doctor(brain: Path) -> str:
    r = subprocess.run([PY, "-B", "scripts/doctor.py"], cwd=brain, capture_output=True,
                       text=True, timeout=300)
    return r.stdout


def main() -> int:
    fails: list[str] = []

    seed = REPO_ROOT / "template" / "seeds" / "inbox.md"
    if not seed.is_file():
        fails.append("template/seeds/inbox.md is missing — nothing to seed")
    if REL not in ub.VAULT_SEEDED:
        fails.append(f"{REL} is not in update_brain.VAULT_SEEDED, so an existing brain never "
                     f"receives it")
    if REL in ub.VAULT_OWNED:
        fails.append(f"{REL} is in VAULT_OWNED — an upgrade would delete waiting messages")
    claude = (REPO_ROOT / "template" / "CLAUDE.md").read_text(encoding="utf-8")
    if REL not in claude or "Read\nit before anything else" not in claude:
        fails.append("the emitted CLAUDE.md does not tell an agent to read vault/inbox.md first "
                     "— messages would be delivered to nobody")

    parent = Path(tempfile.mkdtemp(prefix="inbox-"))
    try:
        brain = parent / "brain"
        generate(brain)
        path = brain / REL
        if not path.is_file():
            fails.append("a freshly generated brain has no inbox")
            raise SystemExit(0)
        if path.read_text(encoding="utf-8") != seed.read_text(encoding="utf-8"):
            fails.append("the seeded inbox does not match the template seed")
        _init(brain)

        out = _doctor(brain)
        if "inbox empty" not in out:
            fails.append("doctor does not report a fresh brain's inbox as empty — the seed's own "
                         "bullets are being counted as messages")

        # --- a waiting message is counted, and survives an upgrade ----------------------
        mine = path.read_text(encoding="utf-8") + "- 2026-10-14: file the article\n"
        path.write_text(mine, encoding="utf-8")
        _commit(brain, "leave a message")
        if "inbox: 1 message(s) waiting" not in _doctor(brain):
            fails.append("doctor did not count the one waiting message")
        out = _update(brain)
        if path.read_text(encoding="utf-8") != mine:
            fails.append("an upgrade OVERWROTE the inbox — a waiting message was lost, silently")
        if f"CHANGED  {REL}" in out:
            fails.append("the inbox was reported CHANGED — it must never be in the write list")

        # --- a brain that lacks it receives it ------------------------------------------
        path.unlink()
        _commit(brain, "a brain predating the inbox")
        _update(brain)
        if not path.is_file():
            fails.append("an existing brain without an inbox did NOT receive one")

        # --- not a note -----------------------------------------------------------------
        sys.path.insert(0, str(brain / "scripts"))
        sys.dont_write_bytecode = True
        import note_selection as ns
        if ns._is_note(REL, ns.PARA_ROOTS):
            fails.append(f"{REL} reads as an embeddable note — messages would be searchable")

        suite = REPO_ROOT / "tests" / "golden" / "tests" / "test_inbox.py"
        r = subprocess.run([PY, "-B", "-m", "unittest", "-q", str(suite)], capture_output=True,
                           text=True, timeout=300)
        if r.returncode != 0:
            fails.append(f"the vendored inbox suite failed:\n{r.stderr[-2000:]}")
    finally:
        shutil.rmtree(parent, ignore_errors=True)

    if fails:
        for f in fails:
            print(f"  FAIL  {f}", file=sys.stderr)
        print(f"\ninbox FAILED: {len(fails)} assertion(s)", file=sys.stderr)
        return 1
    print("inbox OK: seeded into a fresh brain, delivered to one that lacks it, never overwritten, "
          "unembeddable, read first per CLAUDE.md, and its waiting messages counted by doctor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
