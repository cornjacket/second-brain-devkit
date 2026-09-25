#!/usr/bin/env python3
"""Gate 25 — the dashboard index is seeded once and never overwritten.

A brain has four ways to *relate* notes — folder, tag, embedding, wikilink — and none of them
reports **state**. Similarity is not status: nothing knows a checkbox is unticked or that a
project is waiting on someone else. `vault/dashboard-index.md` is that missing view.

Its delivery rule is unlike anything else the generator emits, which is why it needs a gate.
Every other file is either devkit-owned (overwritten on upgrade) or user-owned (never touched).
This one is **both, in sequence**: the devkit creates it once, and from that moment it is the
user's. The two failure modes are opposite and both silent:

* **Overwrite** — an upgrade clobbers live project status with the seed. The user loses hand-
  written state and nothing announces it; the file still exists and still looks plausible.
* **Never delivered** — treating it as user-owned means an existing brain never receives it at
  all, so the feature ships in the code and is absent from every brain that predates it.

So the assertions are: a fresh brain HAS it, an upgrade LEAVES a modified one alone, and a
brain missing it RECEIVES it. Also pinned: it sits at the vault ROOT, outside every PARA root,
so it is unembedded **by construction** rather than by an `embed: false` flag — a status table
is a bad vector that would compete against real notes, and the flag's parser deliberately fails
open, so a typo there would embed it.

Hermetic: stdlib + git. Devkit tool, never emitted.

    python3 tools/check_dashboard_index.py
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
PY = sys.executable
REL = "vault/dashboard-index.md"

sys.path.insert(0, str(TOOLS))
from generate import generate  # noqa: E402
import update_brain as ub  # noqa: E402


def _git(brain: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=brain, capture_output=True, text=True, timeout=120)


def _init(brain: Path) -> None:
    _git(brain, "init", "-q")
    _git(brain, "config", "user.email", "dash@example.invalid")
    _git(brain, "config", "user.name", "Dash")
    _git(brain, "config", "commit.gpgsign", "false")
    _git(brain, "add", "-A")
    _git(brain, "commit", "-q", "-m", "seed brain")


def _update(brain: Path, *extra: str) -> str:
    r = subprocess.run([PY, "-B", str(TOOLS / "update_brain.py"), str(brain), *extra],
                       capture_output=True, text=True, timeout=600)
    return r.stdout + r.stderr


def main() -> int:
    fails: list[str] = []

    # --- static: where it lives, and what claims it -------------------------------------
    seed = REPO_ROOT / "template" / "seeds" / "dashboard-index.md"
    if not seed.is_file():
        fails.append("template/seeds/dashboard-index.md is missing — nothing to seed")
    if REL not in ub.VAULT_SEEDED:
        fails.append(f"{REL} is not in update_brain.VAULT_SEEDED, so an existing brain never "
                     f"receives it")
    if REL in ub.VAULT_OWNED:
        fails.append(f"{REL} is in VAULT_OWNED — that means overwrite-on-upgrade, which would "
                     f"clobber the user's live project status on every update")
    # It must sit at the vault ROOT. One path segment after `vault/` means no PARA root can
    # contain it, which is what makes it unembeddable without relying on a flag.
    if Path(REL).parent.name != "vault":
        fails.append(f"{REL} is not at the vault root — inside a PARA root it would be embedded, "
                     f"and a status table is a bad vector that competes against real notes")

    parent = Path(tempfile.mkdtemp(prefix="dashboard-"))
    try:
        # --- a fresh brain has it -------------------------------------------------------
        brain = parent / "brain"
        generate(brain)
        path = brain / REL
        if not path.is_file():
            fails.append("a freshly generated brain has no dashboard index")
            raise SystemExit(0)
        if path.read_text(encoding="utf-8") != seed.read_text(encoding="utf-8"):
            fails.append("the seeded dashboard index does not match the template seed")
        _init(brain)

        # --- an upgrade must NOT touch a modified one -----------------------------------
        mine = "# My dashboard\n\n| effort | next action | blocked on |\n| --- | --- | --- |\n"
        path.write_text(mine, encoding="utf-8")
        _git(brain, "add", "-A")
        _git(brain, "commit", "-q", "-m", "my own status")
        out = _update(brain, "--apply")
        if path.read_text(encoding="utf-8") != mine:
            fails.append("an upgrade OVERWROTE the user's dashboard index — live project status "
                         "replaced by the seed, silently")
        if "dashboard-index" in out and "CHANGED" in out.split("dashboard-index")[0][-40:]:
            fails.append("the dashboard index was reported CHANGED — it must never appear in "
                         "the write list once it exists")

        # --- a brain that LACKS it receives it ------------------------------------------
        path.unlink()
        _git(brain, "add", "-A")
        _git(brain, "commit", "-q", "-m", "a brain predating the dashboard")
        _update(brain, "--apply")
        if not path.is_file():
            fails.append("an existing brain without a dashboard index did NOT receive one — the "
                         "feature would ship in the code and be absent from every older brain")
        elif path.read_text(encoding="utf-8") != seed.read_text(encoding="utf-8"):
            fails.append("the delivered dashboard index does not match the seed")

        # --- and it is not a note -------------------------------------------------------
        sys.path.insert(0, str(brain / "scripts"))
        sys.dont_write_bytecode = True
        import note_selection as ns
        if ns._is_note(REL, ns.PARA_ROOTS):
            fails.append(f"{REL} reads as an embeddable PARA note — it would be embedded and "
                         f"returned by search")
    finally:
        shutil.rmtree(parent, ignore_errors=True)

    if fails:
        for f in fails:
            print(f"  FAIL  {f}", file=sys.stderr)
        print(f"\ndashboard-index FAILED: {len(fails)} assertion(s)", file=sys.stderr)
        return 1
    print("dashboard-index OK: seeded into a fresh brain, delivered to one that lacks it, never "
          "overwritten once the user owns it, and unembeddable by location rather than by flag")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
