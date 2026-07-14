# Auto-linking — vector-derived note links in Obsidian frontmatter

**Status:** backlog / design-only — nothing built. Task #8. A feature that lets the
brain **materialize** its vector-space neighborhoods as **Obsidian-visible links**, so a
human opening the vault sees machine-made clustering in the graph view — while any link a
human (or an AI, by hand) sets stays sticky and is never re-adjusted by the auto-pass.

Sits **before** the Postgres/big-brain Approach B work: it's a local-first, no-new-service
feature that consumes the vectors already in `data/brain.db`.

---

## 0. What it is (and the gap it fills)

Today vector distance serves **retrieval only** — `search_vault` / the MCP server / the
skill rank notes for a query at read time, and nothing is ever written back into the
vault. So an Obsidian user gets no benefit from the embeddings in the **graph view**; the
only edges there are the ones a human drew by hand.

Auto-linking closes that: a pass computes each note's nearest neighbors (KNN over the
existing vectors) and writes them as links **in the note's frontmatter**, which Obsidian
renders as real graph edges. The vault becomes a self-organizing knowledge graph without
anyone hand-linking.

Two features, deliberately separated:

1. **Auto-linking** — the system writes vector-derived links into a managed frontmatter
   block.
2. **Manual-link preservation** — a link a human/AI sets by hand is **never** touched by
   the auto-pass.

## 1. The core invariant — embed substance, not metadata

Everything else hangs off one line:

> **The embedding (and the change-detecting hash) is computed over the note's *substance*
> — its content — never over the *metadata about* the content.** Author-agnostic: the
> substance may be written by a human or by an AI; what matters is that it's the content,
> not bookkeeping about the content.

This is **not** "human-authored only" — AI will author much of the substance, and that
substance must be embedded. The discriminator is **substance vs. metadata**, because the
thing that must be excluded (`related_auto:`) is metadata *derived from the embedding
itself*. Embedding it would round-trip the system's own output.

Why it matters — the **feedback loop** it prevents. Today `embed_staged.py` embeds the
**whole file** (`text = read_text(...)`, `embed(text)`), frontmatter included. So a naive
auto-linker that writes `related_auto:` and lets the hook re-embed would create:

```
embed(body + auto-links) ──► vector shifts toward linked notes ──► auto-pass writes
        ▲                                                          stronger / new links
        └───────────────── re-embed picks up the new links ◄──────────────┘
```

A rich-get-richer loop with an unstable fixed point — the embedding partly derived from
its own prior output. Excluding metadata from the embedding input breaks it at the source:
the vector is a function of substance only, the auto-links are a pure downstream read of
the vector, and one pass reaches a fixed point.

**The loop was only half-closed until 2026-07-14 (task #26).** Excluding *frontmatter* shut
the `related_auto:` door — but `glossary_scan` writes its links into the **body**, as
`[[wikilinks]]`, and the body *was* being embedded verbatim. So the system's own output was
still round-tripping into its own vectors, just through a different door. The canonical view
now **strips wikilink markup** (`[[term]]` → `term`, `[[slug|surface]]` → `surface`) before
hashing and embedding, which closes it properly and buys a large second prize:

- **A link insertion is now byte-identical in the canonical view**, so `content_hash` matches
  and the existing no-op gate in `embed_staged` **skips the embed entirely**. Auto-linking a
  term across the whole vault costs **zero** re-embeds. That is what makes #25's
  `add_glossary_term` cascade cheap rather than a re-embed storm.
- **A real prose edit still changes the hash and still re-embeds.** The hash comparison over a
  markup-stripped view is precisely what distinguishes *"the content changed"* from *"a link
  was inserted"* — a distinction the raw file cannot express, since both are just "the file
  changed".

The general form, worth remembering beyond this repo: **markup is not substance, and any
derived value written back into an artifact must be computed over a view that excludes it.**
(Written up project-independently in the real brain as *"Embed the substance, not the file"*.)

## 2. Auto-linking pass

- **Input:** the existing per-note vectors in `data/brain.db` (no re-embed needed to
  link). For each note, KNN over the other notes.
- **Output:** a **managed frontmatter property** `related_auto:` holding the neighbors as
  **quoted wikilinks** (see §5 for the Obsidian requirement):

  ```yaml
  related_auto:
    - "[[note-a]]"
    - "[[note-b]]"
  ```

- **Stability rules (essential — the pass rewrites *committed* notes, so churn is the
  enemy):**
  - **Threshold + top-N cap** — only link above a cosine/distance cut, capped at N
    neighbors, so weak links don't flood the graph.
  - **Mutual-KNN (reciprocity) — hub suppression.** Keep an edge `A–B` only when **B is in
    A's top-N _and_ A is in B's top-N**. Note what is and isn't symmetric here: the *distance*
    `d(A,B)=d(B,A)` is always symmetric — that is **not** the discriminator — whereas
    neighbor *membership/rank* is **asymmetric** (A can be in a sparse note's top-N while that
    note is nowhere near A's, because they sit in neighborhoods of different density). A
    **hub** — a note vaguely close to many others — lands in lots of top-N lists, so without
    this rule everything links to it (a star that clutters the graph); but those notes are
    usually *not* in the hub's own top-N, so the one-sided edges are dropped. Mutual-KNN thus
    filters the asymmetric rank relation down to its **reciprocal subset**: fewer edges, each
    higher-precision (both endpoints agree they're close). It raises relevance by *removing*
    weak one-sided links, not by adding links; the surviving edges are symmetric/undirected as
    a **result** of the filter, not its input. (Observed live: at `t_max=0.45`, `magic-number`
    had 4 neighbors under threshold but kept only `[[embeddings]]` — the one pair that was
    reciprocal; the rest were one-sided and pruned.)
  - **Deterministic ordering** — serialize the neighbor set in a fixed order (e.g. by
    distance then note path) so an unchanged set always renders byte-identically → no
    spurious diffs.
  - **Hysteresis / margin near the threshold** — neural vectors carry cross-machine float
    noise (OQ-3), so a neighbor sitting exactly on the cut can flip between runs/machines.
    A margin (add above `t_hi`, drop below `t_lo`) keeps the set stable.
- **When it runs (open question, §6):** likely an **on-demand** `scripts/autolink.py`
  (bulk, like `embed_vault.py`) or an explicit command — **not** an automatic per-commit
  hook — precisely to control churn and keep it deterministic.

### 2.1 First calibration (2026-07-08, `~/second-brain`, 7 notes, ollama + prefixes)

`scripts/autolink.py` (read-only KNN, cosine metric identical to search) was run over the
real brain after the prefix re-embed. All 42 directed note→neighbour distances:

```
min 0.177  median 0.387  max 0.572   (t_max=0.45 links 36/42 edges)
```

Findings that shape the threshold design:

- **The vectors behave well.** Nearest pairs are semantically right (embeddings ↔
  nomic-embedding-prefixes 0.177; second-brain ↔ sqlite-vec 0.236), and the deliberately
  off-topic `magic-number` note is correctly the outlier (its links sit at 0.42–0.57).
- **No clean gap to put a global `t_max` in.** Distances ramp smoothly 0.18 → 0.57 with no
  elbow — because at this size the corpus is **one topical cluster** (six of seven notes are
  about the brain / embeddings / search), so *everything is genuinely related to everything*.
  A fixed cut either links the whole graph (`0.45`) or is arbitrary.
- **Conclusion:** a distance threshold alone is not enough at small scale — the **top-N cap
  and mutual-KNN** rule do the real work of keeping the graph legible; `t_max` mainly fences
  off true outliers. **A meaningful `t_max` cannot be derived from this corpus** — it needs
  the larger, more *topically diverse* dataset that the ablation-benchmark work (PLAN tasks
  #12/#13) will build. Provisional starting point to **recalibrate at scale**: `t_max ≈ 0.45`,
  `top-N = 3–5`, mutual-KNN on.

### 2.2 What `t_max` is, and how to calibrate it

**What `t_max` represents.** `t_max` is the **relatedness cutoff** — the *maximum cosine
distance* at which two notes are still considered related enough to link. Vectors are
L2-normalized, so cosine distance = `1 − cosine_similarity`, ranging **0** (identical
direction) → **1** (orthogonal, unrelated) → **2** (opposite). A candidate neighbour at
distance `d` becomes a link **only when `d < t_max`**. So `t_max ≈ 0.45` means "link notes
whose cosine similarity exceeds ~0.55." It is a single scalar living on the *embedding's*
distance scale — which is why it is **invalid across any index-time change** (model,
task-prefix scheme, canonical-view on/off) and must be recalibrated after one.

**Do not gate `t_max` on note count.** Count is a weak proxy for the thing that actually
governs whether a global cut exists — *topical diversity*. The two failure modes:

- **Many homogeneous notes** (500 notes on one project) — still a dense single cluster, no
  clean gap; a count gate fires "big enough!" and hands you a meaningless `t_max`.
- **Few diverse notes** (30 across cooking, taxes, distributed systems, poetry) — large
  gaps, a clean `t_max`; a count gate says "too small" and misses it.

**Derive it from the distance distribution instead.** Whenever calibration runs, estimate
`t_max` from the observed note→note distances with a method that *also self-reports whether
a cut is meaningful*:

- **Background/null model** — take the mean/σ of *all* pairwise distances (the "random
  pair" distribution) and require a link to beat chance by a margin: `t_max = mean − k·σ`. A
  principled "closer than typical?" test.
- **Gap / elbow** — the largest gap in the sorted distances is the natural cut; it only
  *exists* when the corpus is separable, which is exactly the condition we want to detect.
- **2-component mixture** (related vs. unrelated) — fit it; `t_max` is the crossover, and the
  **overlap of the two components is the confidence score**.

**The key property:** the same analysis that estimates `t_max` reports a **separation /
confidence score**. When separation is low (a unimodal distribution — whether from 7
homogeneous notes *or* 5 000 single-topic ones), emit **no global `t_max`** and fall back to
**top-N + mutual-KNN** only. That is the honest behaviour at any scale, and it means the real
gate is *distributional separability*, computed — not note count, guessed.

**Mechanics (detect-and-instruct, matches the devkit stance).**

- **`autolink.py --calibrate`** analyses the current distance distribution and **prints** a
  recommended `t_max` plus the separation score (or "no confident cut → top-N + mutual-KNN").
  Writing it to config requires an explicit flag — it never silently mutates config
  (consistent with `install_skill`/`doctor`).
- **Store the value with provenance** in an `[autolink]` config block: `t_max`,
  `calibrated_at_size`, the method used, the separation score, and an **embedding-config
  fingerprint** (model + prefix scheme + canonical-view flag). A mismatch between the
  fingerprint and the live embedder **invalidates** `t_max` and forces recalibration.
- **Count keeps two narrow roles** (this is where the "size threshold" instinct belongs):
  (a) a **minimum-sample floor** — below ~20–30 notes any estimate is small-sample noise, so
  skip calibration and use conservative defaults; (b) a **staleness trigger** — *suggest*
  recalibration when the corpus has grown materially since `calibrated_at_size` (e.g. +X%).
  Count triggers *re-running the deriver*; it never *sets* the value.

### 2.3 Measuring topical structure — "how many topics?"

Note count was a weak proxy for the real question: **does the corpus contain distinct
topics?** If it has ≥2 *stable* topics a global `t_max` is meaningful; if it is one blob it
is not — regardless of size. So an explicit **topic count** is the better diversity gate, and
it doubles as a corpus-health metric for the benchmark (#12/#13). "Topics" here means
**clusters in the embedding space**.

**Stdlib-first method — connected components / single-linkage over the KNN graph.**
`autolink.py` already builds the note↔neighbour graph. Connect any two notes within distance
`d`, then count **connected components** via union-find (pure Python — no new dependency).
Now *sweep* `d`:

- At a very small `d` every note is its own component (`N` topics); at a large `d` everything
  merges into one (`1` topic).
- **A plateau — a range of `d` over which the component count stays flat — is robust topic
  structure**, and that stable count *is* the topic count. Its `d`-range is a defensible
  `t_max` band.
- A single-cluster corpus (our 7 notes) shows **no plateau** — a monotonic collapse from `N`
  to `1`. So the *existence and width of a plateau* is itself the "is a global `t_max`
  meaningful?" signal.

This **unifies §2.2 and §2.3**: one single-linkage sweep yields the cut height (`t_max`) and
the resulting cluster count (topics) *together*, from the KNN edges autolink already has.

**Optional heavier methods — for the benchmark only, as isolated optional deps** (kept out of
the lean core, like `requirements-mcp.txt`):

- **HDBSCAN** — density-based, needs no `k`, labels off-topic notes as noise. Best fit for
  "how many topics + which notes are outliers," at the cost of the `hdbscan` dependency.
- **k-means + model selection** (silhouette / gap statistic / BIC over `k`) — simple but
  assumes roughly spherical clusters and a bounded `k` (`scikit-learn`).
- **Spectral** — the number of near-zero eigenvalues of the KNN-graph Laplacian ≈ the number
  of clusters (spectral-clustering theory). Principled, but pulls `scipy`/`numpy`.

**Caveats.** "Number of topics" is not absolute — it is the cluster count at a chosen
resolution, best read off a *stable plateau*, not a single cut. And at ~7 notes no method
finds real topics (same small-sample limit as `t_max`), so meaningful topic analysis waits on
the larger #12/#13 corpus. Topic structure also enables a richer future linking rule (prefer
*within-topic* neighbours), but that is downstream of getting the corpus first.

## 3. Manual-link preservation

A human/AI hand-link must be **sticky**. The clean guarantee is **namespace partition**:

- Manual links live in `related:` (or inline body `[[wikilinks]]`).
- Auto links live **only** in `related_auto:`.
- The auto-pass reads/writes **exclusively** its own `related_auto:` block and never
  parses, moves, or rewrites `related:` or body links.

Because the two namespaces are provably disjoint, the auto-pass can never clobber a manual
link — same discipline as `install_skill.py --nudge`, which only ever edits its own marked
region.

## 4. The `content_hash` no-op gate

> **Built 2026-07-08 — sidecar placement for now (frontmatter deferred to big-brain A).**
> The no-op gate ships: `note_view.content_hash(text)` returns `sha256:<hex>` of the
> canonical body, `embed_staged` records it in each `.embed.json` **sidecar**, and
> `write_sidecar` skips the re-embed when the stored hash + backend are unchanged
> (`force` bypasses it for `doctor --repair`). This fully delivers the local benefit —
> no neural-noise churn, and a frontmatter-only `related_auto:` edit no longer triggers a
> re-embed. **Frontmatter placement (below) is deliberately deferred:** it buys only the
> *cross-machine* "my local vector is still valid" signal for [big-brain Approach
> A](big-brain.md), and writing the hash back into the committed note is the pre-commit
> write-back tension flagged in §7 — not worth taking on until big-brain A needs it. The
> sidecar store is per-machine and regenerated, which is exactly right for a local gate.

Store a hash of the canonical substance view in the note's frontmatter (metadata, so it's
excluded from its own input — no self-reference):

```yaml
---
content_hash: sha256:9f2a…       # byte-hash of the canonical substance view (§4.1)
related:                          # manual links — preserved, never embedded
  - "[[hand-picked]]"
related_auto:                     # managed block — auto-written, never embedded
  - "[[note-a]]"
  - "[[note-b]]"
---
<body — the substance that is hashed and embedded>
```

**Gate:** on any embed trigger, compute `hash(canonical view)`; if it equals the stored
`content_hash`, **skip the embed (no-op)**. This does double duty:

- **Kills the feedback loop** — writing `related_auto:` changes metadata but not the
  substance hash → no re-embed → the vector can't drift toward its own links.
- **Kills neural-noise churn** — re-embedding *unchanged* text on Ollama yields
  byte-different floats every time (OQ-3). The hash short-circuits that: unchanged
  substance → the model is never called → no spurious sidecar rewrite.

### 4.1 Byte-consistent hash — a *change* detector, not a *semantic* one

The hash must be a **byte-deterministic, cross-machine-stable** cryptographic hash
(**SHA-256** / BLAKE2) over the canonical bytes. We are detecting whether *anything in the
body changed at the byte level*, **not** semantic difference — so this is the deliberate
**inverse** of the embedding:

| | Embedding vector | `content_hash` |
|---|---|---|
| Reproducible across machines? | **No** — CPU/GPU/BLAS/quantization drift (OQ-3) | **Yes** — a crypto hash is identical everywhere |
| Detects | *semantic* proximity | *byte-level* change |
| Committed to git? | No (sidecar is derived/git-ignored) | **Yes** — travels with the note |

**Canonical substance view (must be byte-identical on any machine):**
- Take the note **body only** — everything after the closing `---` of the frontmatter.
  All frontmatter/metadata is excluded (that's where the metadata lives).
- Decode as **UTF-8**; normalize line endings to **`\n`** (strip `\r`) so a Windows/CRLF
  checkout hashes the same as macOS/Linux — Obsidian runs on all three.
- Pin trailing-whitespace / final-newline handling (e.g. one trailing `\n`) so
  incidental editor differences don't move the hash.
- `SHA-256` the resulting bytes; store as `sha256:<hex>`.

**Placement — committed note frontmatter, not the git-ignored sidecar.** In the note, the
hash travels with the content, which matters for [big-brain Approach A](big-brain.md): a
pulling peer can tell "substance unchanged, my local vector is still valid, skip re-embed"
without needing the other machine's derived sidecar. (Sidecar placement keeps notes
pristine but is local-only — it can't cross machines.)

## 5. Obsidian rendering — a hard requirement

The auto-links **must** show as graph edges in Obsidian. This is satisfiable *inside
frontmatter*, which is what keeps them on the metadata side of the boundary (excluded from
embedding):

- Obsidian's **link-type properties** treat a `[[wikilink]]` in a YAML list property as a
  real link — it appears in **graph view** and the **backlinks** pane.
- The wikilink **must be quoted** (`- "[[note-a]]"`): bare `[[…]]` is invalid/ambiguous
  YAML.

Why frontmatter, not a body block: a managed `[[wikilink]]` block in the **body** would
land in the *substance* region → get embedded → reintroduce the exact loop §1 removes.
Frontmatter avoids that entirely.

**Build-time verification (don't trust the client).** Since this is a hard requirement and
depends on the Obsidian version (link-type properties, ~v1.4+), add an acceptance check
that asserts the emitted frontmatter is the format Obsidian graphs — same lesson as the
`outputSchema`/Claude-Desktop regression, where an untested client assumption shipped
broken.

## 6. The unified boundary (why it all holds together)

One line — substance vs. metadata — does four jobs at once:

| Frontmatter/content | Written by | Obsidian graph edge? | Embedded? | Hashed? | Auto-pass may rewrite? |
|---|---|---|---|---|---|
| Body | human / AI | — | **yes** | **yes** | never |
| `related:` / inline `[[…]]` | human / AI, by hand | yes | no | no | **never** (preserved) |
| `related_auto:` | the auto-pass | yes | no | no | yes (its own block only) |
| `content_hash` | the embedder | — | no | no (its own input) | never |

## 7. Open questions / design tensions

- **When the pass runs** — on-demand `scripts/autolink.py` vs. a hook. Leaning on-demand
  to keep churn controlled and deterministic; a per-commit hook risks constant frontmatter
  diffs.
- **Commit churn on committed notes** — auto-links mutate tracked files. Stability rules
  (§2) are the mitigation; needs real-world tuning of threshold / top-N / margin.
- **Big-brain Approach A interaction** — unlike vectors, `related_auto:` is committed, so
  it **syncs across peers**. But each peer's vectors carry float noise, so running the pass
  on different machines could yield slightly different link sets → frontmatter merge churn.
  Likely wants a single authority (or a wide enough margin) to run it. To hash out with
  [big-brain.md](big-brain.md).
- **PDF / multi-vector sources (task #7)** — once a source has many chunk vectors, "the
  note's neighbors" needs an aggregation rule (max/mean over chunks). Reconcile with the
  multi-vector schema change.
- **Hybrid FTS5 (task #3)** — lexical neighbors could also feed `related_auto:` (fuse with
  the vector KNN), so the two features compose.

## 8. Where it sits

Backlog, alongside tasks #3 (hybrid FTS5) and #7 (PDF ingestion) — all local-first brain
features that ship into every generated brain. **Before** Postgres/big-brain Approach B,
which it does not depend on. Build loop unchanged: prototype the emitted bits in the golden
→ `vendor_golden.py` → rebuild `template/` → `tools/ci.py` green.
