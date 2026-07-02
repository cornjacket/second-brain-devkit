# Second Brain Devkit — System & Generator Specification

This is the **system spec** for the whole Second Brain effort. It describes the
three repositories involved, how knowledge flows between them, how the system
evolves over time, and how this devkit generates and validates a brain.

It deliberately does **not** re-specify the internals of a single brain (PARA
layout, sidecar schema, embedding contract, search CLI). Those are *product*
contracts and live in the canonical **product spec**
([product-spec.md](product-spec.md), devkit-owned per
[OQ-4](open-questions.md#oq-4)). This spec links to those contracts rather than
duplicating them, so they cannot drift.

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
   • owns the canonical product spec (product-spec.md, promoted per OQ-4)

second-brain-test/     THE BRAIN   (golden reference / reference implementation)
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
| `second-brain-test/` | The brain (golden / reference implementation) | The pipeline scripts, hook, and hand-built known-good vault the product spec is validated against. |
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
([product-spec.md](product-spec.md)).

## 4. Lifecycle & evolution

The system is built **prototype-first**, and spec ownership migrates over time:

1. **Proven by hand in the golden.** The product contracts were authored and
   proven by hand in `second-brain-test/` — the *reference implementation*.
2. **Now — devkit owns the spec.** The product spec has been promoted into the
   devkit as the canonical, devkit-owned design spec
   ([product-spec.md](product-spec.md), [OQ-4](open-questions.md#oq-4)). Note it
   is **not** emitted into a generated brain: the design internals have one home
   (here), and a brain instead carries an operational `README.md` plus a
   provenance back-reference to this devkit. The golden is now validated *against*
   this spec rather than being it.
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

### 5.2 Template strategy — how the generator stores & emits a scaffold

**Decision (2026-07-01):** the generator emits by **copying a tracked template
tree**, not by rendering a templating engine. Two findings drive this:

- **No parameterization exists yet.** The golden's product files contain no
  brain-name, author, or path variables (`git grep second-brain-test` over
  product files is empty). A fill-in-the-blank engine would solve a problem the
  product doesn't have. Revisit if a real per-brain variable appears — a copy
  tree is a strict subset of what an engine could do, so the move stays cheap.
- **The template must be tracked *by the devkit*** (OQ-1 Option A direction) so it
  cannot drift and the copy is byte-exact.

So `generate(target, params)` is, in essence: copy the template tree into
`target`, then run the post-steps (seed the vault from `seeds/`, embed the
committed `test`-backend fixtures — [OQ-3](open-questions.md#oq-3)).

**The template is a *curated, cleaned subset* of the golden — not a raw copy of
its working tree.** The golden is at once the reference implementation *and* a
repo we build with AI assistance, so it mixes two things the generator must
separate:

The buckets are enumerated file-by-file in the emit manifest
(`emit-manifest.toml`); `tools/check_manifest_partition.py` proves they partition
the golden's tracked files exactly. In summary:

| Class | Examples | In a generated brain? |
| --- | --- | --- |
| **Product scaffold** (`verbatim`) | the pipeline scripts, `.githooks/pre-commit`, `seeds/`, `tests/`, `config/`, `data/.gitkeep`, `.gitignore`, `.gitattributes`, `requirements.txt` | **Yes — copied verbatim** (the golden was already scrubbed of `SPEC.md §X` refs, so these need no cleaning) |
| **Product file needing cleaning** (`cleaned`) | `CLAUDE.md`/`GEMINI.md` (`ai-project-status` dev-block); `register.py` (`ai-project-status` comment); `README.md` (expanded into the operational doc + devkit provenance) | **Yes, but cleaned** — forbidden tokens scrubbed, `README.md` grown |
| **Generated post-step** (`generated`) | `vault/**` | **Yes — produced by `seed_vault.py`, not templated** |
| **Dev-process artifact** (`exclude`) | `PLAN.md`, `tasks/`, `daily-plan.md`, `.claude/hooks/check-daily-plan.py`, `.claude/settings.json` (`SessionStart`) | **No — discarded** |

The product's **design spec** is a fourth, once-off case: `SPEC.md` was *promoted*
to the devkit ([product-spec.md](product-spec.md), [OQ-4](open-questions.md#oq-4))
and **removed from the golden entirely**, so it is no longer a golden-tracked file
to classify. A brain's user (human or AI) needs *operational* guidance — record /
query / setup — which lives in the brain's `README.md`; the internal contract does
not belong duplicated inside every brain. The `README.md` also carries a
**provenance back-reference to the devkit** (origin + canonical spec home) — a
documented path for the brain's local AI to reach the internals if ever needed,
*not* a runtime dependency. Why the *dev-process* exclusions: `PLAN.md` / `tasks/`
/ `daily-plan.md` and the daily-plan hook are about *using AI to build and track a
repo* — work the generator itself performs — and would leak `ai-project-status`
machinery into every brain, violating §7.

**Hard invariant — zero forbidden references.** No emitted file may contain the
string `ai-project-status` (or any other devkit-internal dependency) — *not even
to declare independence from it*: an end user has never heard of it, so naming it
only confuses. This is **deterministically enforced**, not trusted — the
validation harness greps the generated tree against a denylist and fails on any
hit (`tools/check_no_forbidden_refs.py`, [§5.3](#53-forbidden-reference-guard)).
So `CLAUDE.md` loses its whole dev-process block, and `register.py` loses its lone
independence mention; the *concept* of independence from meta tooling may remain,
just never named. Emitted files likewise carry no dangling `SPEC.md §X` pointer,
since `SPEC.md` is not shipped.

**Consequence for the G2 diff.** Because the template is a curated subset, the
acceptance diff is **not** "generated tree == golden working tree." It compares
only the emitted intersection, driven by the manifest: `exclude` files are
dropped, and `cleaned` files are compared
against their cleaned variant (or excluded from the byte-diff and checked on their
own). That manifest is the single source of truth for "what a brain contains" —
authored in G1, consumed in G2.

### 5.3 Forbidden-reference guard

A deterministic linter — `tools/check_no_forbidden_refs.py` — scans a target tree
for a **denylist** of tokens that must never appear in a generated brain (seeded
with `ai-project-status`) and exits non-zero on any hit, printing `file:line` for
each. It is not a per-brain product artifact; it lives in the devkit and runs as
part of the Mode-A validation harness against the freshly generated
`sandbox/scratch/`. This turns the §5.2 "zero forbidden references" invariant into
a machine-checked gate rather than a manual promise.

## 6. Where the contracts live

| Concern | Authoritative source |
| --- | --- |
| Per-brain contracts (PARA, sidecar schema, embedding, cache DDL, search CLI, `register`) | [product-spec.md](product-spec.md) (product spec, devkit-owned per OQ-4) |
| In-brain agent memory | `../second-brain-test/CLAUDE.md` (golden reference) |
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
spec ([product-spec.md](product-spec.md)).
