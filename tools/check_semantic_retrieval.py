#!/usr/bin/env python3
"""G2 semantic tier — assert real retrieval quality, not bytes (OQ-2).

The structural tier (`check_structural_diff.py`) proves the generator emits the
right *bytes* using the deterministic `test` embedder. It can never prove the one
thing that matters to a user: that a natural-language query actually finds the
right note. That needs the **real** embedder (`nomic-embed-text` via Ollama), whose
vectors are semantic but *not* byte-reproducible across machines — so this tier
asserts **behavior** (the expected note ranks #1), never exact floats.

Search is now **hybrid** (dense vectors fused with lexical FTS5 via RRF), so the CLI
prints an RRF relevance *score* (higher = better), not a cosine distance. The check is
therefore **rank-based** — it asserts the expected note comes back #1 — which is robust
to the fusion and to the score scale. It covers both paraphrase (vector-strength) and
exact-token (lexical-strength) queries.

What it does, end-to-end against a freshly generated brain (in a temp dir):
  generate → `SECOND_BRAIN_EMBEDDER=ollama embed_vault.py` → `hydrate_cache.py`
  → for each known query, `search_vault.py` and assert the expected note ranks #1.

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

# Known query → the note that should rank #1. Rank-based (no distance threshold): hybrid
# search returns an RRF score, not a cosine distance, so we assert *ranking*. The first
# three are distinct-phrasing paraphrases sharing no title keyword (vector strength); the
# last is a bare identifier (`sqlite-vec`) the lexical FTS5 leg nails (exact-token strength).
CASES = [
    ("how are text representations compared by geometric closeness",
     "vault/resources/embeddings.md"),
    ("vector search inside a local sqlite database file",
     "vault/resources/sqlite-vec.md"),
    ("organizing notes by how actionable they are",
     "vault/areas/knowledge-management.md"),
    ("a single source of truth humans and an AI both read",
     "vault/projects/second-brain.md"),
    ("sqlite-vec", "vault/resources/sqlite-vec.md"),
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
    """Return (source_file, score) of the #1 search result, or None (score: higher=better)."""
    r = _run([sys.executable, "scripts/search_vault.py", query, "-k", "3"], brain, env)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit("semantic: search_vault.py failed")
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    if not lines:
        return None
    score_str, _, source = lines[0].partition("  ")
    return source.strip(), float(score_str)


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
        for query, expected in CASES:
            hit = top_hit(brain, env, query)
            if hit is None:
                print(f"  FAIL  no results — {query!r}")
                failures += 1
                continue
            source, score = hit
            if source == expected:
                print(f"  ok    #1 @ score {score:.4f}  {source}")
                print(f"          ← {query!r}")
            else:
                print(f"  FAIL  wrong note — got {source} @ {score:.4f}, expected {expected}")
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
