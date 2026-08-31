# The `embed: false` opt-out — task #45

**Not every Markdown file under a PARA root has to be a note.** A file whose frontmatter
carries `embed: false` stays in the vault and stays in git, but is never embedded, never
enters the cache, and never comes back from a search. It is ordinary Markdown that happens
to live inside a PARA root.

Status: **built**, shipped in the golden and emitted into every brain. CI gate 20
(`tools/check_embed_opt_out.py`).

| | Step | What it entails |
| --- | --- | --- |
| ✅ | 1. The parser | `note_view.embed_excluded` — one function, failing open, shared by every consumer. |
| ✅ | 2. Honor it | `embed_staged`, `embed_vault`, `update_cache`, `doctor` skip, retract and report. |
| ✅ | 3. A starting point | `vault/templates/not-a-note.md`, seeded into every brain beside `new-note.md`. |
| ✅ | 4. The MCP surface | `get_note_template(variant)`, `add_note(folder, embed)`, `add_pdf(folder)`. |
| ✅ | 5. Docs | This page, plus both note-gate pipes (`CLAUDE.md`, the template) and the README. |
| ✅ | 6. A gate | Gate 20: polarity, bulk retraction, hook retraction, hydrate, doctor. |

## 1. Why — a project's material had nowhere to live

Whether a file is a note was decided **solely by location**: the four `PARA_ROOTS`. Any
`*.md` under one is walked, embedded, tag-linted, auto-linked and encrypted. There was no
way to keep a Markdown file inside a root without it becoming a searchable note.

That blocks a reasonable organizing pattern. A project is goal-bound and ends, so its note
and its material want to live together — `projects/<project>/` — and archive or delete as
**one unit**. Non-Markdown already colocates safely (every walker globs `*.md`), so the
gap was narrow but real: a project README, meeting scratch, or a half-written draft
silently became a note and diluted retrieval.

Surfaced in the live brain while working out how to record CSET algebra subtests — the
project note and its paperwork trail wanted the same folder.

## 2. The polarity is the whole design decision

**Opt-out, never opt-in.** Embedding stays the default and only an explicit marker
excludes. The two schemes fail in opposite directions, and the costs are wildly asymmetric:

- **Opt-out (built).** A file nobody marked is embedded, so a wrong inclusion **shows up
  in a search result** — visible the first time it matters, and one line fixes it.
- **Opt-in (rejected).** A note nobody marked is *not* embedded, so a wrong exclusion is
  **indistinguishable from a note that was never written**. You find out on the day you
  search for it and get nothing — which is also the day you conclude the brain is
  unreliable.

A stray hit costs a second of attention. An invisible note costs the note. This repo
already errs the wrong way once — a note in a non-PARA folder disappears with no warning —
and the rule that follows from it is *do not add a second way to do that*.

The same asymmetry decides how the parser handles anything it does not understand: it
**fails open**. A missing key, a typo (`fasle`), a value it cannot parse, an unterminated
frontmatter, or the key merely *mentioned in prose* all mean **embed**. Only a literal
`false`, `no` or `off` — case- and quote-insensitive — excludes.

This is the property most at risk of quiet inversion by a later "tidy-up" of the parser
(`return value not in ("true", …)` looks equivalent and is the exact bug), which is why
gate 20 asserts the fail-open cases directly rather than trusting the suite alone.

## 3. Retraction — the failure that looks like success

Adding the key to a file that was **already embedded** must remove its sidecar, its
vector, and its search row — not merely stop refreshing them. Left in place, a stale
sidecar keeps being hydrated into the cache, so the file goes on answering searches while
its frontmatter says it is not a note. The exclusion *appears* to work.

Two independent mechanisms cover the two ways a file gets re-processed, and they are not
interchangeable:

- **The commit path.** `update_cache.changed_in_commit` moves an excluded note onto the
  **DELETE** side rather than dropping it from the upsert list. Dropping it would leave
  the row in place; routing it to delete removes the row *and* unlinks the orphan sidecar.
  Routing also avoids a second bug: `upsert()` raises `SystemExit` on a note with no
  sidecar, which would abort the whole post-commit run.
- **The bulk path.** `embed_vault` calls `embed_staged.drop_sidecar`, because nothing
  follows a bulk re-embed to clean up after it. This is the *only* place that drop is
  load-bearing — on the commit path `update_cache.delete()` already unlinks the sidecar —
  and a gate that exercises only the hooks will pass with `drop_sidecar` gutted. Gate 20
  drives both.

Retraction is reversible: delete the key and the next commit puts the file back in the
brain. A one-way opt-out would make a mistake unrecoverable without a manual rebuild.

## 4. Where it is honored

One projection, four consumers — the same shape as the no-embed block (see
[embed-excluded-block.md](embed-excluded-block.md)):

| Consumer | Behavior |
| --- | --- |
| `embed_staged.py` (pre-commit) | Skips the file; drops a stale sidecar; prints which files it excluded. |
| `embed_vault.py` (bulk) | Same, and the summary line states the excluded count instead of just a smaller total. |
| `update_cache.py` (post-commit) | Routes excluded notes to the delete side (§3). |
| `doctor.py` | Excludes them from `para_notes()` — otherwise every one reads as a note missing its sidecar, and `--repair` would embed the very files the key exists to keep out — and **reports the count**. |

`hydrate_cache.py` needs no change: it rebuilds from sidecars, and an excluded file has
none. That is a consequence worth stating rather than assuming, so gate 20 asserts it.

**Everything is reported.** An exclusion nobody can see is the same failure as a silent
one, just relocated into the report: the note count simply comes out smaller than the file
count with nothing explaining the gap. So `embed_vault` names the count in its summary and
`doctor` lists the first few files by name.

## 5. The template variant

`vault/templates/not-a-note.md` ships beside `new-note.md`, seeded into every brain from
`seeds/templates/`. It carries the key, explains the polarity, and documents the naming
convention below. Same reason `new-note.md` exists: the excluded case deserves a starting
point rather than being hand-rolled from a docs page.

It deliberately has **no `tags:` key**. Tags are a note's controlled vocabulary; a file
that is not a note has no business joining it.

Note that `vault/templates/` is not a PARA root, so the key is inert where the template
sits — it only starts doing work once the file is copied into a root.

## 6. The colocation pattern this exists to enable

**Recommended, never enforced.** No script checks any of it, and `doctor.py` should not
grow a rule for it: a one-note project with nothing to colocate is a legitimate exception,
and a warning people learn to ignore is worse than no warning.

```
vault/projects/algebra/algebra.md            <- the entry note (embedded)
vault/projects/algebra/algebra--progress.md  <- material (embed: false)
vault/projects/algebra/practice-test-1.pdf   <- non-Markdown already colocated fine
```

- **The entry note repeats the folder name.** It looks redundant and it is the only form
  that works. Obsidian resolves `[[wikilinks]]` by **name**, so `[[algebra]]` keeps
  resolving after the folder moves to `archive/`, and every note title in the vault stays
  unique. A per-folder `index.md` or `README.md` would put many identically-named notes in
  one vault, breaking wikilink resolution and making search results unreadable.
- **Everything else is `{folder}--{descriptor}.md`.**
- **Folder names carry no `project-` prefix.** The folder's destination is `archive/`, and
  a prefix naming its old status goes stale there.
- **A durable lesson does not live in a project folder.** It goes in `resources/`, flat. A
  project folder holds what dies with the project; burying what outlives it in a folder
  headed for `archive/` is how it becomes unfindable.
- **Subfolders belong in `projects/`.** A resource is filed by topic and an area does not
  end, so neither has the "archive as one unit" motive that justifies nesting.

This depends on PARA roots being walked **recursively** — true of every walker since long
before this feature, and documented nowhere until task #46.

## 7. The MCP surface

Three tools were affected; one of them failed silently, which made it the priority.

- **`get_note_template(variant="note" | "not-a-note")`.** It returned only `new-note.md`,
  so once the variant shipped an MCP client had no way to reach it and **every note an
  assistant created would embed** — the client locked out of the opt-out entirely. That
  fails *silently*: a plausible embedded file appears. Contrast the folder gap below,
  which fails loudly by refusing.
- **`add_note(..., folder="", embed=True)`.** It hardcoded `VAULT/para_root/<slug>.md` and
  asserted the parent, so it refused subfolders outright. Arguments rather than a separate
  `add_project` tool: a second writer would duplicate the whole write path (slugify,
  refuse-overwrite, encrypt, commit, push) to save one argument. Its one real advantage —
  *enforcing* folder-name == entry-note-name — belongs with the deferred pre-commit
  checks, not in a parallel writer.
  With `embed=False` the tool also stops shouting: the "committed but NOT embedded" warning
  exists to catch missing git hooks, and firing it on a file excluded **on purpose** would
  train the user to ignore the one message that matters when the hooks really are off.
- **`add_pdf(..., folder="")`** and `scripts/add_pdf.py --folder`. It hardcoded
  `dest_dir = VAULT_DIR / para_root`, so a PDF could not be colocated in a project folder —
  the exact case colocation exists for.

`get_note`, `search_second_brain` and `list_vault` already worked with subfolders
unchanged (path-based, or `rglob`).

**On the folder validator being written twice.** `mcp_server._safe_folder` and
`add_pdf._FOLDER_RE` state the same rule in the two places that turn caller input into a
path. A shared helper would make the note writer import the PDF module (or invent a module
for six lines); two consumers is not yet a pattern, and the codebase already states
`PARA_ROOTS` ten times. Both are strict allow-lists — a segment must start `[a-z0-9]`, so
`..` cannot match and no traversal payload survives — and both refuse loudly rather than
silently rewriting a bad folder into a good one: an assistant that gets a clear error can
correct itself, whereas a silently relocated file is found later, somewhere else, by a
human.

## 8. Known boundaries

Deliberately out of scope, and worth naming so they are not mistaken for oversights:

- **`tag_hygiene.py` / `tag_lint.py` still read an excluded file's tags.** The shipped
  template has no `tags:` key, so nothing leaks in practice, but a hand-written excluded
  file with tags would contribute to the vocabulary.
- **`glossary_autolink_staged.py` will still auto-link terms in an excluded file.** Off by
  default. The coherent position is that a file that is not a note should not be rewritten
  by note tooling.
- **`encrypt_vault.py` is location-based** and encrypts an excluded file like any other.
  That is almost certainly right — the file is still the user's content and still
  committed — but it is a choice, not an accident.
- **`autolink.py` needs no change**: it works off vectors, and an excluded file has none.
- **Moving a file into or out of a folder** is broken independently of this feature —
  `git mv` is invisible to the pre-commit selector and orphans the sidecar (task #47). The
  archive half of the colocation workflow is a move, which is how it surfaced here.

## 9. Provenance

Prototyped in the live golden (`second-brain-test`) commits `77eae1b`, `b08aa98`,
`ddc3af9`, `f6a081e` (parser + the four consumers) and `d970a46` (template variant, MCP
surface, docs), then productized into the devkit. Plan entry: PLAN.md, "Embed opt-out
(task #45)".
