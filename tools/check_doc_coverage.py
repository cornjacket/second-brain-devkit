#!/usr/bin/env python3
"""Gate 26 — a feature cannot ship while the README does not know it exists (task #58).

`README.md` spent four months describing roughly the mid-2026 product. Encryption at rest,
the `embed: false` opt-out, asset colocation, the filename-uniqueness hook, the `lexical-only`
fence, tag hygiene and the desktop e2e suite had all shipped and none of them appeared in it.

**The cause was structural, not carelessness.** Every feature since #45 shipped with a gate
that touches the *emitted* docs, so `template/README.md` stayed current. Nothing forced the
devkit's own README, so it drifted with no signal at all.

**A gate, not a generator.** Generating a feature list from `docs/` would make the README
machine-written, and its job is to *explain* — which needs judgment about what matters. The
failure here was forgetting, not bad writing. So this asserts that artifacts which already
exist agree, and leaves every word of prose alone. Same shape as gate 9 (two copies of the
note gate) and gate 23 (a capability missing from a tool description).

**The objection this design exists to answer.** A gate needs a source of truth, and a
hand-kept source can omit a topic just as easily as the README can — the gate then stays green
and catches nothing. So the classification below is **partitioned against the filesystem**, the
same property gate 1 gives `emit-manifest.toml`: every file in `docs/` must appear in exactly
one bucket, and adding a page fails this check until it is classified. The list cannot quietly
omit a page, because the walk finds it.

`internal` entries each carry a reason, because each one is a hole — the same discipline
`EXPECTED_UNENCRYPTED` uses in gate 18.

**The residual hole, stated rather than implied.** A feature shipped with **no** doc page and
**no** gate is invisible to this check and to every other one. That is not hypothetical: the
dashboard index shipped exactly that way and sat ungated until someone asked. Mechanism cannot
close it; the repo's rule that features ship with gates can, and this makes that rule enforced
rather than habitual for everything that does have a page.

    python3 tools/check_doc_coverage.py

Hermetic: stdlib only. Devkit tool, never emitted.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
README = REPO_ROOT / "README.md"

# Pages describing a capability a generated brain HAS. Each must be reachable from the README,
# because the README is where someone deciding whether to use this finds out what it does.
PRODUCT = {
    "asset-colocation", "auto-linking", "dashboard-index", "embed-budget-audit",
    "embed-excluded-block", "embed-opt-out", "encrypted-notes", "glossary", "lexical-fence",
    "mcp-server", "pdf-ingestion", "remote-backed-brains", "tag-hygiene",
}

# Pages that are NOT product surface. Every entry needs a reason: each one is a page the README
# is allowed to ignore, and an unjustified entry is how this list becomes a place to hide things.
INTERNAL = {
    "benchmark-corpus": "a devkit test dataset; never emitted into a brain",
    "big-brain": "roadmap for a shared brain — not built, so nothing to describe",
    "claude-desktop-workflow": "setup walkthrough for a feature the README covers via mcp-server",
    "desktop-e2e": "a self-verification suite a user runs, not a capability of the brain",
    "desktop-e2e-disposable-branch": "harness mechanics for the suite above",
    "desktop-e2e-pure-client": "one scenario inside the suite above",
    "embedding-separation": "design analysis of embedding levers; no shipped surface",
    "encrypted-commit-indexing": "a fixed bug inside encryption, which the README covers",
    "mcp-hardening": "non-functional hardening of the MCP server, not a separate capability",
    "note-moves": "a fixed bug — moving a note works, which is the absence of a feature",
    "partial-commit-index-poisoning": "a fixed bug with no user-facing surface",
    "plugin-packaging": "a route that was evaluated and DECLINED; nothing shipped",
    "quality-features": "an internal catalog of candidate retrieval work",
    "readme-managed-block": "how upgrades splice docs; mechanism, covered by the upgrade story",
    "retrieval-quality": "design notes behind hybrid search, which the README covers",
    "search-score-labeling": "a presentation fix inside search output",
    "source-map": "a map of the devkit's own files, for contributors",
    "test-corpus-clustering": "analysis of a devkit test dataset",
    "pdf-elicitation": "an interaction mode inside PDF ingestion, which the README covers",
}


def main() -> int:
    fails: list[str] = []
    pages = {p.stem for p in DOCS.glob("*.md")}

    # 1. PARTITION — the property that makes this gate answerable rather than decorative.
    unclassified = pages - PRODUCT - set(INTERNAL)
    for name in sorted(unclassified):
        fails.append(f"docs/{name}.md is not classified — add it to PRODUCT (and name it in "
                     f"README.md) or to INTERNAL with a reason. A classification that can "
                     f"silently omit a page would make this whole gate green and useless.")
    for name in sorted((PRODUCT | set(INTERNAL)) - pages):
        fails.append(f"docs/{name}.md is classified but does not exist — stale entry")
    both = PRODUCT & set(INTERNAL)
    for name in sorted(both):
        fails.append(f"docs/{name}.md is in BOTH buckets")

    # 2. Every internal exemption is justified.
    for name, why in sorted(INTERNAL.items()):
        if not why.strip():
            fails.append(f"docs/{name}.md is exempted with no reason given")

    # 3. Every product page is reachable from the README.
    readme = README.read_text(encoding="utf-8")
    low = readme.lower()
    for name in sorted(PRODUCT):
        slug, words = name, name.replace("-", " ")
        if f"docs/{slug}.md" in readme or slug in low or words in low:
            continue
        fails.append(f"docs/{slug}.md describes a shipped capability and README.md never "
                     f"mentions it — someone reading the front door cannot learn the brain "
                     f"does this")

    if fails:
        for f in fails:
            print(f"  FAIL  {f}", file=sys.stderr)
        print(f"\ndoc-coverage FAILED: {len(fails)} issue(s)", file=sys.stderr)
        return 1
    print(f"doc-coverage OK: all {len(pages)} docs pages classified; "
          f"{len(PRODUCT)} product capabilities each reachable from README.md; "
          f"{len(INTERNAL)} internal pages each exempted with a reason")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
