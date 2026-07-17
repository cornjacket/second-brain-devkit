#!/usr/bin/env python3
"""Gate 13 — the emitted tag-hygiene tooling is CORRECT and wires up (task #32).

Byte-diffing (gates 2/5) proves the tag-hygiene scripts were *copied* into a brain; it
does not prove the detector still WORKS. This runs the vendored regression suite against
the vendored scripts — the exact bytes ``build_template.py`` emits — so a break in the
near-miss / discrimination / overlap / format-lint passes or the applier fails the build.
Then it smoke-runs the emitted ``tag_lint.py --json`` against the vendored seed vault to
prove the CLI wires up in the emitted layout (imports resolve, ``note_view`` present,
valid JSON out).

The lint tool's *informational* posture (exit 0 on findings, never blocks a commit) lives
in ``tag_lint.py`` itself; this gate asserts the tool is **right**, which is a different
question and SHOULD fail when it regresses. Hermetic: stdlib + the vendored tree, no
Ollama / mcp / git.

    python3 tools/check_tag_lint.py

This is a devkit tool; it is never emitted into a brain.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN = REPO_ROOT / "tests" / "golden"
PY = sys.executable

_REPORT_KEYS = ("note_total", "tag_total", "near_miss", "near_universal",
                "singletons", "format_lint", "overlap")


def _run(argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True)


def main() -> int:
    suite = GOLDEN / "tests" / "test_tag_hygiene.py"
    lint = GOLDEN / "scripts" / "tag_lint.py"
    if not suite.is_file() or not lint.is_file():
        print("FAIL: vendored tag-hygiene files missing (run tools/vendor_golden.py)",
              file=sys.stderr)
        return 1

    # 1. Behavioral regression — the emitted detector/applier must still pass its suite.
    r = _run([PY, str(suite)])
    if r.returncode != 0:
        sys.stdout.write(r.stdout)
        sys.stderr.write(r.stderr)
        print("FAIL: the emitted tag-hygiene detector/applier regressed", file=sys.stderr)
        return 1

    # 2. CLI smoke — the emitted lint wires up in the brain layout and emits valid JSON.
    r = _run([PY, str(lint), "--json"])
    if r.returncode != 0:
        sys.stdout.write(r.stdout)
        sys.stderr.write(r.stderr)
        print("FAIL: emitted tag_lint.py did not run", file=sys.stderr)
        return 1
    try:
        report = json.loads(r.stdout)
    except json.JSONDecodeError as exc:
        print(f"FAIL: tag_lint --json did not emit valid JSON: {exc}", file=sys.stderr)
        return 1
    missing = [k for k in _REPORT_KEYS if k not in report]
    if missing:
        print(f"FAIL: tag_lint report missing keys: {missing}", file=sys.stderr)
        return 1

    print(f"tag-hygiene OK: emitted detector suite green; tag_lint --json scanned "
          f"{report['tag_total']} tags across {report['note_total']} notes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
