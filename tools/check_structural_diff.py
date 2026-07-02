#!/usr/bin/env python3
"""G2 structural diff — the acceptance oracle for a generated brain (SPEC §5.2).

Byte-compares a generated brain against a known-good reference, driven by the emit
manifest. The manifest's four buckets are NOT all diffed the same way, because a
generated brain is a *curated* subset of the golden, not a copy of its working
tree:

  • ``verbatim`` + ``generated`` (vault/**) → compared against the **golden**
    (the vendored ``tests/golden/`` snapshot, OQ-1 Option A). This is the real
    end-to-end check: the whole
    pipeline (build_template → generate) must reproduce the golden byte-for-byte.
    Meaningful because the vault notes are plain copies and the committed fixtures
    use the deterministic ``test`` backend (OQ-3) — no neural float drift.
  • ``cleaned`` → compared against their **cleaned ``template/`` variant**, not the
    golden. The golden carries the *uncleaned* original (its ai-project-status
    dev-block, golden-reference framing), so it is the wrong reference here.
    Cleaning *correctness* is enforced elsewhere (build_template.py anchors + the
    forbidden-ref guard); this leg just proves ``generate()`` carried the cleaned
    file through intact.
  • ``exclude`` → never emitted, never diffed. If one appears in the generated
    tree it is caught by the completeness check below, not by a per-file compare.

Then a **completeness check**: the generated tree must contain *exactly* the
emitted set (``verbatim`` + ``cleaned`` + ``generated``) — no missing file, and no
stray/leaked extra (an ``exclude`` file, a ``__pycache__``, a live sidecar).

Symlinks (``GEMINI.md`` → ``CLAUDE.md``) are compared by link target, not by
following them.

Exit ``0`` = the generated tree matches; non-zero = drift (prints every mismatch).

    python3 tools/check_structural_diff.py <generated-root>

This is a devkit tool; it is never emitted into a brain.
"""
from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN = REPO_ROOT / "tests" / "golden"          # vendored snapshot (OQ-1 Option A)
TEMPLATE = REPO_ROOT / "template"
MANIFEST = REPO_ROOT / "emit-manifest.toml"


def load_manifest() -> dict:
    with MANIFEST.open("rb") as fh:
        return tomllib.load(fh)


def compare_file(gen: Path, ref: Path, rel: str, ref_label: str,
                 problems: list[str]) -> None:
    """Byte- (or symlink-target-) compare one emitted file against its reference."""
    if not ref.is_symlink() and not ref.exists():
        problems.append(f"  REF-MISSING  {rel} — no {ref_label} reference at {ref}")
        return

    if ref.is_symlink() or gen.is_symlink():
        if not gen.is_symlink():
            problems.append(f"  NOT-SYMLINK  {rel} — expected a symlink (per {ref_label})")
        elif not ref.is_symlink():
            problems.append(f"  UNEXPECTED-SYMLINK  {rel} — {ref_label} is a real file")
        elif os.readlink(gen) != os.readlink(ref):
            problems.append(
                f"  SYMLINK-DIFF  {rel} — target {os.readlink(gen)!r} "
                f"!= {ref_label} {os.readlink(ref)!r}"
            )
        return

    if not gen.exists():
        problems.append(f"  MISSING  {rel} — not in the generated tree")
    elif gen.read_bytes() != ref.read_bytes():
        problems.append(f"  DIFF  {rel} — bytes differ from {ref_label}")


def iter_tree(root: Path) -> list[str]:
    """All files + symlinks under root (posix-relative), excluding any .git dir."""
    out: list[str] = []
    for p in root.rglob("*"):
        if any(part == ".git" for part in p.relative_to(root).parts):
            continue
        if p.is_symlink() or p.is_file():
            out.append(p.relative_to(root).as_posix())
    return out


def check(generated_root: Path) -> int:
    m = load_manifest()
    verbatim = m["verbatim"]["paths"]
    cleaned = m["cleaned"]["paths"]
    generated = m["generated"]["paths"]
    emitted = set(verbatim) | set(cleaned) | set(generated)

    problems: list[str] = []

    # verbatim + vault → golden is the reference (real end-to-end check)
    for rel in sorted(verbatim) + sorted(generated):
        compare_file(generated_root / rel, GOLDEN / rel, rel, "golden", problems)
    # cleaned → the cleaned template variant is the reference
    for rel in sorted(cleaned):
        compare_file(generated_root / rel, TEMPLATE / rel, rel, "template", problems)

    # completeness: the generated tree must be EXACTLY the emitted set
    present = set(iter_tree(generated_root))
    for rel in sorted(present - emitted):
        problems.append(f"  EXTRA  {rel} — present but not an emitted file (leak?)")
    # (missing files are already reported per-bucket above as MISSING)

    total = len(emitted)
    if problems:
        print(f"structural diff FAILED — {len(problems)} mismatch(es) vs the golden:")
        print("\n".join(problems))
        return 1
    print(f"structural diff OK — {total}/{total} emitted files match "
          f"(verbatim+vault vs golden, cleaned vs template); no stray files")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        raise SystemExit("usage: check_structural_diff.py <generated-root>")
    generated_root = Path(argv[0]).resolve()
    if not generated_root.is_dir():
        raise SystemExit(f"check_structural_diff: no generated tree at {generated_root}")
    if not GOLDEN.is_dir():
        raise SystemExit(
            f"check_structural_diff: no vendored golden at {GOLDEN} "
            f"(run tools/vendor_golden.py)"
        )
    return check(generated_root)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
