#!/usr/bin/env python3
"""Scaffold a new glossary term note — the controlled-vocabulary layer (task #19).

Turns a term into `vault/glossary/<slug>.md` from a **built-in** template, so every card is
structurally consistent — and thus valid for the community *Spaced Repetition* Obsidian
plugin — by construction.

    python3 scripts/glossary_new.py "retrieval substrates"

**Detect-and-instruct**, like `install_skill.py` / `doctor.py`: it refuses to overwrite. If
the term already exists it prints the existing path and exits non-zero; it never opens an
editor and never touches an existing file. The value is for a **human** hand-adding a term
(consistency + dedup + a plugin-valid shape); an AI can just write the note directly.

The term shape is **embedded here**, not a separate scaffold file — the tool owns the shape
it produces, so it is self-contained and works identically in a freshly created brain and in
one upgraded via `update_brain.py` (which re-emits tooling but never the vault). See the shape
documented for hand-authors in `vault/glossary/README.md`.

Glossary notes live under `vault/glossary/`, which is **not** a PARA root, so the scaffolded
note is never embedded or returned by semantic search — see `vault/glossary/README.md`.

Pure stdlib; no dependency on the embedder/cache pipeline.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GLOSSARY_DIR = REPO_ROOT / "vault" / "glossary"

# The shared term shape (flashcard-valid: a `Term ? <definition>` card + a #flashcards/ deck
# tag). `aliases:` is an empty placeholder — fill it with surface forms the MCP glossary
# lookup should also match (e.g. `aliases: [ablation study, ablations]`). Single source of
# truth for the shape; `vault/glossary/README.md` documents it for hand-authors.
_SCAFFOLD = """\
---
type: glossary
aliases: []
tags: [glossary]
---

# {term}

{term} ? A one-line definition — state the meaning atomically, one term, one idea.

#flashcards/glossary
"""


def slugify(term: str) -> str:
    """Lowercase kebab-case slug: drop punctuation, collapse whitespace/underscores to '-'."""
    s = re.sub(r"[^\w\s-]", "", term.strip().lower())
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def scaffold(term: str) -> str:
    """The term note text: the built-in shape with the term in the title and card front."""
    return _SCAFFOLD.format(term=term)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Scaffold a new glossary term note (PARA(G)).")
    ap.add_argument("term", help="the term, in natural form (e.g. \"retrieval substrates\")")
    args = ap.parse_args(argv)

    slug = slugify(args.term)
    if not slug:
        print(f"glossary_new: {args.term!r} has no usable characters for a filename",
              file=sys.stderr)
        return 2

    dest = GLOSSARY_DIR / f"{slug}.md"
    if dest.exists():
        print(f"glossary_new: term already exists → {dest.relative_to(REPO_ROOT)} "
              f"(edit it; not overwriting)", file=sys.stderr)
        return 1

    GLOSSARY_DIR.mkdir(parents=True, exist_ok=True)
    dest.write_text(scaffold(args.term), encoding="utf-8")
    print(f"  created {dest.relative_to(REPO_ROOT)}")
    print("  fill in the definition, then commit (glossary notes are not embedded — no sidecar).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
