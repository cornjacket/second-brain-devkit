# Moving a note — task #47

**Archiving a note used to remove it from the brain.** A `git mv` with no content edit was
invisible to the pre-commit hook, so nothing re-embedded the note at its new path; the
post-commit cache update then deleted the old row and died on the missing sidecar. The
commit succeeded. The note was gone from search.

Status: **fixed**, shipped in the golden and emitted into every brain. CI gate 21
(`tools/check_note_move.py`).

## 1. `R` — the letter that was missing

Git labels every staged change with one status letter:

```
M	alpha.txt              M = Modified
D	beta.txt               D = Deleted
A	delta.txt              A = Added
R100	gamma.txt  moved.txt   R = Renamed (100 = content 100% identical)
```

`--diff-filter=<letters>` is a **whitelist** of those letters. The selector asked for
`ACM` — Added, Copied, Modified — so the `R` entry matched nothing:

```
$ git diff --cached --name-only --diff-filter=ACM
alpha.txt
delta.txt          <- moved.txt is absent. It is an R.
```

The whole fix is one character, `ACM` → `ACMR`. For an `R` entry `--name-only` prints the
**destination** path, which is exactly the path that needs embedding; the old path is left
to `update_cache`, which already understood renames.

## 2. Why there was no user-side workaround

The obvious workaround — don't use `git mv`, move the file and stage it by hand — does not
work, and it is worth knowing why rather than rediscovering it:

- `git mv` **is** `mv` + `git rm` + `git add`. It records nothing extra.
- Rename detection happens at **diff** time, not at add time, and `diff.renames` defaults
  to true (git ≥ 2.9). Git looks at the staged delete+add pair and infers `R100` either way.

So both routes produce an identical index and an identical answer from the selector. This
also rules out the other tempting fix — a `move_note.py` wrapper that does the right thing.
A wrapper only helps people who remember to call it, `git mv` is what people type, and
**Obsidian moves notes through its own file explorer** without calling anything a brain
ships. The hook is the only choke point every route passes through.

## 3. The two modes disagreed, and only one of them was wrong about `R`

| | plaintext | encrypted |
| --- | --- | --- |
| Re-embed at the new path | **was broken** (`ACM` dropped the `R`) | already correct |
| Remove the vector at the old path | correct (`update_cache.delete()` unlinks it) | **was broken** |
| `git mv` usable at all | yes | **no** — the vault is git-ignored, so the source is "not under version control" |
| Cache updated on commit | yes | no — see §5 |

The encrypted path was immune to the `R` bug for a reason worth keeping: task #42 made it
stop asking git what changed and read the working tree instead, because a git-ignored vault
cannot answer. It was wrong about the *other* half — nothing removed the sidecar abandoned
at the old path, since the post-commit update only ever sees an opaque blob, never a PARA
note.

That orphan is not cosmetic. `hydrate_cache` rebuilds **from sidecars**, so it reads the
abandoned vector and inserts a row for a file that no longer exists — search then answers
with a dead path, alongside the live one. `embed_staged.prune_orphan_sidecars()` sweeps
them, which is what makes the two modes agree. A sidecar under a PARA root with no note
beside it is always garbage: it is derived, so there is no case where keeping one is right.

## 4. Recovery advice that reported success without fixing anything

The post-commit hook caught its own failure and printed:

> run `python3 scripts/hydrate_cache.py` manually to make new notes searchable

That advice cannot work. Hydrate rebuilds the cache **from sidecars**, and the sidecar is
precisely what is missing. Running it prints a cheerful `hydrated 4 note(s)` and leaves the
note exactly as unsearchable as before.

**Advice that reports success without fixing anything is worse than no advice** — the user
stops looking. The hook now names `doctor.py --repair`, which re-embeds what has no sidecar
and *then* rebuilds, covering both causes. Verified: `--repair` restores the moved note;
`hydrate_cache` does not.

## 5. Found while fixing this, filed separately

**An encrypted brain never updates its cache on commit at all.** The commit contains
`enc/<opaque>.md.enc`, not a PARA note, so `update_cache --from-commit` reports "no PARA-note
changes" and exits clean. The note is embedded but not searchable until someone runs
`hydrate_cache` by hand — which contradicts the promise stated in the README and `CLAUDE.md`
that a committed note is searchable immediately.

Same class as #47 and as the four selectors #42 had to fix: **a component asking git a
question a git-ignored vault cannot answer.** Not folded in here, because the fix is a design
choice (teach `update_cache` to map blob → path, or have it fall back to the working tree)
rather than a letter in a filter. Tracked as its own task; gate 21 deliberately does not
assert the encrypted cache, so this gate's green never implies that gap is closed.

## 6. What the gate pins

Three scenarios, because they run through different code:

- one note moved between PARA roots — the plaintext selector;
- a whole project folder archived in one `git mv` — the workflow the `embed: false`
  colocation pattern exists for ([embed-opt-out.md](embed-opt-out.md)), and the first thing
  that depended on moves working;
- the same move on an encrypted brain — plain `mv`, asserting the re-embed, the dropped
  blob, and that hydrate does **not** resurrect the old path.

The assertion is the end-user promise — the note is **searchable at its new path** — not
merely that a row exists somewhere.

Five unit tests in `tests/test_note_selection.py` cover the selector itself; three of them
go red against the old `ACM` filter. The other two are guard rails against over-correcting:
a `D`eleted note must still *not* be selected (removal is `update_cache`'s job, not the
embedder's), and a note moved out of the PARA roots — into `vault/templates/`, say — has
left the embedding scope and must not be embedded at its destination.

## 7. Provenance

Prototyped in the live golden (`second-brain-test`) commit `43bc5ff`, then productized.
Plan entry: PLAN.md, "Moving a note breaks its index entry (task #47)".
