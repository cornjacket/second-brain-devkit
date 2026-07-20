# PDF ingestion — chunk-and-embed long documents (task #7)

**Status:** Design (M0) locked 2026-07-19. **M1–M6 done — PDF ingestion shipped.** Every generated
brain now ingests and searches PDFs end to end. Built, prototyped in the golden, emitted, and gated:
M1 (`chunker.py` + `pdf_extract.py`), M2 (`embed_pdf.py`, chunk-list sidecar, byte-exact fixture),
M3 (`pdf_cache.py`, the bolt-on `pdf_chunks`/`_meta`/`_fts` tables + loader wired into
`hydrate_cache.py` so the note path stays byte-identical), M4 (`pdf_search.py`, chunk-grain RRF
passage search + shaping + within-document + `get_passage`), M5 (`add_pdf.py`, the ingest engine +
`pdf_config.py`), and M6 (all seven modules promoted to `verbatim`; the `[pdf]` config block; the
four MCP tools `list_inbox_pdfs`/`add_pdf`/`search_pdf_passages`/`get_pdf_passage`; the "Add a PDF"
README section; `requirements-pdf.txt`; CI gate 14; and doctor PDF parity). **Deferred:** MCP
*elicitation* (a client-rendered selection form) — Claude Desktop's chat surface does not implement
it (§2), and chat selection works everywhere, so it is a future enhancement, not a blocker.

## TL;DR

Today a brain ingests only **Markdown notes**, and each note becomes **one vector**. A PDF is long
and spans many topics, so embedding the whole document into a single vector produces a blurry
**average** — a query for something on page 12 ranks poorly against that diluted whole-document
vector. PDF ingestion is therefore **"chunk-and-embed"**: split the PDF's text into passages
(chunks), embed each passage, and store **many vectors per source file**. A search hit then points at
*the passage on page 12*, not just "somewhere in this file."

The PDF-reading part is easy. The substance is that this **breaks the brain's "one note = one
vector" assumption**, and that ripples through the cache schema, the sidecar format, hydration, and
search. Build it **source-type-agnostic** so very long Markdown notes can reuse the same chunking
later.

> **Counterpoint worth keeping.** A document's **centroid** (the average of its chunk vectors) *does*
> carry meaning — it is a fine whole-document *summary*, just a poor *retrieval* target for a
> specific passage. That summary-vs-retrieval split is why we chunk for search yet can still use the
> centroid to *characterize* a document. See the meaning-histogram backlog (#37) in
> [quality-features.md](quality-features.md).

## 1. Locked decisions

1. **Bolt-on, not unify.** Notes stay exactly as they are (one row per note); PDF chunks are added
   as a **separate, additive** multi-row entry keyed `(source_file, chunk_id)`. Unifying everything
   under chunking (a short note = a 1-chunk source) is cleaner long-term but forces re-embedding every
   note and changing the note sidecar format — a big migration that would disturb the byte-exact CI
   diff. **Bolt-on keeps the note path untouched**, so PDF support cannot break what already works.

2. **PDFs are NOT committed to Git.** Committing binaries is an anti-pattern. The PDF lives **in the
   vault as-is but git-ignored**, and its derived sidecar is git-ignored too (like every note
   sidecar). **All PDFs will eventually be tracked via Git-LFS** (large-file storage), later.
   *Implication:* until LFS lands, a PDF and its searchable content are **local-only** — they do not
   travel when the brain is cloned to another machine.

3. **Extracted chunk text lives in the git-ignored sidecar, not in Git.** The chunk text must be
   persisted so the keyword index and result snippets have it without re-opening the PDF — the
   cheapest, most consistent home is the same derived sidecar that holds the chunk vectors. Committing
   extracted text would only buy cross-machine portability of PDF *content*, which is exactly what
   LFS (decision 2) will solve — so keep it derived and git-ignored.

4. **Chunking = fixed token-window with overlap, tracking page + char span.** ~512 tokens per chunk,
   ~15% overlap so a sentence spanning a boundary is not lost; each chunk records its **page number**
   and character span so a hit can say "page 12" and the passage can be located. Page-based chunks are
   uneven (pages vary wildly in length); the window is predictable and tunable. Design it
   **source-type-agnostic** (text → chunks), so long notes can reuse it.

5. **Parser = `pypdf`, an optional dependency.** Pure-Python, lightweight, permissive license, no
   system libraries. Shipped in a separate **`requirements-pdf.txt`** (like `requirements-mcp.txt`)
   so the core and the CI gate stay stdlib-lean. Everything degrades cleanly with a clear
   "install `requirements-pdf.txt`" message when the parser is absent.

6. **Ingestion trigger: a manual command now; a hook later.** A manual `add_pdf` command for v1;
   *later* extend the pre-commit hook **for PDF files only**. Wiring PDFs into the auto-hook now would
   make every commit depend on the optional parser being installed, even when only editing a note.

7. **Configurable result shaping + an intra-document mode.** Fuse the meaning (vector) and keyword
   (FTS5/BM25) legs with Reciprocal Rank Fusion at the **chunk** grain, then shape results per a
   config: **`best_per_source`** (one best passage per document, so a big PDF does not flood the
   top-k) or **`all_chunks`**. Plus a separate **within-one-document** top-k mode ("where in *this*
   PDF is X").

8. **No commit, no push on PDF ingestion.** Because the PDF and its sidecar are git-ignored
   (decision 2), the ingestion path just moves a file and builds a local sidecar — **unlike
   `add_note`, there is no commit and no push**, which sidesteps all the git/push complexity.

9. **Selection is folder-first, in one of two UI modes.** When importing, the **first** question is
   *which tracked folder* (enumerated from config, priority-ordered), **then** which PDF in that
   folder, **then** which PARA destination. Because the PDF list depends on the chosen folder, this is
   **sequential** (folder, then PDFs-in-folder) in either UI mode.

## 2. Desktop / client UI — elicitation with a chat fallback

MCP defines an **elicitation** capability (a server asks the client to render a form and return a
structured answer), and `enum` fields are supported — so the folder/PDF/destination choices could be
dropdowns. **But Claude Desktop's Chat surface does not implement elicitation** (it returns an
immediate *cancelled* response with no UI — Anthropic issue #56243, confirmed 2026-07-18). **Claude
Code (the CLI) does** support it (since v2.1.76). Desktop's `roots` support is unconfirmed and is not
relied upon anyway (a local server reads its configured folders directly).

**Design: one shared enumeration core, two presentations, chosen by client capability.**

- **Core (build first):** scan the configured folders, apply the sort + pagination config, build the
  option lists. Pure logic, UI-agnostic.
- **Front-end A — chat (baseline, works everywhere incl. Desktop):** the tool *returns the enumerated
  list as its result*; the user picks in chat (`list_inbox_pdfs()` → "ingest #3 into resources" →
  `add_pdf(path, para_root)`). The chat turn *is* the selection UI.
- **Front-end B — elicitation (the experiment; Claude Code CLI today, Desktop if it ever ships):** the
  same options rendered as an elicitation form.

The server picks the front-end by **capability detection** — MCP clients declare capabilities in the
opening handshake, so the server uses elicitation only if the client advertised it — and **falls back
to chat at runtime** on a `decline`/`cancel` (which is what Desktop does). This is the brain's usual
"detect and adapt, never force" stance; elicitation is a thin, independently-testable add-on over the
fallback, not a hard dependency. *Watch item:* MCP's File-Uploads Working Group / SEP-1306 ("binary
mode" elicitation for file uploads) could later enable a true native file picker — not merged yet.

## 3. Config surface

A new `[pdf]` block in `config/features.toml` (read via `scripts/features.py`, same
`env > config > default` precedence as the existing keys). Proposed keys:

```toml
[pdf]
inbox_dirs     = ["vault/inbox"]  # source folders, priority order (first shown first)
list_sort      = "newest"      # how folder contents are ordered: "newest" | "alphabetical"
list_page_size = 20            # how many entries to enumerate before paginating
chunk_tokens   = 512           # target chunk size (tokens)
chunk_overlap  = 0.15          # fractional overlap between adjacent chunks
result_mode    = "best_per_source"   # "best_per_source" | "all_chunks"
move_from_inbox = true         # move (vs copy) the file out of a source folder on ingest
```

Note the parser itself is an **optional pip dependency** (`requirements-pdf.txt`), not a config key.

### 3.1 `~/Downloads` is deliberately not a default (task #38, 2026-07-20)

`inbox_dirs` originally shipped as `["vault/inbox", "~/Downloads"]`. Downloads is where a user
*actually* has PDFs, so it looked like the helpful default. It was removed, for a reason worth
recording because it will recur for any folder we are tempted to add:

**macOS gates `~/Downloads`, `~/Desktop` and `~/Documents` behind per-app consent (TCC), and the
consent dialog can only be presented to a GUI app with bundle identity.** Our scripts — the CLI,
the MCP server, anything launched from a terminal or by `launchd` — are plain processes. They
inherit whatever the parent was granted and cannot trigger a prompt of their own, so on a machine
where the terminal lacks the grant, the folder is refused outright with `EPERM` and **no dialog
the user could ever say yes to**. The user sees a source folder that reports nothing, and nothing
tells them why.

That combined with the #38 bug (a denial read as an empty folder) made this the worst kind of
default: it pointed at the right place, failed silently, and blamed nothing. #38 fixed the
silence; removing the default fixes the **false promise**. `vault/inbox` lives inside the brain,
is not TCC-protected, and always works.

The lesson generalizes: **do not ship a default that depends on a permission the software cannot
request.** A user can add `~/Downloads` back by hand — and if they do, `doctor.py` reports it as
unreadable and listing it raises, so the failure is now legible. Finder holds the grant and the
user is the consenting party, so *moving the file* is the reliable path, not *reaching for it*.

## 4. Architecture — the bolt-on schema

The whole design is one picture: the PDF side **mirrors the note side, but at *chunk* grain**, and
the note tables are left exactly as they are. Everything above the divider already exists today;
PDF support is purely the block below it.

```
┌──────────────────────── NOTE PATH — UNTOUCHED ────────────────────────┐
│                                                                        │
│   notes  (vec0)                    notes_fts  (fts5)                    │
│   ┌───────────────────────────┐    ┌───────────────────────────┐       │
│   │ source_file  TEXT  ⚷ PK   │    │ source_file  UNINDEXED    │       │
│   │ embedding    FLOAT[768]   │    │ body                      │       │
│   │              cosine       │    │ tags                      │       │
│   └───────────────────────────┘    └───────────────────────────┘       │
│                                                                        │
│        one note  ─────────────►  exactly ONE row in each               │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────── PDF PATH — NEW, ADDITIVE ───────────────────────┐
│                                                                        │
│   pdf_chunks  (vec0)          ← the meaning leg, one row per chunk      │
│   ┌───────────────────────────────────────────┐                        │
│   │ rowid = chunk_rowid   ◄───────────┐        │                        │
│   │ embedding    FLOAT[768]  cosine   │        │                        │
│   └───────────────────────────────────┼────────┘                        │
│                                        │ joined by the SAME rowid        │
│   pdf_chunks_meta  (plain table)       │  ← the human-facing columns     │
│   ┌───────────────────────────────────┼────────┐                        │
│   │ rowid = chunk_rowid   ◄───────────┤        │                        │
│   │ source_file  TEXT     (which PDF) │        │                        │
│   │ chunk_id     INT      (0, 1, 2 …) │        │                        │
│   │ page         INT                  │        │  ← straight from        │
│   │ char_start   INT                  │        │    chunker.Chunk        │
│   │ char_end     INT                  │        │                        │
│   │ text         TEXT                 │        │                        │
│   └───────────────────────────────────┼────────┘                        │
│                                        │ joined by the SAME rowid        │
│   pdf_chunks_fts  (fts5)               │  ← the keyword leg, per chunk   │
│   ┌───────────────────────────────────┼────────┐                        │
│   │ rowid = chunk_rowid   ◄───────────┘        │                        │
│   │ source_file  UNINDEXED                     │                        │
│   │ chunk_id     UNINDEXED                     │                        │
│   │ text                                       │                        │
│   └────────────────────────────────────────────┘                        │
│                                                                        │
│        one PDF  ─────────────►  MANY chunk rows (grouped by source_file)│
└────────────────────────────────────────────────────────────────────────┘
```

**How to read it**

- **The split down the middle is the bolt-on promise.** The note tables' DDL does not change; PDF
  support is only the additive block. That is what keeps the note path byte-exact for CI.
- **A shared `rowid` stitches the three PDF tables into one logical chunk.** Both `vec0` and `fts5`
  tables are keyed by an integer `rowid` and neither holds arbitrary columns well, so chunk *N* of a
  document is its vector in `pdf_chunks`, its metadata + text in `pdf_chunks_meta`, and its
  searchable text in `pdf_chunks_fts` — **all at the same `rowid`**. Search fuses hits from the two
  legs, then looks up page/text by that `rowid`.
- **`source_file` groups a document's chunks.** One PDF fans out to many rows; `WHERE source_file =
  '…'` gives the whole document, which is exactly what the `best_per_source` collapse and the
  within-one-document mode need.
- **`page / char_start / char_end / text` come straight off `chunker.Chunk`** (the M1 output), so M3
  is really "persist what M1 already produces, plus the vector M2 adds."
- **`UNINDEXED` on the FTS columns is deliberate** — `source_file` and `chunk_id` are *stored so a
  hit can be identified, grouped, and deleted*, but are **not tokenized**, so a query term can never
  match a path or an id and skew BM25. Only `text` is searched. (Same rule as `notes_fts`, whose
  `source_file` is UNINDEXED for exactly this reason.)

Concretely, `report.pdf` split into 3 passages lands as three rows in `pdf_chunks_meta` (with three
matching vectors in `pdf_chunks` and three matching text rows in `pdf_chunks_fts`, all at the same
rowids):

```
 rowid │ source_file │ chunk_id │ page │ char_start │ char_end │ text
 ──────┼─────────────┼──────────┼──────┼────────────┼──────────┼──────────────
   41  │ report.pdf  │    0     │  1   │     0      │   2130   │ "Executive…"
   42  │ report.pdf  │    1     │  1   │    1980    │   4025   │ "…continued…"
   43  │ report.pdf  │    2     │  2   │    3900    │   6010   │ "Methods…"
```

**Load and search wiring:**

- `hydrate_cache.py` (full rebuild) and `update_cache.py` (single source) learn to load a PDF's
  **multi-chunk** sidecar into these tables, in the same pass that builds the note tables.
- `search_vault.search()` runs the vector + FTS legs over **both** the note tables and the PDF-chunk
  tables, fuses all candidates with RRF, then applies the `result_mode` collapse (best-chunk-per-
  source / all-chunks) and returns source + page + snippet for PDF hits.

The diagram shows the **rowid-join** option (thin `vec0` table; columns live in `pdf_chunks_meta`),
the natural `sqlite-vec` pattern and the leading choice. The exact layout — this, versus carrying
`chunk_id` directly in the vector table — is finalized in milestone M3.

## 5. Milestones

- **M0 — Lock the design in writing** *(this document)*.
- **M1 — Turn a PDF into clean chunks, provably.** `pdf_extract.py` (pypdf → text + page map) and a
  source-type-agnostic `chunker.py` (text → overlapping token-window chunks with page/char spans).
  Deterministic, model-free, tested against a tiny fixture PDF.
- **M2 — Sidecar format for a chunked source.** A PDF's `.embed.json` holds a *list* of chunks, each
  with `{chunk_id, page, char_start, char_end, text, vector}`, embedded `task="document"`.
  Deterministic on the `test` backend, so a committed fixture sidecar byte-diffs in CI.
- **M3 — Cache schema + hydrate/update for chunks.** The additive parallel tables (§4); hydrate/update
  load PDF sidecars while the note path stays byte-identical.
- **M4 — Search returns a passage.** Chunk-grain RRF, `result_mode` shaping, the within-one-document
  mode, and source + page + snippet in results.
- **M5 — Ingestion engine (CLI).** `add_pdf` — folder-first selection (`inbox_folders`/`list_pdfs`),
  move/copy into `vault/<para>/`, extract → chunk → embed → load the cache, **no commit/push** — plus
  the `[pdf]` config accessors (`pdf_config`) and the passage-fetch (`pdf_search.get_passage`).
  CLI-usable and tested. The MCP/Desktop surface is emitted with the feature at M6 (below).
- **M6 — Emit + Desktop surface + docs + CI + doctor.** Promote the PDF modules `exclude` → `verbatim`;
  register the MCP tools (`list_inbox_pdfs` / `add_pdf` / passage search / passage-fetch) with the chat
  baseline + capability-gated elicitation (§2), and unify passage search into `search_second_brain`;
  add the `[pdf]` block to the emitted `config/features.toml`; an "Add a PDF" README section;
  `requirements-pdf.txt`; a new CI gate (deterministic sidecar fixture + opt-in semantic test); and
  doctor stale-detection parity for PDF sidecars.

## 6. Implementation steps (locked 2026-07-19)

Every step follows the dev loop: **prototype in the golden → `vendor_golden.py` → `build_template.py`
→ `tools/ci.py` green.**

1. Write this doc + a CLAUDE.md pointer. *(M0 — done)*
2. `chunker.py` — pure-stdlib text→chunks (window + overlap, page/char spans) + unit tests. *(M1)*
3. `pdf_extract.py` — pypdf behind the optional dep, graceful "install requirements-pdf.txt" when
   absent; tiny fixture PDF. *(M1)*
4. Chunk-list sidecar writer (`embed_pdf.py` or a generalized embed path); commit a `test`-backend
   fixture sidecar. *(M2)*
5. Schema + hydrate/update for the parallel PDF tables; prove the note path stays byte-exact. *(M3)*
6. Search: chunk-grain RRF, `result_mode`, within-document mode, page/snippet rendering. *(M4)*
7. `add_pdf` engine — folder-first selection + move/copy + extract→chunk→embed→load, `pdf_config`,
   and `pdf_search.get_passage`; CLI + tests. *(M5)*
8. Emit (`exclude`→`verbatim`) + MCP tools (chat baseline + capability-gated elicitation, confirm
   `ctx.elicit`) + unify passage search into `search_second_brain` + `[pdf]` config block + README
   "Add a PDF" + `requirements-pdf.txt` + CI gate + doctor parity. *(M6)*

## Open items / risks

- **Binary bloat** until Git-LFS lands (decision 2); many PDFs will grow the working tree.
- **Optional-dep + CI** — extraction never runs in CI (test backend, no pypdf); coverage is the
  deterministic sidecar fixture + an opt-in semantic test. Confirm "pypdf missing" degrades cleanly
  everywhere.
- **Note-path byte-exactness** through the schema change — the bolt-on promise must be proven, not
  assumed, by the structural-diff gate.
- **FastMCP elicitation + capability-detection API** — verify against the installed version at M5.
