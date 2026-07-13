#!/usr/bin/env python3
"""Scaffold a new glossary term note — the controlled-vocabulary layer (task #19).

Turns a term into `vault/glossary/<slug>.md`, scaffolded from the shared template
(`vault/templates/glossary-term.md`) so every card is structurally consistent — and thus
valid for the community *Spaced Repetition* Obsidian plugin — by construction.

    python3 scripts/glossary_new.py "retrieval substrates"

**Detect-and-instruct**, like `install_skill.py` / `doctor.py`: it refuses to overwrite. If the
term already exists it prints the existing path and exits non-zero; it never opens an editor and
never touches an existing file. The value is for a **human** hand-adding a term (consistency +
dedup + a plugin-valid shape); an AI can just copy the template.

Glossary notes live under `vault/glossary/`, which is **not** a PARA root, so the scaffolded note
is never embedded or returned by semantic search — see `vault/glossary/README.md`.

Pure stdlib; no dependency on the embedder/cache pipeline.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GLOSSARY_DIR = REPO_ROOT / "vault" / "glossary"
TEMPLATE = REPO_ROOT / "vault" / "templates" / "glossary-term.md"


def slugify(term: str) -> str:
    """Lowercase kebab-case slug: drop punctuation, collapse whitespace/underscores to '-'."""
    s = re.sub(r"[^\w\s-]", "", term.strip().lower())
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def scaffold(term: str) -> str:
    """Fill the term into the template's title + card front and strip the how-to comment."""
    text = TEMPLATE.read_text(encoding="utf-8")
    text = text.replace("# Term", f"# {term}", 1)
    text = text.replace("Term ? ", f"{term} ? ", 1)
    text = re.sub(r"\n?<!--.*?-->\n?", "", text, flags=re.DOTALL)  # drop the how-to block
    return text.rstrip() + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Scaffold a new glossary term note (PARA(G)).")
    ap.add_argument("term", help="the term, in natural form (e.g. \"retrieval substrates\")")
    args = ap.parse_args(argv)

    slug = slugify(args.term)
    if not slug:
        print(f"glossary_new: {args.term!r} has no usable characters for a filename",
              file=sys.stderr)
        return 2
    if not TEMPLATE.is_file():
        print(f"glossary_new: missing term template at "
              f"{TEMPLATE.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1

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
