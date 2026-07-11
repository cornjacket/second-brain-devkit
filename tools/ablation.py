#!/usr/bin/env python3
"""Ablation harness — quantify a quality feature's contribution (task #12, increment 1).

Runs the #15 benchmark corpus + its labeled query set (``tests/bench-corpus/queries.jsonl``)
through real embeddings and reports IR metrics (recall@1/@5, MRR, nDCG@5, mean top-1 distance,
mean rank-1 margin) under each **feature configuration**, so a feature's payoff is a number,
not a hunch. See the feature catalog in ``docs/quality-features.md``.

This increment ablates the **nomic task prefix** (the #3 feature) on the *query* side: it embeds
every note once with ``search_document:`` (the brain's real scheme) and then re-runs retrieval
with the query embedded three ways — ``search_query:`` (the correct asymmetric pairing),
no prefix, and ``search_document:`` (symmetric) — against the same note index. A query-side flip
needs no note re-embed, so all three configs share one document embedding pass.

**Opt-in / local:** needs Ollama + ``nomic-embed-text``; prints SKIP and exits 0 when Ollama is
absent, so it stays out of the hermetic CI gate (like ``check_semantic_retrieval.py``). Run on
demand::

    python3 tools/ablation.py

Follow-ons (rest of #12): a per-brain ``config/features.toml`` wiring the toggles into the emitted
scripts, and index-time ablations that re-embed the notes (canonical view, embedder/model swap,
chunking) — matrixed because each forces a full re-embed.
"""
from __future__ import annotations

import json
import math
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS = REPO_ROOT / "tests" / "bench-corpus"
QUERIES = CORPUS / "queries.jsonl"
sys.path.insert(0, str(REPO_ROOT / "template" / "scripts"))
from note_view import canonical_body  # noqa: E402  (emitted brain module, reused for fidelity)

OLLAMA = "http://localhost:11434"
MODEL = "nomic-embed-text"
DOC_PREFIX = "search_document: "  # how the brain stores notes (fixed here)
# Query-side configurations to compare (the task-prefix ablation):
QUERY_CONFIGS = {
    "prefixes on (search_query:)": "search_query: ",   # correct asymmetric pairing — baseline
    "prefixes off (no prefix)":    "",                  # raw query text
    "symmetric (search_document:)": "search_document: ",# wrong scheme for search
}
K = 10


def ollama_up() -> bool:
    try:
        urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=5).read()
        return True
    except (urllib.error.URLError, OSError):
        return False


def embed(text: str) -> list[float]:
    body = json.dumps({"model": MODEL, "prompt": text}).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/embeddings", data=body,
                                 headers={"Content-Type": "application/json"})
    v = json.loads(urllib.request.urlopen(req, timeout=60).read())["embedding"]
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def rank_of(qvec, doc_index, expected: set[str]) -> tuple[int, float, float]:
    """Return (1-indexed rank of the best expected note, its distance, rank-1 margin).

    Margin = distance(rank-2) − distance(rank-1): how clearly the top hit won.
    """
    scored = sorted(((1.0 - dot(qvec, dv), name) for name, dv in doc_index.items()))
    rank = next((i for i, (_, name) in enumerate(scored, 1) if name in expected), None)
    top1_dist = scored[0][0]
    margin = scored[1][0] - scored[0][0] if len(scored) > 1 else 0.0
    return (rank if rank is not None else len(scored) + 1), top1_dist, margin


def metrics(ranks, top1_dists, margins) -> dict:
    n = len(ranks)
    dcg = [1.0 / math.log2(r + 1) if r <= 5 else 0.0 for r in ranks]  # single relevant → idealDCG=1
    return {
        "recall@1": sum(r == 1 for r in ranks) / n,
        "recall@5": sum(r <= 5 for r in ranks) / n,
        "MRR": sum(1.0 / r for r in ranks) / n,
        "nDCG@5": sum(dcg) / n,
        "mean top-1 dist": sum(top1_dists) / n,
        "mean margin": sum(margins) / n,
    }


def main() -> int:
    if not ollama_up():
        print("ablation: SKIP — Ollama not reachable at "
              f"{OLLAMA} (run `ollama serve` + `ollama pull {MODEL}`).")
        return 0
    if not QUERIES.exists():
        print(f"ablation: no query set at {QUERIES}", file=sys.stderr)
        return 1

    notes = sorted(CORPUS.rglob("bench_*.md"))
    queries = [json.loads(l) for l in QUERIES.read_text().splitlines() if l.strip()]
    print(f"ablation: embedding {len(notes)} notes + {len(queries)} queries via {MODEL} …")

    doc_index = {p.name: embed(DOC_PREFIX + canonical_body(p.read_text())) for p in notes}
    # Pre-embed each query once per prefix, then score all configs against the one doc index.
    qvecs = {prefix: [embed(prefix + q["query"]) for q in queries]
             for prefix in set(QUERY_CONFIGS.values())}

    print(f"\nAblation: nomic task prefix (query side), {len(queries)} queries, "
          f"notes stored with '{DOC_PREFIX.strip()}'\n")
    cols = ["recall@1", "recall@5", "MRR", "nDCG@5", "mean top-1 dist", "mean margin"]
    print("  " + "config".ljust(30) + "".join(c.rjust(16) for c in cols))
    for label, prefix in QUERY_CONFIGS.items():
        ranks, d1, mg = [], [], []
        for q, qv in zip(queries, qvecs[prefix]):
            r, t, m = rank_of(qv, doc_index, set(q["expected"]))
            ranks.append(r); d1.append(t); mg.append(m)
        m = metrics(ranks, d1, mg)
        print("  " + label.ljust(30) + "".join(f"{m[c]:16.3f}" for c in cols))
    print("\n(higher recall/MRR/nDCG/margin = better; lower top-1 dist = tighter.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
