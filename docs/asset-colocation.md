# Colocating an asset with its note — task #50

**A note and the material it displays now live in the same folder.** `projects/algebra/chapter-1/`
holds `chapter-1.md` and `tile-pattern-cpm-source.svg`, and the whole folder archives or deletes
as one unit.

Status: **built**, shipped in the golden and emitted into every brain. CI gate 23
(`tools/check_asset_colocation.py`).

| | Step | What it entails |
| --- | --- | --- |
| ✅ | 1. `subpath` | `add_note`/`add_pdf` nest under `projects/` and `archive/` only. |
| ✅ | 2. `add_asset` | A separate tool: verbatim filename, never embedded, refuses an orphan. |
| ✅ | 3. Uniqueness | Pre-commit check refusing duplicate note basenames vault-wide. |
| ✅ | 4. Vector hygiene | Asset filenames cut from the embed input; alt text kept. |
| ✅ | 5. Docs + gate | Both note-gate pipes, the README, and gate 23. |

## 1. Two tools, not one

The tempting shape is one `add(filetype=...)`. It was rejected, and the reason generalises.

An asset is a **sub-feature of a note, not a peer of it**: it needs the note to be meaningful,
and an orphaned asset or a broken image reference makes the other one wrong. Run the
orthogonality test from [[orthogonal-features-not-nesting]] — does enabling one change the
correctness of the other? Yes. Does one require the other? Yes. That is not a 2×2; it is a
parent and a child.

Mechanically, a merged tool would branch on `filetype` for frontmatter, the H1, kebab-case
renaming, the "what earns a note" gate, and whether to embed — **five behaviours on one
parameter**, which is the shape of two functions sharing a name. A `filetype`/`encoding`
parameter *inside* `add_asset` is fine, and exists: that is one level down, where the branches
really do share a model.

## 2. Where nesting is allowed, and why not everywhere

`subpath` works under **`projects/` and `archive/` only**. Both other roots refuse, with an
error that says why.

The motive for nesting is *archive-as-one-unit*: a project is goal-bound, it ends, and when it
does you want to move one folder. A **resource** is filed by topic and is found by search, so
nesting only buries it. An **area** never ends, so it never has a moment where moving it as a
unit makes sense. Without that motive a subfolder is pure cost — a deeper path, a less findable
note, and one more place to look.

`archive/` is included because it is where a finished project folder lands, and a destination
you cannot write to is not a destination.

## 3. Every folder carries an entry note — at every level

`projects/algebra/algebra.md`, and `projects/algebra/chapter-1/chapter-1.md`. The rule
**recurses** (decided 2026-08-30).

It looks redundant and it is the form that works: Obsidian resolves `[[wikilinks]]` by **name**,
so `[[chapter-1]]` keeps resolving after the folder moves to `archive/`. A per-folder `index.md`
or `README.md` would put many identically-named notes in one vault, which breaks both wikilink
resolution and readable search results.

**The slug rule bites here, and it is easy to trip over.** `add_note(title="Chapter 1")`
produces `chapter-1.md`, so the folder must be `chapter-1/`, not `chapter1/`. Name folders as
the entry note's title slugifies. `add_note` emits a `FOLDER HINT` when it writes into a folder
that has no matching entry note — advisory, never a refusal, because a one-note folder is a
legitimate exception and a rule that refused would train people to fight the tool. Silence would
be worse than either: nothing else in the system would ever mention the convention.

## 4. Uniqueness was an accident; now it is a rule

Obsidian resolves `[[wikilinks]]` by basename. Every note in the vault had a unique filename —
but nothing *decided* that. Notes sat directly in a PARA root, and a directory cannot hold two
files of one name, so the filesystem handed uniqueness over **within** each root. Across the
four roots it was held up by naming habit across a few dozen hand-written notes.

Subfolders remove the accident silently. `projects/algebra/test-1.md` and
`projects/geometry/test-1.md` are two valid, different paths: `add_note`'s refuse-to-overwrite
check passes, git is happy, nothing fails. Every `[[test-1]]` in the vault is now ambiguous,
Obsidian picks one, and the other is unreachable by link.

Per [[emergent-properties-are-not-invariants]], the fix for a load-bearing property with no
mechanism is a mechanism: `scripts/check_unique_names.py`, run by the pre-commit hook.

**It blocks the commit rather than warning**, which is the opposite of the neighbouring
line-count guard, and deliberately so. A long note is visible the moment you open it; a
misrouted link is invisible at the time and gets attributed to Obsidian months later. The fix is
always a rename, always local, and always cheapest at the moment you are already thinking about
the file.

The check considers notes only. Two `tile.svg` files in different project folders are fine — a
relative image link resolves by *path*, so assets have no uniqueness requirement at all.

## 5. Assets never embed — twice over

**The file.** Only Markdown is eligible, and that is structural rather than a flag: every walker
over a PARA root globs `*.md`. It has always been true, which is why the `embed: false`
frontmatter opt-out ([embed-opt-out.md](embed-opt-out.md)) was never the mechanism for this —
SVG and PNG have no frontmatter, so a frontmatter flag could not reach them even in principle.
Per [[embed-the-substance-not-the-file]], SVG is XML: markup, not meaning, and embedding it
would fill the vector with tag soup.

**The reference.** This is the part that was leaking. `![alt](tile-pattern.svg)` put
`tile-pattern.svg` into the *note's* embedding — so notes that display diagrams started
resembling each other by how their files were named rather than by what they said. Same category
as the `[[ ]]` brackets `canonical_body` already strips. `strip_asset_links` now removes the
target and **keeps the alt text**, because a human wrote that to describe the picture and it is
often the only description of the diagram the embedder will ever see.

Which is a reason to write `![a tiling of the plane](tile.svg)` rather than `![](tile.svg)`: the
alt text is what makes the image findable at all.

One consequence worth knowing: this changes the canonical view of any existing note that
references an asset, so `doctor` will report those notes stale and `--repair` will re-embed
them. That is correct — their vectors really were polluted — but it is not a no-op upgrade.

## 6. Which image syntax to use

```markdown
![a tiling of the plane](tile-pattern.svg)   <- use this
![[tile-pattern.svg]]                        <- works in Obsidian only
```

Both render in Obsidian. The difference is how the file is found: `![[ ]]` searches the vault
**by name**, the relative form resolves **by path**.

Prefer the relative form for two reasons. It renders on GitHub, and it does **not** depend on
the filename being unique — which matters because the entry-note convention already spends the
vault's one basename namespace on notes. Its weakness (it breaks if the note and image are
separated) does not apply here: the whole colocation design is that the folder moves as a unit.

## 7. What `add_asset` refuses

- **An orphan** — no note in the target folder. Nothing embeds an asset, nothing links it, and
  search cannot return it, so an asset with no note is invisible the moment you forget it is
  there. This is the failure mode the note/asset coupling in §1 predicts, so the tool is the
  right place to prevent it. Call `add_note` first.
- **A `.md` filename** — that is a note; `add_note` gives it frontmatter, an H1, and a place in
  the index.
- **A path in `filename`** — the name is used verbatim (the note's reference must match it), so
  it is validated as one bare segment with an extension. The location goes in `subpath`.
- **An overwrite** — same rule as `add_note`.
- **An encrypted brain.** The vault is git-ignored and only `*.md` is encrypted, so an asset
  would reach **no commit in any form** — see [task #49](encrypted-commit-indexing.md) and the
  PLAN entry. Refusing beats reporting "committed and pushed" while pushing nothing; that exact
  silent-success shape has had to be fixed three times already this month.

## 8. Provenance

Prototyped in the live golden (`second-brain-test`) commit `e442c74`, then productized. Plan
entry: PLAN.md, "Colocate assets with notes (task #50)". Blocked-on: task #49 for the encrypted
case.
