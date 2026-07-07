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
  - **Deterministic ordering** — serialize the neighbor set in a fixed order (e.g. by
    distance then note path) so an unchanged set always renders byte-identically → no
    spurious diffs.
  - **Hysteresis / margin near the threshold** — neural vectors carry cross-machine float
    noise (OQ-3), so a neighbor sitting exactly on the cut can flip between runs/machines.
    A margin (add above `t_hi`, drop below `t_lo`) keeps the set stable.
- **When it runs (open question, §6):** likely an **on-demand** `scripts/autolink.py`
  (bulk, like `embed_vault.py`) or an explicit command — **not** an automatic per-commit
  hook — precisely to control churn and keep it deterministic.

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
