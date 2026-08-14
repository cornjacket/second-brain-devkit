#!/usr/bin/env python3
"""Gate 17 — the encryption mechanism, and the commit path that must not go blind (#42).

Runs the two vendored suites against the vendored bytes, the same way ``check_pdf.py`` and
``check_tag_lint.py`` do: byte-diffing proves the modules were *copied*, this proves they
still *work*.

  ``tests/test_encrypt_vault.py``   keys, opaque names, envelope, verifier, tamper detection
  ``tests/test_note_selection.py``  which notes a commit picks up — in BOTH modes
  ``tests/test_encrypt_migration.py`` enable / clone / decrypt / disable, against real git

The second suite is the one that earns a gate. Three callers used to ask git ``diff
--cached -- '*.md'`` for their work list, which returns an **empty list** the moment the
vault is git-ignored — no error, no failure, and every caller silently does nothing. That
failure cannot be caught by a test asserting "it did not crash", so those tests assert a
specific note is *selected*, and this gate is what makes them run.

The ``cryptography`` dependency is optional, so the encrypted-mode cases skip cleanly when
it is absent — but a **skip is not a pass**, and a run where everything skipped would be a
green gate covering nothing. So the skip count is reported, and if the dependency is
present the gate requires the encrypted cases to have actually executed.

Hermetic: stdlib + the vendored tree. Devkit tool, never emitted.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN = REPO_ROOT / "tests" / "golden"
SUITES = ("tests.test_encrypt_vault", "tests.test_note_selection",
          "tests.test_encrypt_migration", "tests.test_notes_are_committed")


def have_crypto() -> bool:
    try:
        import cryptography  # noqa: F401
        return True
    except ImportError:
        return False


def run_suite(module: str) -> tuple[bool, str]:
    # -B: never write .pyc INTO tests/golden. These suites live inside the vendored tree,
    # and gate 1 partitions that tree by walking the filesystem — so a stray __pycache__
    # is an unclassified file that fails the build on the NEXT run, far from its cause.
    # The sibling gates (check_pdf, check_tag_lint) do the same, for the same reason.
    proc = subprocess.run([sys.executable, "-B", "-m", "unittest", module, "-v"],
                          cwd=GOLDEN, capture_output=True, text=True)
    return proc.returncode == 0, (proc.stderr or "") + (proc.stdout or "")


def check_dependency_is_optional() -> list[str]:
    """`cryptography` must never be imported at module level in an emitted brain.

    It is declared in `requirements-crypt.txt`, not `requirements.txt`, so the overwhelming
    majority of brains — every one that never turns encryption on — will not have it
    installed. A single module-level import anywhere in the emitted tree turns that into an
    ImportError on a path that has nothing to do with encryption: the pre-commit hook, or
    `doctor`, or `search_vault`. The feature would break brains that never asked for it.

    Static rather than behavioural on purpose. Simulating the absence of an installed
    package is fiddly and easy to get subtly wrong; "no line in the shipped tree begins
    with `import cryptography`" is exact, and it is the property that actually matters.
    """
    template = REPO_ROOT / "template"
    offenders = []
    for path in sorted(template.rglob("*.py")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.match(r"^(import|from)\s+cryptography\b", line):
                offenders.append(f"{path.relative_to(template)}:{lineno}: {line.strip()}")
    if offenders:
        return [f"'cryptography' is imported at module level in the emitted brain — a brain "
                f"without the optional dependency would break on a path unrelated to "
                f"encryption: {offenders}"]
    print(f"  ok    'cryptography' is imported lazily everywhere it is used")
    return []


def main() -> int:
    fails: list[str] = check_dependency_is_optional()
    crypto = have_crypto()
    if not crypto:
        print("  note: optional 'cryptography' is absent — encrypted-mode cases will skip")

    for module in SUITES:
        ok, output = run_suite(module)
        ran = next((line for line in output.splitlines() if line.startswith("Ran ")), "Ran ?")
        skipped = output.count("skipped")
        if not ok:
            fails.append(f"{module} FAILED")
            print(output[-2000:], file=sys.stderr)
        elif crypto and skipped:
            # With the dependency installed nothing should skip. A silent skip here would
            # mean the gate is green while the encrypted path never ran at all.
            fails.append(f"{module}: {skipped} case(s) skipped despite cryptography being "
                         f"installed — the gate would be green over an unexercised path")
        status = "FAIL" if not ok else "ok  "
        print(f"  {status}  {module}: {ran}" + (f" ({skipped} skipped)" if skipped else ""))

    if fails:
        for f in fails:
            print(f"  FAIL  {f}")
        print("\nencryption FAILED")
        return 1
    print("\nencryption OK: mechanism + commit-path selection verified"
          + ("" if crypto else " (encrypted-mode cases skipped: no 'cryptography')"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
