#!/usr/bin/env python3
"""Gate 18 — every Markdown file in a brain is either encrypted content or machinery (#42).

Encryption protects *content*. Which files are content is not a list anybody maintains —
it follows one rule that is already implemented, in ``tools/update_brain.py``:

    If update_brain.py may overwrite it, it is machinery and stays plaintext.
    Otherwise it is content and gets encrypted.

An upgrade must never need a passphrase, and anything the devkit is free to overwrite is
by construction identical in every brain, so it says nothing about you.

**This gate is why the rule is a rule and not a hope.** It generates a brain, asks
``update_brain`` about every ``.md`` in it, and compares that verdict against what
``encrypt_vault`` would actually encrypt. Both directions are failures:

  * **preserved but not encrypted** — a file the devkit will never touch, therefore the
    user's own, that encryption does not cover. That is a leak: it goes to the remote in
    the clear. This is the direction that matters.
  * **encrypted but overwritable** — the devkit would rewrite a file encryption owns, so
    an upgrade would clobber ciphertext or demand a passphrase.

The point is that a *newly added* Markdown file cannot ship unclassified. Someone adding a
README-shaped file to the template, or a new note type to the vault, gets a build error
instead of a leak discovered by reading someone's repository.

Hermetic: generates a throwaway brain, stdlib only. Devkit tool, never emitted.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO_ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))
from generate import generate  # noqa: E402
import update_brain as ub  # noqa: E402

# Files that `update_brain` preserves but encryption deliberately does not cover. Every
# entry needs a reason, because each one is a hole in the rule above.
EXPECTED_UNENCRYPTED = {
    "GEMINI.md": "a symlink to CLAUDE.md — preserved only so the link is not clobbered; "
                 "its content IS CLAUDE.md, which is machinery. Encrypting it would "
                 "encrypt the devkit's own instructions.",
}


def classify(brain: Path) -> tuple[set[str], set[str]]:
    """(preserved, encrypted) — the two verdicts, as brain-relative paths."""
    sys.path.insert(0, str(brain / "scripts"))
    for stale in ("encrypt_vault", "features", "passphrase"):
        sys.modules.pop(stale, None)
    import encrypt_vault as ev

    markdown = {
        p.relative_to(brain).as_posix()
        for p in brain.rglob("*.md")
        if ".git" not in p.parts and "__pycache__" not in p.parts
    }
    preserved = {rel for rel in markdown if ub._is_preserved(rel)}
    encrypted = set(ev.content_notes(brain))
    return preserved, encrypted


def main() -> int:
    parent = Path(tempfile.mkdtemp(prefix="classification-"))
    brain = parent / "brain"
    try:
        generate(brain)
        preserved, encrypted = classify(brain)
    finally:
        shutil.rmtree(parent, ignore_errors=True)

    fails: list[str] = []

    leaked = preserved - encrypted - set(EXPECTED_UNENCRYPTED)
    for rel in sorted(leaked):
        fails.append(f"{rel}: update_brain PRESERVES it (so it is the user's, not the "
                     f"devkit's) but encryption does not cover it — it would be committed "
                     f"in the clear. Either add it to encrypt_vault's content set, or "
                     f"record it in EXPECTED_UNENCRYPTED with a reason.")

    clobbered = {rel for rel in encrypted if not ub._is_preserved(rel)}
    for rel in sorted(clobbered):
        fails.append(f"{rel}: encryption owns it but update_brain would OVERWRITE it — an "
                     f"upgrade would clobber ciphertext or demand a passphrase.")

    for rel, reason in sorted(EXPECTED_UNENCRYPTED.items()):
        if rel in encrypted:
            fails.append(f"{rel}: listed as deliberately unencrypted, but encryption now "
                         f"covers it — delete the stale exception.")
        elif rel not in preserved:
            fails.append(f"{rel}: listed as deliberately unencrypted, but update_brain no "
                         f"longer preserves it — the exception no longer applies "
                         f"({reason.split('—')[0].strip()}).")

    print(f"  ok    {len(encrypted)} content note(s) encrypted")
    print(f"  ok    {len(preserved - set(EXPECTED_UNENCRYPTED)) - len(leaked)} preserved "
          f"Markdown file(s) accounted for")
    for rel in sorted(EXPECTED_UNENCRYPTED):
        print(f"        deliberately unencrypted: {rel}")

    if fails:
        for f in fails:
            print(f"  FAIL  {f}")
        print("\nclassification FAILED: a Markdown file is not accounted for")
        return 1
    print("\nclassification OK: every Markdown file is content or machinery, by the rule")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
