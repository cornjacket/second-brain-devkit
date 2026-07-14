#!/usr/bin/env python3
"""Gate 10 — exercise NON-DEFAULT config, not just the defaults (task #29).

Task #28 shipped, passed every gate, and then corrupted note content in a real brain. The
toggle that triggered it — ``glossary_autolink`` — **defaults to false**, so the golden, the
template and every harness run executed with the only file-modifying hook **switched off**.
The write suite that explicitly asserts "never touch the user's staged work" passed for
exactly that reason: *the condition never occurred*.

**A test matrix that only exercises defaults does not test the product.** Every non-default
toggle is a code path with no coverage, and it will be found by the user, on their data.

Two things this gate does:

1. **Coverage is enforced, not remembered.** The toggle space is read from
   ``config/features.toml`` — the real one, as emitted. Every key must have an entry in
   ``MATRIX`` below, or the gate **fails**. So a new toggle cannot ship without coverage;
   forgetting is a build error rather than a bug found in production.
2. **Each toggle is flipped off its default at least once** and the affected behaviour is
   asserted. That is **n+1 runs, not 2^n** — deliberately. The full cross-product is not worth
   its runtime, and n+1 is what would have caught #28.

**Honest about what it does NOT cover** (a silent gap reads as coverage — see §"UNCOVERED"
printed at the end): toggle *interactions* (only one is flipped at a time), and the ``ollama``
backend (every gate here runs the deterministic ``test`` backend; the Ollama paths are
covered only by the opt-in ``check_semantic_retrieval.py``).

    python3 tools/check_config_matrix.py

Hermetic: generates throwaway brains, ``test`` backend, stdlib only. Devkit tool, never emitted.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import generate  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
FEATURES = REPO_ROOT / "template" / "config" / "features.toml"

# Each toggle: the env var that overrides it, its shipped default, and the NON-default value to
# exercise. Adding a key to features.toml without adding it here fails the gate (by design).
MATRIX = {
    "hybrid_search":     {"env": "SECOND_BRAIN_HYBRID_SEARCH",    "default": "true",  "flip": "0"},
    "rrf_k":             {"env": "SECOND_BRAIN_RRF_K",            "default": "60",    "flip": "10"},
    "glossary_autolink": {"env": "SECOND_BRAIN_GLOSSARY_AUTOLINK", "default": "false", "flip": "1"},
}


def _run(cmd: list[str], cwd: Path, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)


def declared_toggles() -> dict[str, str]:
    """key -> default, parsed from the emitted config/features.toml (the real toggle space)."""
    out: dict[str, str] = {}
    for line in FEATURES.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*([a-z_]+)\s*=\s*(\S+)\s*$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def check_coverage() -> list[str]:
    """The anti-recurrence guard: every shipped toggle must be exercised here."""
    declared = declared_toggles()
    fails = []
    for key, default in declared.items():
        if key not in MATRIX:
            fails.append(f"config/features.toml ships '{key}' but tools/check_config_matrix.py "
                         f"has NO coverage for it — a toggle with no test is how #28 shipped. "
                         f"Add it to MATRIX.")
        elif MATRIX[key]["default"] != default:
            fails.append(f"'{key}' default drifted: features.toml says {default!r}, the matrix "
                         f"expects {MATRIX[key]['default']!r} — the flip may no longer be a flip")
    for key in MATRIX:
        if key not in declared:
            fails.append(f"the matrix covers '{key}' but features.toml no longer ships it "
                         f"(stale coverage)")
    return fails


def _git(brain: Path, *args: str, env: dict) -> subprocess.CompletedProcess:
    return _run(["git", *args], brain, env)


def _git_brain(brain: Path, env: dict) -> None:
    _git(brain, "init", "-q", env=env)
    _git(brain, "config", "user.email", "cfg@example.invalid", env=env)
    _git(brain, "config", "user.name", "Config Matrix", env=env)
    _git(brain, "config", "commit.gpgsign", "false", env=env)
    _git(brain, "config", "core.hooksPath", ".githooks", env=env)
    _git(brain, "add", "-A", env=env)
    _git(brain, "commit", "-q", "-m", "seed", env=env)


def check_glossary_autolink(brain: Path, env: dict) -> list[str]:
    """glossary_autolink=TRUE (default false) — the pre-commit hook EDITS a staged note.

    This is the whole class #28 lived in: a hook that rewrites the file being committed. Assert
    the hook links the term, the note embeds *with* its link, and — the #28 signature — the
    index is left CLEAN (nothing staged behind our back for the next commit to apply).
    """
    fails: list[str] = []
    _git_brain(brain, env)
    (brain / "vault" / "glossary" / "ablation.md").write_text(
        "---\ntype: glossary\n---\n\n# ablation\n\nTurn a feature off and re-measure.\n",
        encoding="utf-8")
    note = brain / "vault" / "resources" / "cfg-note.md"
    note.write_text("---\ntags: [cfg]\n---\n\n# Cfg Note\n\nAn ablation quantifies a feature.\n",
                    encoding="utf-8")
    _git(brain, "add", "--", "vault/glossary/ablation.md", "vault/resources/cfg-note.md", env=env)
    c = _git(brain, "commit", "-q", "-m", "note: cfg", env=env)
    if c.returncode != 0:
        return [f"commit failed with glossary_autolink=true: {(c.stderr or c.stdout)[:160]}"]

    committed = _git(brain, "show", "HEAD:vault/resources/cfg-note.md", env=env).stdout
    if "[[ablation]]" not in committed:
        fails.append("glossary_autolink=true did not link the term in the committed note — the "
                     "non-default hook path is broken (or never ran)")
    staged = _git(brain, "diff", "--cached", "--name-only", env=env).stdout.strip()
    if staged:
        fails.append(f"glossary_autolink=true left a DIRTY INDEX after commit: {staged.split()} — "
                     f"a hook that re-stages must not strand changes for the next commit (#28)")
    sidecar = note.parent / f".{note.stem}.embed.json"
    if not sidecar.exists():
        fails.append("the auto-linked note was not embedded — the hook chain broke under the "
                     "non-default toggle")
    return fails


def check_search_toggle(brain: Path, env: dict, label: str) -> list[str]:
    """hybrid_search=false / rrf_k=10 — search must still work, just rank differently.

    The vector-only path is the pre-hybrid baseline the ablation harness uses; it must not rot.
    """
    if _run([sys.executable, "scripts/embed_vault.py"], brain, env).returncode != 0:
        return [f"{label}: embed_vault failed"]
    if _run([sys.executable, "scripts/hydrate_cache.py"], brain, env).returncode != 0:
        return [f"{label}: hydrate_cache failed"]
    r = _run([sys.executable, "scripts/search_vault.py", "knowledge management"], brain, env)
    if r.returncode != 0:
        return [f"{label}: search_vault failed: {(r.stderr or r.stdout).strip()[:160]}"]
    if "vault/" not in r.stdout:
        return [f"{label}: search returned no hits under the non-default toggle: "
                f"{r.stdout.strip()[:120]!r}"]
    return []


def main() -> int:
    fails = check_coverage()
    if fails:  # a missing toggle makes every run below meaningless — fail loudly, first
        for f in fails:
            print(f"  FAIL  {f}")
        print("\nconfig-matrix FAILED: the toggle space is not fully covered")
        return 1

    base = {**os.environ, "SECOND_BRAIN_EMBEDDER": "test"}
    parent = Path(tempfile.mkdtemp(prefix="cfg-matrix-"))
    try:
        for key, spec in MATRIX.items():
            brain = parent / key
            generate(brain)
            env = {**base, spec["env"]: spec["flip"]}
            if key == "glossary_autolink":
                found = check_glossary_autolink(brain, env)
            else:
                found = check_search_toggle(brain, env, f"{key}={spec['flip']}")
            fails += found
            status = "FAIL" if found else "ok  "
            print(f"  {status}  {key}: default {spec['default']} -> exercised at {spec['flip']!r}")
    finally:
        shutil.rmtree(parent, ignore_errors=True)

    if fails:
        for f in fails:
            print(f"  FAIL  {f}")
        print(f"\nconfig-matrix FAILED: {len(fails)} assertion(s)")
        return 1

    print(f"\nconfig-matrix OK: all {len(MATRIX)} toggles exercised off their defaults")
    print("  UNCOVERED (stated, not implied): toggle *interactions* (one flip at a time, n+1 not")
    print("  2^n) and the 'ollama' backend (these run 'test'; Ollama is opt-in via")
    print("  check_semantic_retrieval.py). A silent gap reads as coverage — so it is named here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
