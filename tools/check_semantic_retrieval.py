#!/usr/bin/env python3
"""G2 semantic tier — assert real retrieval quality, not bytes (OQ-2).

The structural tier (`check_structural_diff.py`) proves the generator emits the
right *bytes* using the deterministic `test` embedder. It can never prove the one
thing that matters to a user: that a natural-language query actually finds the
right note. That needs the **real** embedder (`nomic-embed-text` via Ollama), whose
vectors are semantic but *not* byte-reproducible across machines — so this tier
asserts **behavior** (top-k ranking + a cosine-distance threshold), never exact
floats.

What it does, end-to-end against a freshly generated brain (in a temp dir):
  generate → `SECOND_BRAIN_EMBEDDER=ollama embed_vault.py` → `hydrate_cache.py`
  → for each known query, `search_vault.py` and assert the expected note ranks #1
    within a distance threshold.

This exercises the real production path the `test` backend never touches: the
Ollama call, the 768-dim check, L2-normalize, sqlite-vec KNN.

**Opt-in and Ollama-gated** — NOT part of the portable CI acceptance gate (which
stays stdlib-only). If Ollama or the model is unavailable it prints SKIP and exits
0, so it is safe to run anywhere; it only *fails* on a genuine retrieval regression.

    python3 tools/check_semantic_retrieval.py

This is a devkit tool; it is never emitted into a brain.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import generate  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.environ.get("SECOND_BRAIN_EMBED_MODEL", "nomic-embed-text")

# Known query → the note that should rank #1, with a max acceptable cosine
# distance. Thresholds are loose (well above observed ~0.25–0.40 top-1 distances)
# so the check asserts *relevance*, not a brittle float. Distinct-phrasing queries
# that share no keyword with the note's title, to test semantics not lexical match.
CASES = [
    ("how are text representations compared by geometric closeness",
     "vault/resources/embeddings.md", 0.45),
    ("vector search inside a local sqlite database file",
     "vault/resources/sqlite-vec.md", 0.45),
    ("organizing notes by how actionable they are",
     "vault/areas/knowledge-management.md", 0.50),
    ("a single source of truth humans and an AI both read",
     "vault/projects/second-brain.md", 0.50),
]


def ollama_ready() -> tuple[bool, str]:
    """(reachable + model pulled?, reason). Drives the SKIP gate."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=3) as resp:
            tags = json.loads(resp.read())
    except Exception as exc:  # noqa: BLE001 — any failure means "not available"
        return False, f"Ollama not reachable at {OLLAMA_HOST} ({exc})"
    names = {m.get("name", "") for m in tags.get("models", [])}
    if not any(n == MODEL or n.startswith(f"{MODEL}:") for n in names):
        return False, f"model {MODEL!r} not pulled (have: {sorted(names) or 'none'})"
    return True, ""


def _run(cmd: list[str], cwd: Path, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)


def top_hit(brain: Path, env: dict, query: str) -> tuple[str, float] | None:
    """Return (source_file, distance) of the #1 search result, or None."""
    r = _run([sys.executable, "scripts/search_vault.py", query, "-k", "3"], brain, env)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit("semantic: search_vault.py failed")
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    if not lines:
        return None
    dist_str, _, source = lines[0].partition("  ")
    return source.strip(), float(dist_str)


def main() -> int:
    ready, why = ollama_ready()
    if not ready:
        print(f"SKIP semantic tier — {why}")
        print("  (opt-in, Ollama-gated; not part of the CI acceptance gate)")
        return 0

    env = {**os.environ, "SECOND_BRAIN_EMBEDDER": "ollama",
           "SECOND_BRAIN_EMBED_MODEL": MODEL}
    parent = Path(tempfile.mkdtemp(prefix="semantic-"))
    brain = parent / "brain"
    try:
        generate(brain)
        print(f"generated brain -> {brain}")
        if _run([sys.executable, "scripts/embed_vault.py"], brain, env).returncode != 0:
            raise SystemExit("semantic: embed_vault.py failed")
        if _run([sys.executable, "scripts/hydrate_cache.py"], brain, env).returncode != 0:
            raise SystemExit("semantic: hydrate_cache.py failed")
        print(f"embedded + hydrated with {MODEL}\n")

        failures = 0
        for query, expected, threshold in CASES:
            hit = top_hit(brain, env, query)
            if hit is None:
                print(f"  FAIL  no results — {query!r}")
                failures += 1
                continue
            source, dist = hit
            ok_rank = source == expected
            ok_dist = dist <= threshold
            if ok_rank and ok_dist:
                print(f"  ok    {dist:.4f} ≤ {threshold}  {source}")
                print(f"          ← {query!r}")
            else:
                reason = ("wrong note" if not ok_rank
                          else f"distance {dist:.4f} > {threshold}")
                print(f"  FAIL  {reason} — got {source} @ {dist:.4f}, expected {expected}")
                print(f"          ← {query!r}")
                failures += 1

        total = len(CASES)
        print()
        if failures:
            print(f"semantic tier FAILED: {failures}/{total} query(ies) regressed")
            return 1
        print(f"semantic tier OK: {total}/{total} queries retrieve the expected note #1")
        return 0
    finally:
        shutil.rmtree(parent, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
