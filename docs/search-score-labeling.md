# The search score is not a distance — label it (task #31)

**Status:** OPEN → fixing 2026-07-14. **Surfaced by a false alarm it directly caused.**
**Scope:** the emitted `skill/second-brain/` (SKILL.md + query.py). The MCP path is already correct.

---

## 1. What happened

A capable reviewer (another Claude session, working in the user's real brain) reported:

> *"All the similarity scores in this vault sit around 0.03, including the top hit. That's what a
> test-backend embedder looks like — deterministic plumbing, not real semantic search. If you
> expected ollama to be live, `config/embedder.toml` may not be pointing where you think."*

**Every part of that diagnosis is wrong, and the brain told it so.** The brain is on Ollama
(`backend = "ollama"`, every sidecar stamped `ollama:nomic-embed-text`, 768-dim vectors). Nothing
is misconfigured.

The 0.03 is **Reciprocal Rank Fusion**, which task #3 shipped. RRF scores each hit as
`Σ 1/(k + rank)` over the vector and lexical rankings, with `rrf_k = 60`:

| hit | score |
| --- | --- |
| ranked #1 in **both** lists | `2/(60+1)` = **0.0328** ← the observed top hit, exactly |
| ranked #5 in **both** lists | `2/(60+5)` = **0.0308** ← the observed last hit, exactly |

**RRF scores are derived from *ranks*, not from similarity.** They therefore *always* sit in a
narrow band around `1/k`, and *always* look "clustered". That is the algorithm working correctly.
And **higher is better** — the exact opposite of a distance.

## 2. The bug is ours

`skill/second-brain/SKILL.md` says:

> *Prints … up to 5 matches as `distance  <absolute-path>` (lower distance = closer match).*

Both halves are false since #3: it is **not a distance**, and **lower is not better**.
`query.py` reinforces it — it prints a bare number and names the variable `dist`.

**When #3 replaced cosine distance with an RRF score, the MCP tool's description was updated
(*"hybrid relevance `score` (larger = more relevant)"*) and the skill's was not.** A partial
update. The skill is the *primary* AI interface — the one every CLI agent uses — so the wrong
description is the one most readers see.

**The brain was instructing its readers to interpret its output backwards**, and a competent
reviewer followed the instructions to a confident, incorrect conclusion, then advised the user
their config was broken. That is what a mislabeled output costs: not a wrong number, but a wrong
*diagnosis*, made with justified confidence, by someone doing everything right.

Note what is *not* broken: ranking. Search still sorts best-first, so results were always correct.
This is purely presentational — which is exactly why it survived so long.

## 3. The fix

- **`SKILL.md`** — call it a **score**, state **higher = more relevant**, and — the part that
  actually prevents a recurrence — say that RRF scores are **rank-derived, cluster near `1/k` by
  construction, and carry no similarity magnitude**. Do not read meaning into their absolute value;
  a 0.03 top hit is normal and says nothing about embedding quality.
- **`query.py`** — rename `dist` → `score` and print a one-line legend in the header it already
  emits.
- Leave `autolink.py` alone. It reports **genuine cosine distances** from a vector-only KNN — those
  *are* distances and lower *is* closer. Correcting them would be the opposite error.

## 4. The lesson worth keeping

**When a quantity's meaning changes, its label is part of the change.** #3 flipped the score from
"distance, lower is better" to "RRF relevance, higher is better" — a reversal of *polarity* and a
change of *units* — and shipped the number under the old name. Everything downstream kept working,
which is precisely why nobody noticed: a mislabeled value fails silently, and it fails in the
**reader**, not the code.

A useful check when changing a metric: *grep for every place its name or its interpretation is
written down, not just every place it is computed.*
