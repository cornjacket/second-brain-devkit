# Glossary — the brain's controlled vocabulary (the **G** in PARA(G))

This folder is a **controlled-vocabulary layer**: one atomic note per **pre-identified**
term, and every use of that term across the vault links back to its definition. It is a
*different axis* from PARA — not a fifth actionability bucket, but an orthogonal note **type**,
a sibling of `templates/`. Hence **PARA(G)**: **P**rojects · **A**reas · **R**esources ·
**A**rchive, plus a **G**lossary.

## What earns a glossary note

A term earns a `glossary/<term>.md` note only when it is **pre-identified** as
glossary-worthy — **reused** across notes, or **non-obvious** enough that future-you will want
the definition. A word used once does not get a node (that is how a vault fills with stubs).
The set of glossary terms *is* your controlled vocabulary.

## How glossary notes differ from PARA notes

- **Not semantically searchable — by design.** Glossary notes are **excluded from the vector
  index** (`data/brain.db`): they never get an `.embed.json` sidecar and never appear in
  `search_vault.py` results. A one-line definition is keyword-dense and would rank too high for
  its own term, crowding out richer notes. Their value is carried by **how they are
  referenced** (the link graph), not by embedding proximity — the **symbolic** retrieval layer,
  not the semantic one. This falls out for free: `glossary/` is not a PARA root, and the whole
  embed/cache pipeline scopes to PARA roots (exactly like `templates/`).
- **The inline `[[term]]` links _are_ embedded** — and that is correct. A link written into
  another note's *body* is genuine substance, so it is embedded as part of that note. Only the
  definition note itself is excluded.
- **`type: glossary` is the tool-facing marker.** The folder is for humans; the frontmatter
  `type: glossary` key is what tools (the scan, flashcards, graph coloring) key off.

## Adding a term

1. Copy [`../templates/glossary-term.md`](../templates/glossary-term.md) into this folder,
   renamed to the term in lowercase-kebab-case (e.g. `retrieval-substrates.md`).
2. Fill in the one-line definition. Keep it atomic — one term, one meaning.
3. Commit it. (It won't be embedded — see above — so there is no sidecar to manage.)

The term-note shape (`Term ? <definition>` + a `#flashcards/…` deck tag) is valid for the
community **Spaced Repetition** Obsidian plugin out of the box, so your glossary doubles as a
flashcard deck.

## Linking terms across the vault

Wherever a glossary term appears in another note's body, link it to its definition with
`[[term]]` — that inline link is what carries the term's meaning (and draws the graph edge).
A `scripts/glossary_scan.py` tool to automate this — report unlinked occurrences and, with
`--apply`, insert the links as an on-demand pass — is on the roadmap; for now, add the links by
hand as you write.

## What ships in a fresh brain

Just this README and the term template — **no pre-filled terms**. The vocabulary is yours to
curate. In Obsidian's graph view, color the whole layer at once with a `path:glossary/` (or
`tag:#glossary`) color group.
