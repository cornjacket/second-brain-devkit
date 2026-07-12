#!/usr/bin/env python3
"""Ablation harness — quantify a quality feature's contribution (task #12).

Runs the #15 benchmark corpus + its labeled query set (``tests/bench-corpus/queries.jsonl``)
through real embeddings and reports IR metrics (recall@1/@5, MRR, nDCG@5, mean top-1 distance,
mean rank-1 margin) under each **feature configuration**, so a feature's payoff is a number,
not a hunch. See the feature catalog in ``docs/quality-features.md``.

Two cost classes of feature, and the harness treats them differently:

- **§1 Task prefix — query-time.** A query-side flip needs no note re-embed, so all three
  configs share **one** ``search_document:`` note-embedding pass (increment 1).
- **§2 Canonical view / §3 model swap — index-time.** Flipping these changes the *stored*
  vectors, so each config re-embeds the notes. A process-wide memo (keyed ``(model, text)``)
  dedupes passes that happen to coincide (e.g. the nomic/canonical/``search_document:`` note
  pass is shared by §1, §2-ON and §3-nomic — embedded once).

**Opt-in / local:** needs Ollama + the models below; prints SKIP and exits 0 when Ollama is
absent (like ``check_semantic_retrieval.py``), and SKIPs an individual §3 model that isn't
pulled. Run on demand::

    python3 tools/ablation.py                # far-apart domains (#15 bench corpus)
    python3 tools/ablation.py --corpus it    # everything-adjacent IT topics (#16/#17 — the hard case)

§3 compares embedders (the [embedding-separation §6](../docs/embedding-separation.md) lever) —
each model uses **its own trained retrieval scheme** so it performs as it would if shipped.
Pull a second embedder first, e.g. ``ollama pull mxbai-embed-large``.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# Selectable benchmark corpora → (subdir under tests/, note-file glob). Both are devkit-side and
# never emitted; each ships its own labeled queries.jsonl.
CORPORA = {
    "bench": ("bench-corpus", "bench_*.md"),  # #15 — far-apart domains (clean/separable)
    "it":    ("seed-corpus",  "seed_*.md"),   # #16/#17 — everything-adjacent IT topics (the hard case)
}
sys.dont_write_bytecode = True  # never drop a __pycache__ into the tracked template/ tree
sys.path.insert(0, str(REPO_ROOT / "template" / "scripts"))
from note_view import canonical_body  # noqa: E402  (emitted brain module, reused for fidelity)

OLLAMA = "http://localhost:11434"
NOMIC = "nomic-embed-text"
COLS = ["recall@1", "recall@5", "MRR", "nDCG@5", "mean top-1 dist", "mean margin"]

# Per-model retrieval scheme for §3 — each embedder gets the (doc_prefix, query_prefix) it was
# trained with, so the comparison is model-vs-model at each model's best, not a prefix artefact.
#   nomic-embed-text : nomic's search_document:/search_query: instruction prefixes (768-dim).
#   mxbai-embed-large: no doc prefix; the mixedbread retrieval query instruction (1024-dim).
MODEL_SCHEMES = [
    ("nomic-embed-text (768d)",  NOMIC,               "search_document: ", "search_query: "),
    ("mxbai-embed-large (1024d)", "mxbai-embed-large", "",
     "Represent this sentence for searching relevant passages: "),
]


def ollama_up() -> bool:
    try:
        urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=5).read()
        return True
    except (urllib.error.URLError, OSError):
        return False


def models_available() -> set[str]:
    """Locally-pulled model names, both the full ``name:tag`` and the bare name."""
    try:
        data = json.loads(urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=5).read())
    except (urllib.error.URLError, OSError):
        return set()
    names: set[str] = set()
    for m in data.get("models", []):
        n = m.get("name", "")
        names.add(n)
        names.add(n.split(":")[0])
    return names


_MEMO: dict[tuple[str, str], list[float]] = {}


def embed(model: str, text: str) -> list[float]:
    """L2-normalized embedding of ``text`` by ``model`` via Ollama, memoized per (model, text)."""
    key = (model, text)
    cached = _MEMO.get(key)
    if cached is not None:
        return cached
    body = json.dumps({"model": model, "prompt": text}).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/embeddings", data=body,
                                 headers={"Content-Type": "application/json"})
    v = json.loads(urllib.request.urlopen(req, timeout=120).read())["embedding"]
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    vec = [x / n for x in v]
    _MEMO[key] = vec
    return vec


def full_text(text: str) -> str:
    """Identity body view — the 'canonical view OFF' input (frontmatter included)."""
    return text


def embed_corpus(notes, queries, model, doc_prefix, query_prefix, body_fn):
    """Embed the note corpus + the query set under one index-time config.

    Returns ``(doc_index, qvecs)`` where ``doc_index`` maps note filename -> vector and ``qvecs``
    is parallel to ``queries``. ``body_fn`` selects the note view (``canonical_body`` vs
    ``full_text``). Notes and queries share ``model`` so their vectors are always comparable.
    """
    doc_index = {p.name: embed(model, doc_prefix + body_fn(p.read_text())) for p in notes}
    qvecs = [embed(model, query_prefix + q["query"]) for q in queries]
    return doc_index, qvecs


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def rank_of(qvec, doc_index, expected: set[str]) -> tuple[int, float, float]:
    """Return (1-indexed rank of the best expected note, its distance, rank-1 margin).

    Margin = distance(rank-2) - distance(rank-1): how clearly the top hit won.
    """
    scored = sorted(((1.0 - dot(qvec, dv), name) for name, dv in doc_index.items()))
    rank = next((i for i, (_, name) in enumerate(scored, 1) if name in expected), None)
    top1_dist = scored[0][0]
    margin = scored[1][0] - scored[0][0] if len(scored) > 1 else 0.0
    return (rank if rank is not None else len(scored) + 1), top1_dist, margin


def metrics(ranks, top1_dists, margins) -> dict:
    n = len(ranks)
    dcg = [1.0 / math.log2(r + 1) if r <= 5 else 0.0 for r in ranks]  # single relevant -> idealDCG=1
    return {
        "recall@1": sum(r == 1 for r in ranks) / n,
        "recall@5": sum(r <= 5 for r in ranks) / n,
        "MRR": sum(1.0 / r for r in ranks) / n,
        "nDCG@5": sum(dcg) / n,
        "mean top-1 dist": sum(top1_dists) / n,
        "mean margin": sum(margins) / n,
    }


def score(doc_index, qvecs, queries) -> dict:
    """Metrics for one config: rank every query's expected note against the doc index."""
    ranks, d1, mg = [], [], []
    for q, qv in zip(queries, qvecs):
        r, t, m = rank_of(qv, doc_index, set(q["expected"]))
        ranks.append(r); d1.append(t); mg.append(m)
    return metrics(ranks, d1, mg)


def print_table(title: str, rows: list[tuple[str, dict]]) -> None:
    print(f"\n{title}\n")
    print("  " + "config".ljust(32) + "".join(c.rjust(16) for c in COLS))
    for label, m in rows:
        print("  " + label.ljust(32) + "".join(f"{m[c]:16.3f}" for c in COLS))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Ablation harness — quantify a feature's contribution "
                                             "(task #12).")
    ap.add_argument("--corpus", choices=sorted(CORPORA), default="bench",
                    help="which benchmark corpus to ablate: 'bench' (far-apart domains, #15) or "
                         "'it' (everything-adjacent IT topics, #16/#17). Default: bench.")
    args = ap.parse_args(argv)
    subdir, note_glob = CORPORA[args.corpus]
    corpus = REPO_ROOT / "tests" / subdir
    queries_path = corpus / "queries.jsonl"

    if not ollama_up():
        print("ablation: SKIP — Ollama not reachable at "
              f"{OLLAMA} (run `ollama serve` + `ollama pull {NOMIC}`).")
        return 0
    if not queries_path.exists():
        print(f"ablation: no query set at {queries_path}", file=sys.stderr)
        return 1

    notes = sorted(corpus.rglob(note_glob))
    queries = [json.loads(l) for l in queries_path.read_text().splitlines() if l.strip()]
    have = models_available()
    print(f"ablation: {len(notes)} notes / {len(queries)} queries "
          f"({args.corpus} corpus), embedding on demand …")

    # --- §1  Task prefix (query-time): one nomic/canonical note pass, sweep the query prefix. ---
    doc_nomic, _ = embed_corpus(notes, queries, NOMIC, "search_document: ", "search_query: ",
                                canonical_body)
    rows1 = []
    for label, qp in (("prefixes on (search_query:)", "search_query: "),
                      ("prefixes off (no prefix)", ""),
                      ("symmetric (search_document:)", "search_document: ")):
        qvecs = [embed(NOMIC, qp + q["query"]) for q in queries]
        rows1.append((label, score(doc_nomic, qvecs, queries)))
    print_table("§1  nomic task prefix — query-time (notes stored 'search_document:')", rows1)

    # --- §2  Canonical substance view (index-time): nomic, correct prefixes, ON vs OFF body. ---
    rows2 = []
    for label, body_fn in (("canonical view ON (body only)", canonical_body),
                           ("canonical view OFF (full text)", full_text)):
        di, qv = embed_corpus(notes, queries, NOMIC, "search_document: ", "search_query: ", body_fn)
        rows2.append((label, score(di, qv, queries)))
    print_table("§2  canonical substance view — index-time (nomic, correct prefixes)", rows2)

    # --- §3  Embedder model swap (index-time): canonical body, each model's native scheme. ---
    rows3, skipped = [], []
    for label, model, dp, qp in MODEL_SCHEMES:
        if model not in have and model.split(":")[0] not in have:
            skipped.append((label, model))
            continue
        di, qv = embed_corpus(notes, queries, model, dp, qp, canonical_body)
        rows3.append((label, score(di, qv, queries)))
    if rows3:
        print_table("§3  embedder model swap — index-time (canonical body, each model's native "
                    "scheme)", rows3)
        print("      (recall/MRR/nDCG are rank-based → comparable across models; top-1 dist / "
              "margin are model-relative.)")
    for label, model in skipped:
        print(f"\n§3  SKIP {label} — not pulled (`ollama pull {model}`).")

    print("\n(higher recall/MRR/nDCG/margin = better; lower top-1 dist = tighter.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
