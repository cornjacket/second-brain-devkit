#!/usr/bin/env python3
"""Assert autolink.py emits the frontmatter format Obsidian renders as graph edges.

Obsidian's link-type properties turn a ``[[wikilink]]`` into a real graph edge **only**
when it is a *quoted* string in a YAML list property (``- "[[note]]"``); a bare
``- [[note]]`` is invalid/ambiguous YAML and is silently **not** graphed. That is the
same regression class as the MCP ``outputSchema``/Claude-Desktop bug — an untested client
assumption that ships green (docs/auto-linking.md §5). This gate locks the emitted format
so a future edit to autolink's block can't quietly break the graph.

Hermetic: it imports the emitted ``apply_links`` (a pure text function) from the
post-clean ``template/`` tree — no Obsidian, no DB, no Ollama, no third-party deps (the
module's ``db``/sqlite-vec import is lazy). The quoted-wikilink requirement is asserted
**independently** here (this file's own regex), not by trusting autolink's own code, and a
negative self-test proves the assertion has teeth.

    python3 tools/check_autolink_format.py

Devkit tool; never emitted into a brain.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Importing the emitted module below must not drop __pycache__/*.pyc into the tracked
# template/ tree — those would leak into a generated brain and trip the structural diff.
sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parent.parent
EMITTED_SCRIPTS = REPO_ROOT / "template" / "scripts"
sys.path.insert(0, str(EMITTED_SCRIPTS))
import autolink  # noqa: E402  (emitted module; its db import is lazy → no sqlite-vec needed)

# Independent definition of an Obsidian-graphable link item: a quoted wikilink at the
# two-space YAML list indent. A bare ``- [[x]]`` (no quotes) must NOT match.
ITEM_RE = re.compile(r'^  - "\[\[[^"\[\]]+\]\]"$')


def graphable_links(note_text: str) -> list[str]:
    """Return the ``related_auto:`` link names, asserting the block is Obsidian-graphable.

    Raises ``AssertionError`` on any deviation from: a marked block **inside** the
    frontmatter, a ``related_auto:`` list key, and each item a **quoted** wikilink.
    """
    fm = autolink._split_frontmatter(note_text)
    assert fm is not None, "no frontmatter — related_auto: must live in frontmatter"
    inner = fm["inner"]
    assert autolink.BEGIN in inner and autolink.END in inner, \
        "related_auto: block is not inside the frontmatter"
    block = inner.split(autolink.BEGIN, 1)[1].split(autolink.END, 1)[0]
    lines = [ln for ln in block.splitlines() if ln.strip()]
    assert lines and lines[0] == "related_auto:", \
        f"block must start with the 'related_auto:' key, got {lines[:1]}"
    names = []
    for ln in lines[1:]:
        assert ITEM_RE.match(ln), \
            f"not a quoted wikilink list item (Obsidian won't graph it): {ln!r}"
        names.append(ln.split('"[[', 1)[1].split(']]"', 1)[0])
    return names


def main() -> int:
    # 1. positive — apply_links emits quoted wikilinks in a YAML list, inside frontmatter
    note = "---\ntags: [x]\n---\n\n# Title\n\nbody\n"
    out = autolink.apply_links(note, ["beta", "alpha"])
    names = graphable_links(out)
    assert names == ["alpha", "beta"], f"expected sorted [alpha, beta], got {names}"
    assert '  - "[[alpha]]"' in out, "wikilink must be double-quoted"
    assert "  - [[alpha]]" not in out, "wikilink must never be emitted bare"

    # 2. no-frontmatter note — synthesized frontmatter is still graphable
    assert graphable_links(autolink.apply_links("# Plain\n\nbody\n", ["gamma"])) == ["gamma"]

    # 3. negative — the check has teeth: a bare (unquoted) wikilink is rejected
    bad = (f"---\ntags: [x]\n{autolink.BEGIN}\nrelated_auto:\n"
           f"  - [[unquoted]]\n{autolink.END}\n---\nbody\n")
    try:
        graphable_links(bad)
    except AssertionError:
        pass
    else:
        print("FAIL: a bare (unquoted) wikilink was accepted — the check is toothless",
              file=sys.stderr)
        return 1

    print("autolink-format OK: related_auto: emits quoted wikilinks in a YAML list "
          "(the format Obsidian graphs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
