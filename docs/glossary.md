# Glossary — a controlled-vocabulary layer for the brain

**Status:** **increment 1 BUILT 2026-07-12** — the namespace + convention emit into every brain:
`vault/glossary/` (non-PARA sibling) with `glossary/README.md`,
`type: glossary` marker, `scripts/glossary_new.py` (dedup-checked term scaffolder; the term shape
is **embedded in the script** — the tool owns the shape it produces, so it survives the
`update_brain.py` path, which re-emits tooling but never the vault — see §7.1),
embedding-exclusion (verified — falls out of PARA-scoping for free), and dual-README + SPEC §2.1
docs (PARA → PARA(G)). Unblocks #20/#21. **Increment 2 BUILT 2026-07-12** — `scripts/glossary_scan.py`,
the on-demand body-link pass: report by default / `--apply` inserts `[[term]]` at the first unlinked
occurrence per note, **idempotent** (skips already-linked terms), skips text inside existing
wikilinks; verified in the golden (report → apply → no-op re-run). **Remaining:** the flashcard/graph
tail (mostly free). Task #19. A feature that gives a
brain a **controlled vocabulary**: one atomic Markdown note per **pre-identified** term,
and every use of that term across the vault links back to its definition. The links are
authored (or scripted) into note **bodies**, where the word actually appears — so a reader
clicks straight from a term to its meaning, and Obsidian's graph shows the vocabulary as a
hub of edges.

This is a **devkit feature**: it ships into every generated brain (the folder convention,
the embed-exclusion rule, the scan tool, and the brain-README docs), not a one-off edit to
one vault. It follows the normal build loop — prototype in the golden
(`../second-brain-test/`) → `vendor_golden.py` → rebuild `template/` → `tools/ci.py` green.

---

## 0. What it is (and the gap it fills)

The vault already has *ad-hoc* concept notes (`resources/embeddings.md`,
`resources/mutual-knn.md`) cross-linked with `[[wikilinks]]` — a de-facto glossary that was
never named or made systematic. This feature makes that pattern **first-class and
controlled**:

- **Curated, not emergent.** A term earns a glossary note only when it is *pre-identified*
  as glossary-worthy (reused across notes, or non-obvious enough that future-you needs the
  definition). The set of glossary terms **is** the "glossary index" — the controlled
  vocabulary. A word used once does not get a node (that is how a vault fills with stubs).
- **Link on use.** Wherever a glossary term appears in another note's body, it is linked to
  its definition note. This is done periodically by a **scan** (§4), not by hand each time.
- **Definitions are simple memories.** A glossary note is a short definition — a *sub-note*,
  not a rich note whose meaning must be inferred by an embedding. Its value is carried by
  **how it is referenced**, not by semantic proximity. This is the crux of §3.

## 1. Namespace — a typed, non-PARA sibling: `vault/glossary/`

PARA (Projects, Areas, Resources, Archive) sorts notes by **actionability**. A glossary
term is not an actionability level — it is a different **axis** (a note *type*). So glossary
notes do **not** belong inside `resources/` (they would drown the real reference notes
~10:1 and pollute search); they get their own top-level folder.

- **Folder:** `vault/glossary/`, flat, **one note per term**, named for the term.
- **Precedent:** `vault/templates/` already sits at that top level and is **not** a PARA
  category — so a typed, non-PARA sibling folder is already an established pattern in the
  vault. `glossary/` simply joins it.
- **Advertising — "PARA(G)".** Writing the scheme as **PARA(G)** in docs is honest signage:
  the parenthesis says "there is a Glossary here" while encoding that it is *orthogonal* to
  P/A/R/A, not a fifth actionability bucket.
- **Tool-facing marker:** `type: glossary` (or `tags: [glossary]`) in the note's
  frontmatter. The **folder is for humans; the frontmatter marker is for tools** — every
  script (embed-exclusion, scanner, flashcards, graph coloring) keys off the marker, so a
  glossary note is recognizable even if one ever lives outside the folder.

## 2. Retrieval substrates — the frame this feature lives in

A brain has **two retrieval substrates**, and this feature is what makes the distinction
explicit (it is itself a candidate glossary term — [[retrieval-substrates]]):

1. **Vector / semantic layer** — "what notes are *about* something like this?" Fuzzy,
   recall-oriented, for rich notes with meaning an embedding can infer. (search_vault, the
   skill, the MCP server, auto-link KNN.)
2. **Symbolic / graph layer** — exact terms, `[[wikilinks]]`, controlled vocabulary.
   Precise, navigational, no inference. (Obsidian graph, backlinks, the glossary scan.)

**Glossary terms are pure symbolic-layer objects.** All three of their use cases — link,
flashcard, graph-highlight — live entirely in the symbolic layer and never touch a vector.

> **MCP exposure (task #20 — BUILT 2026-07-12).**
> An assistant reaches the symbolic layer through two exact-match, no-embedding MCP tools —
> `list_glossary_terms()` and `lookup_glossary_term(term)` — beside the vector-layer
> `search_second_brain`. They enforce the split at the tool boundary: the glossary is
> *intentionally absent* from semantic search, and lookup is for **explicit "what is X" intent
> only** (looking up every concept in sight just recreates the hub problem one layer up). See
> [mcp-server.md §3](mcp-server.md).

## 3. Embedding-exclusion — glossary notes stay out of the vector index

**Decision: glossary notes are excluded from embedding.** The indexer/embedder skips them,
so they never enter `data/brain.db`'s vector table.

- **Why:** a one-line, keyword-dense definition tends to rank **too high** for its own term
  in semantic search and crowd richer notes out of the results — stub-pollution of the
  vector space. And none of the glossary use cases *need* an embedding (§2). Their meaning
  is captured by reference structure, not by vector proximity.
- **How — nearly free, because `glossary/` is a non-PARA root.** Verified 2026-07-10 while
  seeding the real brain: every embed/cache path already scopes to
  `PARA_ROOTS = (projects, areas, resources, archive)` — `embed_staged` (pre-commit),
  `embed_vault.py`, and `update_cache.py` filter on it, and `hydrate_cache.py` only ingests
  existing sidecars (none get written for a glossary note). So a `vault/glossary/` note is
  ignored by the whole pipeline *for free*, exactly like `templates/`. The subtask is
  therefore mostly **confirm + document + keep `glossary/` out of `PARA_ROOTS`**, not new
  exclusion code. (Live proof: committing seven glossary notes to `~/second-brain` produced
  `update_cache: no PARA-note changes in HEAD` and wrote zero sidecars/vectors.)
- **`doctor.py` already ignores them — confirmed.** `doctor`'s `para_notes()` and its
  sidecar scan are both `PARA_ROOTS`-scoped, so glossary notes are invisible to the drift
  checks (no false missing-sidecar / note-missing-from-cache reports). This was the feared
  gotcha; the PARA scoping resolves it with no change. Only revisit if the discriminator ever
  moves from folder-path to the `type: glossary` marker.
- **Not the same as emission-exclusion.** [[embedding-exclusion]] (does the *indexer*
  vectorize this note?) is a different mechanism from [[emission-exclusion]] (does the
  *generator* write this file into a brain at all — e.g. the devkit's `SPEC.md`, the test
  seed-corpus). A glossary note **is** emitted into a brain *and* is embedding-excluded.
- **Inline links are still embedded — and that is correct.** The `[[term]]` link the scan
  writes into another note's **body** is genuine substance (a human would write it there),
  so it is embedded as part of that note. This is the deliberate **opposite** of
  `related_auto:` (task #8), which is machine-derived-from-the-embedding metadata kept in
  frontmatter and excluded to avoid a feedback loop. A glossary link is curated content, not
  derived output — no loop — so the substance-vs-metadata boundary (auto-linking §1) places
  it correctly on the substance side.

## 4. The scan — link on use (start dumb)

`scripts/glossary_scan.py` (emitted into every brain, stdlib-only):

- Walk the vault; for each term in `glossary/`, find occurrences in other notes' bodies.
- **Report unlinked occurrences** by default (dry-run) — "note X uses 'corpus' but does not
  link it." This is the periodic "scan all documents and add the links" workflow.
- **`--apply`** inserts `[[term]]` at the first unlinked occurrence per note. Because it edits
  bodies, it *does* change the substance hash and trigger a re-embed of the touched notes —
  acceptable (the link is real content), but it is an index-perturbing pass.
- **Detect-and-instruct**, `--apply`-gated, idempotent — consistent with
  `install_skill.py` / `doctor.py`.

**Three ways the same link engine runs (`link_body`/`link_note_file`, shared):**
1. **Whole-vault, on-demand** — `glossary_scan.py --apply`. The periodic "link everything" pass.
2. **New term, scoped** — `glossary_new.py "<term>"` sweeps *just that term* across the vault
   after scaffolding it (`--no-relink` to skip). Synchronous and visible — the automatic path
   for adding a term. Chosen over a commit hook because a glossary note is non-PARA (its commit
   wouldn't fire the embed hook) and a hook rewriting *other* notes would leave them unstaged.
3. **Per-commit, contained, opt-in** — when `config/features.toml` `glossary_autolink = true`,
   the pre-commit hook (`glossary_autolink_staged.py`, before `embed_staged.py`) links known
   terms in the **staged** note(s) only and re-stages them, so a note embeds *with* its links.
   Off by default — a hook that edits your prose should be opt-in — and contained (only the
   notes you're already committing), which is what makes it safe where a whole-vault hook wasn't.

The earlier "on-demand, never a hook" stance (churn-control, like `autolink.py`) still holds for
the *whole-vault* sweep; the opt-in per-commit hook is safe precisely because it is scoped to the
staged note, not the whole vault.

**Deliberately the dumb version first** — exact-term matching, report + optional insert.
That delivers ~80% of the value at near-zero cost. Fancier matching (stemming, aliases,
case rules, skip-inside-code-fences) is a follow-on only if the dumb version proves noisy.

## 5. The three linkers — where the glossary sits (the "complementary" frame)

Four mechanisms draw links in the vault, at different precision/recall points:

| Mechanism | Who draws the edge | Precision | Recall | Nature |
|---|---|---|---|---|
| **Vector similarity** (mutual-kNN, task #8) | machine, from embeddings | low | high | semantic, fuzzy |
| **Manual `[[wikilinks]]`** | human/AI, per instance | high | low | judgment |
| **Auto-link `related_auto:`** (task #8) | machine → you promote | (bridges the two) | | vector→curated |
| **Glossary scan** (this feature) | a *rule*, per exact term | high | high\* | deterministic string match |

\* over a **controlled vocabulary you curated by hand.**

They are **complementary**: vector similarity supplies *candidates you forgot about* (recall)
but is noisy; manual wikilinks are *trustworthy* (precision) but sparse; the auto-linker
bridges them (vector proposes → you promote to a wikilink). The **glossary scan is a fourth
thing that does not sit on the vector↔manual spectrum at all** — it is *rule-based* ("wherever
this exact term appears, always link it"). You pay the curation cost once (deciding a word is
glossary-worthy) and get every future link for free — the cheapest high-quality edges in the
system.

## 6. Flashcards & graph — downstream, keep it simple

- **Flashcards / spaced repetition.** Atomic term notes are ideal cards (term = front,
  definition = back). If every glossary note follows a **consistent term-as-title /
  definition-as-body structure from day one**, the community *Spaced Repetition* Obsidian
  plugin can generate cards directly — no bespoke tooling. The only requirement on us is
  structural consistency (don't retrofit 50 notes later).
- **Graph highlighting.** Obsidian's graph view has **native color groups by query** —
  `tag:#glossary` (or `path:glossary/`) colors every glossary node as a group **out of the
  box**, no custom tool. Per-*term* highlighting would need a plugin; **defer it**.

## 7. Sequencing — do not build it all at once

Order by value / cost; earlier items must earn the later ones:

1. **Convention** — `vault/glossary/` folder + `type: glossary` marker + the "link on
   (second) use" rule + a starter `glossary/README.md` + the **term shape** (the flashcard
   form: `Term ? <definition>` + `#flashcards/…` deck tag). **Decision (2026-07-12):** the shape
   is **embedded in `glossary_new.py`**, not a separate `templates/glossary-term.md` file. A
   vault template would be seeded only at *create* time and stranded on the `update_brain.py`
   path (which never writes the vault), breaking the scaffolder on an upgraded brain; and reading
   it back from `seeds/` is semantically wrong (that's the generation baseline, not a runtime
   resource, and it would ignore user edits). The tool owning its output shape is the single
   source of truth; `glossary/README.md` documents the same shape for hand-authors.
2. **New-term helper** — `glossary_new.py <term>`: slugify, **dedup-check** (refuse if the term
   exists, printing its path), else scaffold from the **built-in** shape, print the path
   (never open/overwrite — detect-and-instruct). Guarantees every card is plugin-valid; its value
   is for a human hand-adding terms (an AI just writes the note directly).
3. **Embedding-exclusion** — indexer/hook/cache skip glossary notes; `doctor` treats them as
   intentionally unembedded.
4. **Scanner** — `glossary_scan.py`, report-then-`--apply`.
5. **Flashcards** — free once the note structure is consistent.
6. **Plugin / per-term graph coloring** — last, if ever.

Generated brains ship the **empty** `glossary/` folder + its README + the scanner + the
embed-exclusion — **not** pre-filled terms (the vocabulary is the user's to curate). The
brain README documents the convention and the scan command.

## 8. Candidate seed terms (from the design conversation)

Terms surfaced while designing this, useful as the first entries / prototype examples:
`corpus` · `purity` · `benchmark` · `ground-truth-labels` · [[retrieval-substrates]] ·
[[emission-exclusion]] · [[embedding-exclusion]]. The last three are pleasingly
self-referential — the glossary's own design vocabulary becomes its first entries.

## 9. Where the contract lives

Per the devkit's "don't duplicate product contracts" rule, the **per-brain contract** —
what `type: glossary` means, the `glossary/` location, that glossary notes are
embedding-excluded, and the scan behavior — is specified in the **product spec**
(`../second-brain-test/SPEC.md`), not here. This doc is the devkit-side design rationale;
the PLAN task (#19) tracks the build.

## 10. Open questions

- **Exclusion discriminator** — path (`glossary/**`) vs frontmatter (`type: glossary`) vs
  both as the *primary* key for embed-exclusion. Leaning path-primary (deterministic),
  marker for the semantic tools.
- **Where inline links are inserted** — first occurrence only, every occurrence, or first
  per section. First-per-note is the low-churn default.
- **Alias / surface-form matching** — plural/inflected forms, multi-word terms, acronym vs
  expansion. Out of scope for the dumb v1; revisit if recall is poor.
- **Interaction with a shared brain (big-brain A)** — the scan rewrites committed bodies, so
  like `autolink.py` it wants a single authority or a stable, idempotent pass to avoid
  cross-peer merge churn.
