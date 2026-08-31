# An encrypted brain's cache, on commit — task #48

**On an encrypted brain, a committed note was embedded but not searchable.** The README and
the emitted `CLAUDE.md` both promise that committing a note makes it searchable immediately,
with no manual step. That was true in plaintext and false under encryption, and nothing said
so.

Status: **fixed**, shipped in the golden and emitted into every brain. CI gate 22
(`tools/check_commit_indexes.py`).

## 1. Every signal said success

This is what made it hard to see. Walk the commit:

- the pre-commit hook **really did** embed the note and write its sidecar;
- `encrypt_vault --precommit` **really did** write and stage the blob;
- the commit **really did** land;
- the post-commit hook **really did** run, print `no PARA-note changes in HEAD`, and **exit 0**.

Nothing failed. The note was simply absent from `data/brain.db` until someone ran
`hydrate_cache.py` by hand.

The cause: `update_cache --from-commit` asks `git diff-tree` what the commit touched. With
encryption on, the vault is git-ignored and the commit contains only
`enc/<opaque>.md.enc` — so `is_para_note` rejects every path and the answer is, truthfully,
nothing.

**This is the third instance of one shape.** Task #42 found four selectors that went blind
the same way; task #47 a fifth (`--diff-filter=ACM` dropping renames). The recurring lesson
is not about any one call site:

> A git-ignored vault answers "what changed?" with an empty list, not an error. An empty
> answer is indistinguishable from a quiet, correct no-op — so the failure is silent by
> construction. Every `git diff`-shaped question in this repo is a candidate.

An audit of every such call in the emitted scripts was run while fixing this, and it found
no remaining blind ones: `encrypt_vault`'s `ls-files` / `diff --cached` and `doctor`'s
`ls-files vault` legitimately ask about **blobs**, which are tracked.

## 2. Resolved forwards, not backwards

A blob's name is a keyed HMAC of the note's path, so the path **cannot** be recovered from
the name. The fix does not try:

- **Upserts.** Compute every *live* note's blob name — a pure function of the path — and
  intersect with the blob names this commit touched. No decryption, no reverse mapping. It
  is the same trick `encrypt_vault.orphan_blobs` already uses.
- **Deletes.** A deleted note's name cannot be computed, because the note is gone. Rather
  than decrypt the old blob out of git history to recover its path, the deletion half asks a
  cheaper question with a better answer: **which cache rows name a file that is not on
  disk?** That needs neither git nor the keys, works in both modes, and also catches a note
  removed outside a commit entirely.

The incremental property survives — only changed rows are touched, the cache is never torn
down, so a concurrent query is never served an empty database.

## 3. Blind must be loud

If the keys cannot be derived (no passphrase, missing `cryptography`, unreadable keyfile),
`encrypted_changes` raises rather than returning `[]`, and `update_cache` prints what
happened and exits non-zero:

```
update_cache: encryption is on but the keys could not be derived (…) —
this commit's notes are NOT in the search cache. Run 'python3 scripts/doctor.py --repair'.
```

Returning `[]` there would reproduce the original bug exactly: an empty list is
indistinguishable from "this commit changed nothing". The distinction *is* the fix.

In practice this path is reached sideways — without a passphrase the **pre-commit** hook
refuses the commit outright (a #42 deliberate choice), so the post-commit hook rarely gets a
chance. It is asserted anyway, because it is the behaviour the whole fix turns on.

## 4. What the gate pins

Gate 22 runs the full lifecycle in **both** modes, because each step goes through different
code:

```
create → search finds it
edit   → the lexical row holds the NEW wording and not the old
move   → search finds it at the new path, and the old row is gone
delete → search stops finding it
```

Two deliberate choices in how it asserts:

- **The claim is the user-visible one** — `search_vault` returns the note — not "a row
  exists". A row is an implementation detail; being findable is the promise that was broken.
- **Except for the edit.** Search always returns the top *k*, because a KNN ranks every row
  no matter what was asked, so "absent from the results" is only meaningful for a row that is
  genuinely gone. Proving an edit landed therefore reads the FTS row directly. (Written the
  other way first, it failed against correct code — the assertion was wrong, not the fix.)
- The encrypted half **skips loudly** when `cryptography` is absent, naming that the half
  which was broken went unexercised, rather than letting a skip read as coverage.

## 5. Provenance

Surfaced while building gate 21 for task #47 — that gate's encrypted scenario could not
assert the cache, which is how the gap became visible. Prototyped in the live golden
(`second-brain-test`) commit `de8be8d`, then productized. Plan entry: PLAN.md, "Encrypted
brains never update the cache on commit (task #48)".
