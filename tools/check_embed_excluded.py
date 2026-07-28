#!/usr/bin/env python3
"""Gate 15 — the emitted no-embed (embed-excluded) block is CORRECT (task #39).

Byte-diffing (gates 2/5) proves ``note_view.py`` and ``marked_block.py`` were *copied*
into a brain; it does not prove the canonical view still excludes what it must. This runs
the vendored regression suite against the vendored bytes — the exact bytes
``build_template.py`` emits — then asserts three properties directly, because each is a
way the feature can rot silently rather than loudly:

1. **The block is excluded from the embed input.** The visible failure mode. Regressing
   it puts decorative art back in the vector.
2. **The block is excluded from the *content hash* too.** The invisible one. The
   embedding and the hash must read the *same* view or the two disagree: redrawing a
   diagram would re-embed the note and doctor would report a note that is not stale as
   stale, forever, on every scan.
3. **A note with no markers hashes exactly as it did before the feature.** The
   compatibility one. Any drift in the unmarked path restamps every content hash in every
   existing brain, so ``update_brain`` would silently mark the whole vault stale. Pinned
   against a literal expected digest so it cannot drift with the implementation.

Hermetic: stdlib + the vendored tree, no Ollama / mcp / git.

    python3 tools/check_embed_excluded.py

This is a devkit tool; it is never emitted into a brain.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN = REPO_ROOT / "tests" / "golden"
PY = sys.executable

# The canonical view of PLAIN_NOTE, and its sha256, written out by hand. This is the
# whole point of pinning: if the projection ever changes for a note that uses no markers,
# this literal is what refuses to move with it.
PLAIN_NOTE = "---\ntags: [t]\n---\n\n# N\n\nAn [[ablation]] of the corpus.\n"
PLAIN_VIEW = "# N\n\nAn ablation of the corpus.\n"


def _run(argv: list[str]) -> subprocess.CompletedProcess:
    # -B: never write .pyc. These run code inside tests/golden/, and a __pycache__ there
    # would be an unclassified file that fails the very next partition check (gate 1).
    return subprocess.run([argv[0], "-B", *argv[1:]], capture_output=True, text=True)


def main() -> int:
    suite = GOLDEN / "tests" / "test_note_view.py"
    if not suite.is_file():
        print("FAIL: vendored tests/test_note_view.py missing (run tools/vendor_golden.py)",
              file=sys.stderr)
        return 1

    # 1. Behavioral regression — the emitted projection must still pass its suite.
    r = _run([PY, str(suite)])
    if r.returncode != 0:
        sys.stdout.write(r.stdout)
        sys.stderr.write(r.stderr)
        print("FAIL: the emitted no-embed projection regressed", file=sys.stderr)
        return 1

    # 2. Assert the three properties independently of the suite, against the vendored
    #    module, so a deleted/weakened test cannot take the gate with it.
    #    This import happens IN THIS PROCESS, so the subprocess `-B` above cannot help:
    #    without this, importing note_view writes tests/golden/scripts/__pycache__/*.pyc —
    #    unclassified files that fail the very next partition check (gate 1).
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(GOLDEN / "scripts"))
    try:
        import note_view as nv
    except ImportError as exc:
        print(f"FAIL: cannot import the vendored note_view: {exc}", file=sys.stderr)
        return 1

    begin, end = nv.NO_EMBED_BEGIN, nv.NO_EMBED_END
    art_a = f"{PLAIN_NOTE}\n{begin}\n```\n┌──┐\n└──┘\n```\n{end}\n"
    art_b = f"{PLAIN_NOTE}\n{begin}\n```\n▓▓▓▓ a completely different diagram ▓▓▓▓\n```\n{end}\n"

    failures: list[str] = []
    if nv.canonical_body(art_a) != PLAIN_VIEW:
        failures.append(f"the no-embed block reached the embed input: "
                        f"{nv.canonical_body(art_a)!r} != {PLAIN_VIEW!r}")
    if nv.content_hash(art_a) != nv.content_hash(art_b):
        failures.append("editing the excluded art changed the content hash — redrawing a "
                        "diagram would re-embed the note and doctor would call it stale")
    if nv.canonical_body(PLAIN_NOTE) != PLAIN_VIEW:
        failures.append(f"the canonical view of an UNMARKED note drifted: "
                        f"{nv.canonical_body(PLAIN_NOTE)!r} != {PLAIN_VIEW!r}")
    expected = "sha256:" + hashlib.sha256(PLAIN_VIEW.encode("utf-8")).hexdigest()
    if nv.content_hash(PLAIN_NOTE) != expected:
        failures.append(f"the content hash of an UNMARKED note drifted ({expected} "
                        f"expected) — every existing brain would read as stale")

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1

    print("no-embed OK: emitted suite green; block excluded from both the embed input and "
          "the content hash; unmarked notes hash exactly as before")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
