#!/usr/bin/env python3
"""Gate 9 — the "what earns a note" rule must be identical in its two copies.

The editorial gate (*durable over transient; would I search for this in six months?; link
don't copy*) is **deliberately duplicated** — the one place this repo knowingly breaks
link-don't-copy — because the two audiences are **disjoint**:

  • an agent working *inside* a brain reads ``CLAUDE.md`` (always loaded) and can never
    call an MCP tool;
  • an assistant in **Claude Desktop** reads ``vault/templates/new-note.md`` via the MCP
    ``get_note_template()`` tool and can never see ``CLAUDE.md``.

One rule, two pipes that don't connect. The alternative — a pointer in ``CLAUDE.md`` saying
"go read the template" — trades an always-loaded rule for one the model must remember to
fetch, and forgetting is **silent**: the note still gets written, just unfiltered.

Duplication is only safe if it cannot drift, so this makes the drift *mechanical* rather
than a promise in a comment: the block between the markers must match in both files, or the
build fails. ``CLAUDE.md`` is canonical; ``--sync`` rewrites the template's copy from it.

Comparison is on **normalized** content (whitespace collapsed), not bytes, because the two
files carry the block differently: ``CLAUDE.md`` uses HTML-comment markers, while the
template's copy lives *inside* an existing HTML comment — where ``<!-- -->`` markers cannot
be nested (the first ``-->`` would close the comment early), so it uses plain-text markers.

    python3 tools/check_note_gate.py [--sync]

Devkit tool; never emitted. Runs against the emitted `template/` tree (what a user actually
gets) and the vendored golden.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# CLAUDE.md: HTML-comment markers (invisible when rendered, canonical copy).
MD_BEGIN, MD_END = "<!-- BEGIN what-earns-a-note -->", "<!-- END what-earns-a-note -->"
# new-note.md: plain-text markers — the block sits inside an HTML comment already.
TPL_BEGIN, TPL_END = "[what-earns-a-note: BEGIN]", "[what-earns-a-note: END]"


def _between(text: str, begin: str, end: str, where: Path) -> str:
    i, j = text.find(begin), text.find(end)
    if i == -1 or j == -1:
        raise SystemExit(f"FAIL {where}: missing the {'BEGIN' if i == -1 else 'END'} marker "
                         f"for the what-earns-a-note block")
    if j < i:
        raise SystemExit(f"FAIL {where}: END marker precedes BEGIN")
    return text[i + len(begin):j]


def _norm(block: str) -> str:
    """Collapse whitespace — the two copies are formatted for different hosts, so compare
    what they *say*, not how they are laid out."""
    return " ".join(block.split())


def check(tree: Path) -> list[str]:
    # seeds/ is the shipped baseline — `seed_vault.py` copies it into vault/ at creation, so
    # seeds/templates/new-note.md is the copy that actually reaches a user's brain (and the
    # structural-diff gate already proves vault/ matches it).
    claude, tpl = tree / "CLAUDE.md", tree / "seeds" / "templates" / "new-note.md"
    if not claude.exists() or not tpl.exists():
        return [f"{tree}: missing CLAUDE.md or seeds/templates/new-note.md"]

    canonical = _between(claude.read_text(encoding="utf-8"), MD_BEGIN, MD_END, claude)
    mirror = _between(tpl.read_text(encoding="utf-8"), TPL_BEGIN, TPL_END, tpl)
    if _norm(canonical) != _norm(mirror):
        return [f"{tree}: the what-earns-a-note gate has DRIFTED between CLAUDE.md (canonical) "
                f"and seeds/templates/new-note.md — an assistant in Claude Desktop would be "
                f"held to a different bar than one working in the repo. Run: "
                f"python3 tools/check_note_gate.py --sync"]
    if not _norm(canonical):
        return [f"{tree}: the what-earns-a-note block is EMPTY — the gate that keeps the brain's "
                f"signal-to-noise high would reach neither audience"]
    return []


def sync(tree: Path) -> None:
    """Rewrite the template's copy from CLAUDE.md (the canonical one)."""
    # seeds/ is the shipped baseline — `seed_vault.py` copies it into vault/ at creation, so
    # seeds/templates/new-note.md is the copy that actually reaches a user's brain (and the
    # structural-diff gate already proves vault/ matches it).
    claude, tpl = tree / "CLAUDE.md", tree / "seeds" / "templates" / "new-note.md"
    canonical = _between(claude.read_text(encoding="utf-8"), MD_BEGIN, MD_END, claude).strip("\n")
    text = tpl.read_text(encoding="utf-8")
    new = re.sub(re.escape(TPL_BEGIN) + r".*?" + re.escape(TPL_END),
                 f"{TPL_BEGIN}\n{canonical}\n{TPL_END}", text, flags=re.DOTALL)
    tpl.write_text(new, encoding="utf-8")
    print(f"synced {tpl} from {claude}")


def main() -> int:
    trees = [REPO_ROOT / "template", REPO_ROOT / "tests" / "golden"]
    if "--sync" in sys.argv:
        for t in trees:
            sync(t)
        print("NOTE: --sync edits the generated trees. Fix the LIVE golden "
              "(../second-brain-test/) too, then re-vendor — it is the prototyping surface.")
        return 0

    fails = [f for t in trees for f in check(t)]
    if fails:
        for f in fails:
            print(f"  FAIL  {f}")
        return 1
    print("note-gate OK: 'what earns a note' is identical in CLAUDE.md and the note template")
    print("  (deliberate duplication — disjoint audiences: in-repo agent vs Claude Desktop)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
