#!/usr/bin/env python3
"""Gate 14 — the emitted PDF ingestion suite is CORRECT (task #7).

Byte-diffing (gates 2/5) proves the PDF modules were *copied* into a brain; it does not
prove they still WORK. This runs the vendored PDF regression suites against the vendored
scripts — the exact bytes ``build_template.py`` emits — so a break in chunking, extraction,
the sidecar format, the bolt-on cache load, passage search, the ingest engine, or the MCP
tools fails the build.

The suites are written to tolerate the optional ``pypdf``/``mcp`` deps: the pure paths
(chunker, cache, search, selection) always run, and the extraction/ingest/MCP paths skip
cleanly when the dep is absent — as in this CI. So the gate is hermetic: stdlib + sqlite-vec
+ the vendored tree, no pypdf / mcp / Ollama / git. It also covers the ``[pdf]`` config
parameters the config-matrix gate (10) deliberately scopes out.

    python3 tools/check_pdf.py

This is a devkit tool; it is never emitted into a brain.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN = REPO_ROOT / "tests" / "golden"
PY = sys.executable

SUITES = [
    "test_chunker.py",      # M1 — text -> overlapping page-tagged chunks
    "test_pdf_extract.py",  # M1 — pypdf extraction + page map (skips w/o pypdf)
    "test_embed_pdf.py",    # M2 — chunk-list sidecar, byte-exact fixture
    "test_pdf_cache.py",    # M3 — bolt-on tables + loader, note path unchanged
    "test_pdf_search.py",   # M4 — chunk-grain passage search + shaping
    "test_add_pdf.py",      # M5 — selection + end-to-end ingest (ingest skips w/o pypdf)
    "test_mcp_pdf.py",      # M6 — MCP tools (skips w/o mcp/pypdf)
    "test_doctor_pdf.py",   # M6 — doctor PDF parity (no mis-flag; stale check w/ pypdf)
    "test_pdf_gitignore.py",  # #39 — an ingested PDF is ignored, not merely untracked
]


def main() -> int:
    tests_dir = GOLDEN / "tests"
    missing = [s for s in SUITES if not (tests_dir / s).is_file()]
    if missing:
        print(f"FAIL: vendored PDF suites missing {missing} (run tools/vendor_golden.py)",
              file=sys.stderr)
        return 1

    for suite in SUITES:
        # -B: never write .pyc INTO tests/golden — an unclassified __pycache__ there would
        # fail the very next partition check (gate 1), the same trap gate 13 documents.
        r = subprocess.run([PY, "-B", str(tests_dir / suite)], capture_output=True, text=True)
        if r.returncode != 0:
            sys.stdout.write(r.stdout)
            sys.stderr.write(r.stderr)
            print(f"FAIL: the emitted PDF suite regressed: {suite}", file=sys.stderr)
            return 1

    print(f"pdf OK: {len(SUITES)} emitted PDF suite(s) green "
          f"(extraction/ingest/MCP tests skip cleanly without pypdf/mcp)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
