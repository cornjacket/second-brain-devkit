# The `lexical-only` fence — task #55

**A region can now leave the vector while staying in keyword search.** Reference data — IDs,
phone numbers, account names, contact lists, volatile checklists — is fenced between
`<!-- second-brain:lexical-only:begin -->` and `<!-- second-brain:lexical-only:end -->`.

Status: **built**, shipped in the golden and emitted into every brain. CI gate 24
(`tools/check_lexical_fence.py`).

## 1. Why one fence was not enough

Search is **hybrid**: BM25 over an FTS5 index, fused with a vector KNN by Reciprocal Rank
Fusion. The two halves are good at different things — and until now, one marker excluded a
region from both, because `update_cache.index_fts` indexed `canonical_body(text)`, the same
projection the embedder uses.

That was deliberate in [#39](embed-excluded-block.md) and correct for what #39 was about:
ASCII art has no meaning to retrieve by, so keeping it out of keyword search too is right.

It is wrong for reference data. **An identifier is a token, not a meaning.** `REG-066388` has
no neighbours in embedding space — it dilutes the vector and contributes nothing to similarity
— while being exactly the kind of thing BM25 nails. Sending it to the lexical half *only* plays
to both halves' strengths.

Found on a real note. `substitute-permit.md` had reached **1722 of 1800** embed tokens — one
paragraph from failing to embed at all. Fencing its four operational sections brought it to
857 and made checkbox edits free, but it also took `TRDS92FI`, `408-453-6767` and the CTC
username out of keyword search. That loss is what this fence undoes.

## 2. Two fences, three cases

| Case | Example | Vector | Keyword | Fence |
| --- | --- | --- | --- | --- |
| Decorative | ASCII art, diagrams | out | out | `no-embed` |
| Reference data | IDs, numbers, contacts | out | **in** | `lexical-only` |
| Volatile status | checkboxes, progress tables | out | **in** | `lexical-only` |

Cases 2 and 3 want the same treatment, so this is **one** new fence, not two. Status text is
worth finding by keyword ("TB test" is a real query) and its *state* carries no semantic change,
so churning it should never touch a vector.

## 3. Narrowness is the safety argument

`lexical_body()` differs from `canonical_body()` in **exactly one** way: `lexical-only` blocks
are kept. Frontmatter, line endings, `no-embed` blocks, asset filenames and wikilink brackets
are all handled identically.

That is deliberate and it is the whole defence. #39's lesson was that the embedding, the content
hash and the lexical index disagree the moment they are computed from different projections —
excluding at the embed call rather than in `canonical_body()` would have made a redrawn diagram
both re-embed the note *and* report it stale forever. One documented difference is auditable;
two is where drift starts. Gate 24 asserts it directly: a note with no `lexical-only` region
must project **byte-identically** through both.

The nastiest coupling is untouched. The vector and the content hash both still come from
`canonical_body`, so they cannot diverge.

**Both FTS writers share the new projection** — `update_cache.index_fts` and
`hydrate_cache`. Those two disagreeing would mean a row's contents depended on which path last
touched it, which is the same failure one level down.

## 4. Why editing inside the fence is free

The region is outside `canonical_body`, so it is outside the **content hash** — and
`write_sidecar` skips re-embedding when the hash is unchanged. Meanwhile `index_fts` runs on
**every** upsert, independent of that gate.

So the lexical row is rewritten on every commit while the vector never moves. Ticking a checkbox
or correcting a phone number re-indexes without re-embedding. That combination is the feature,
and it falls out of machinery that already existed rather than needing new plumbing.

## 5. Fences do not nest

One layer only, of either kind. Nesting has no useful meaning here — an inner fence could only
repeat or contradict the outer one — and forbidding it makes validity checkable in a **single
pass** over the markers in document order: they must strictly alternate, and an `end` must close
the fence that is open.

That also catches **interleaving** (`no-embed:begin`, `lexical-only:begin`, `no-embed:end`,
`lexical-only:end`), which balances by count and is still meaningless. A count-based check would
call it fine.

`note_view.fence_errors()` is the one validator, shared by `scripts/check_fences.py` and the
pre-commit hook's warning — the scanner and the hook disagreeing about what "valid" means would
be this feature's own central risk, one level down again.

## 6. A broken fence is refused, not warned

The pre-commit hook **blocks** on a malformed fence, unlike the neighbouring line-count guard.
A fence that never closes excludes **nothing**: the note commits, renders correctly in Obsidian
(the markers are HTML comments either way), and quietly carries into the index exactly what the
author fenced off. Nothing else in the system would ever mention it.

The same reasoning as the uniqueness hook — the damage is silent and the fix is a one-line edit
at the moment you are already looking at the file.

```
python3 scripts/check_fences.py            # every note under the PARA roots
python3 scripts/check_fences.py a.md b.md  # just these
```

## 7. Provenance

Proposed by review rather than found by a failure: the design was filed as task #55 and
reviewed before any code was written. Prototyped in the live golden (`second-brain-test`), then
productized. Plan entry: PLAN.md, "Fence a region out of the VECTOR but keep it lexically
searchable (task #55)".
