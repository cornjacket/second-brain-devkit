# Second Brain Devkit — System & Generator Specification

This is the **system spec** for the whole Second Brain effort. It describes the
three repositories involved, how knowledge flows between them, how the system
evolves over time, and how this devkit generates and validates a brain.

It deliberately does **not** re-specify the internals of a single brain (PARA
layout, sidecar schema, embedding contract, search CLI). Those are *product*
contracts and live in the canonical **product spec**:
[`../second-brain-test/SPEC.md`](../second-brain-test/SPEC.md). This spec links
to those contracts rather than duplicating them, so they cannot drift.

## 0. Open Items

Unresolved design decisions are tracked in [open-questions.md](open-questions.md).
Resolve the relevant item before finalizing any feature it affects.

- **OQ-1 — DECIDED (interim):** The golden reference lives as a **standalone
  sibling repo** at `../second-brain-test/` (its own `.git` + remote) so the
  pre-commit hook fires for real while we build. Trade-off: the devkit does not
  track its contents, so they can drift and are synced by hand. Revisit toward
  Option A (tracked files inside the devkit) when the regenerate-and-diff harness
  lands. See
  [open-questions.md](open-questions.md#oq-1-how-should-the-golden-reference-repo-be-stored-inside-the-devkit).

## 1. What this repo is

`second-brain-devkit/` plays two roles:

1. **Generator** — it scaffolds a new Second Brain repo (a dual-interface
   knowledge graph: humans write Markdown in Obsidian; AI queries a local SQLite
   `vec0` cache built from the same notes).
2. **System home** — it is the single place that documents the *entire*
   three-repo workflow: the generator, the brain it produces, and the external
   project repos that feed knowledge into the brain. If you want to understand
   how the whole thing fits together, you start here.

## 2. The three-repo system

```
second-brain-devkit/   GENERATOR + SYSTEM HOME
   • generates a brain and validates it against the golden reference
   • documents the entire three-repo workflow (this file)
   • eventually owns the canonical product spec (after the golden is mothballed)

second-brain-test/     THE BRAIN   (golden reference + canonical product spec, FOR NOW)
   • knowledge store: PARA notes ─embed→ sidecars ─hydrate→ vec0 cache ─search→ AI
   • ships a `register` script that wires an external project repo to itself
   • prototype-first; eventually mothballed once the devkit can generate brains

<your-project-repo>/   KNOWLEDGE SOURCE   (external, any project; not built here)
   • Claude/Gemini builds it; durable lessons, insights, and architecture
     understandings gained along the way are deposited INTO the brain as notes
   • opts in via the brain's `register` script
```

### Roles & responsibilities

| Repo | Role | Owns |
| --- | --- | --- |
| `second-brain-devkit/` | Generator + system home | This system spec, the generator code, the regenerate-and-diff validation harness. |
| `second-brain-test/` | The brain (golden + product spec) | The canonical product contracts, the pipeline scripts, the hand-built known-good vault. |
| `<your-project-repo>/` | Knowledge source | Its own work; a managed block (injected by `register`) telling its agent to deposit learnings into the brain. |

## 3. Knowledge flow

The brain serves two interfaces from one plain-text source of truth:

- **Human interface** — Obsidian over the PARA Markdown vault (write, link, graph).
- **Machine interface** — a local SQLite `vec0` cache the AI queries deterministically.

End-to-end flow:

```
project repo ──register──▶ project CLAUDE.md points at the brain
      │
      ▼  (agent records a durable learning)
brain: new PARA note (.md)
      │  pre-commit hook
      ▼
.embed.json sidecar (768-dim vector)
      │  hydrate
      ▼
SQLite vec0 cache  ──search──▶  AI (Claude / Gemini) gets ranked context
```

Ingestion is **not** a separate path: a "lesson" deposited into the brain is just
a new PARA note, which flows through the same embed → hydrate → search pipeline.
The precise contracts for each stage are in the product spec
([`../second-brain-test/SPEC.md`](../second-brain-test/SPEC.md)).

## 4. Lifecycle & evolution

The system is built **prototype-first**, and spec ownership migrates over time:

1. **Now — golden is canonical.** The product contracts are authored and proven
   by hand in `second-brain-test/`. That repo is both the *reference
   implementation* and the *canonical product spec*. The devkit links to it.
2. **Later — devkit becomes canonical.** Once the generator can reliably produce
   a brain, the product spec is promoted into the devkit as a template, and the
   devkit emits it (and the rest of the brain) into every generated repo.
3. **Eventually — the golden is mothballed.** Once generation + the
   regenerate-and-diff harness are trustworthy, `second-brain-test/` is retired;
   the devkit's generated output, validated against the harness, takes its place.

## 5. The generator & its validation loop

The devkit builds each feature with a three-step loop:

1. **Prototype** the feature by hand in the golden reference
   (`../second-brain-test/`) and confirm it behaves as expected. The golden is
   the known-good *expected output* and the regression baseline.
2. **Productize** it into the devkit — the script, prompt, or harness that
   *generates* the feature.
3. **Validate** by running the devkit against a throwaway repo at
   `sandbox/scratch/`. The harness must **wipe-and-regenerate** `sandbox/scratch/`
   on every run (never test against stale state), then **diff** the generated
   output against the golden. **A clean diff is the acceptance test.**

- `sandbox/` is gitignored — regenerated output, never committed.
- The golden answers *"does the feature work?"*; `sandbox/scratch/` answers
  *"does the devkit generate it correctly?"*
- Determinism of the golden's sidecars (via the `test` embedding backend) is what
  makes the diff meaningful — see the product spec's embedding contract.

### 5.1 Two generation modes: validation vs production

Generation happens in **two modes that share one generator core but have opposite
lifecycles.** The generator is a pure function — `generate(target, params)` writes
a brain scaffold into `target`; only the target and the post-step differ.

| | **Validation (Mode A)** | **Production (Mode B)** |
| --- | --- | --- |
| Purpose | prove the generator is correct | produce a real brain for a user |
| Target | `sandbox/scratch/` (inside devkit) | a user-chosen path (e.g. `~/my-brain`) |
| Post-step | diff vs golden → **discard** | `git init` + first commit → **kept** |
| Git | gitignored; never tracked | its **own** repo, tracked by the **user** |
| Owner | the devkit's test harness | the end user |

```
generator core ─▶ sandbox/scratch/ ─diff─▶ golden      (Mode A: throwaway self-test)
generator core ─▶ ~/my-brain ─git init─▶ user's repo   (Mode B: the durable product)
```

Consequences:

- **The product is Mode B and is never thrown away.** `sandbox/scratch/` is only a
  test artifact — a stand-in for "what a user would get" — so it can be discarded.
  The real output lands at a user path and persists.
- **A generated brain is tracked by its own git**, created at generation time
  (`git init`, `core.hooksPath`, first commit). Its history *starts* at generation
  and is owned by the user. It is **never** nested inside the devkit's git (the
  repo-inside-a-repo antipattern — see [OQ-1](open-questions.md#oq-1-how-should-the-golden-reference-repo-be-stored-inside-the-devkit)).
- **The diff-vs-golden only governs a *freshly* generated brain** (default seed).
  Once the user adds notes, their brain diverges from the golden — expected, not a
  failure.
- The two modes must produce **byte-identical** scaffolds at generation time; Mode
  A is what proves that, so Mode B can be trusted without re-diffing.

## 6. Where the contracts live

| Concern | Authoritative source |
| --- | --- |
| Per-brain contracts (PARA, sidecar schema, embedding, cache DDL, search CLI, `register`) | [`../second-brain-test/SPEC.md`](../second-brain-test/SPEC.md) (product spec) |
| In-brain agent memory | `../second-brain-test/CLAUDE.md` |
| System workflow, roles, lifecycle, generator/validation | **this file** |
| Working *on* the devkit (build/commit/daily-plan conventions) | [CLAUDE.md](CLAUDE.md) |
| Unresolved design decisions | [open-questions.md](open-questions.md) |

## 7. Non-goals & boundaries

- **Disjoint from `ai-project-status`.** The brain and its `register` mechanism
  are independent of the `ai-project-status` meta-repo. A second-brain user must
  **never** be forced into `ai-project-status`. (This devkit happens to be
  *tracked by* `ai-project-status` for its own development — that is unrelated to
  the product and must not leak into anything the generator emits.)
- **Local-first.** No third-party cloud vector stores (Pinecone, Milvus,
  Supabase). The whole system runs against local files and a local model.

## 8. Tech stack (system level)

- **Runtime:** Python 3.11+
- **Storage:** flat-file SQLite 3 with the `sqlite-vec` extension
- **Embeddings:** `nomic-embed-text` (local, via [Ollama](https://ollama.com)) in
  production; a deterministic `test` backend for reproducible golden sidecars
- **Human frontend:** [Obsidian](https://obsidian.md) over the Markdown vault
- **AI frontends:** Claude (Claude Code) and Gemini (Gemini CLI), sharing one
  project memory file

Exact versions, dimensions, env vars, and invariants are specified in the product
spec ([`../second-brain-test/SPEC.md`](../second-brain-test/SPEC.md)).
