# Partial-commit index poisoning — the `add_note` bug (task #28)

**Status:** FIXED 2026-07-14 (golden `9a36850`). **Awaiting user review — see §6.**
**Severity:** silent **content corruption**. It reverted a note's body in a live brain, in a commit
that never touched that note. Nothing errors; nothing warns.

---

## 1. The symptom

A commit adding a *new* note also silently reverted a wikilink in a **different, unrelated** note:

```diff
-Asked to define `[[ablation]]`, an assistant searched the semantic index …
+Asked to define `ablation`, an assistant searched the semantic index …
```

Nobody edited that file. It was not staged by the committer. It appeared in the commit anyway,
with the glossary link removed — undoing work a hook had done earlier.

## 2. The mechanism (this is the part worth understanding)

Three correct-looking things combine into a bug:

1. **`add_note` commits with a pathspec** — `git commit -m … -- vault/resources/foo.md`. This is
   deliberate and *right*: it is what guarantees an agent can never sweep the user's in-progress
   work into a commit it authored. It is the central safety property of the write path.
2. **A pathspec commit is a *partial commit*.** Git cannot use the real index (it holds staged
   changes the user did *not* ask to commit), so it **builds a temporary index** containing only
   HEAD plus the pathspec'd paths, and exports it to hooks via `GIT_INDEX_FILE`.
3. **The pre-commit hook edits the note and re-stages it.** With `glossary_autolink = true`, the
   hook links known glossary terms in staged notes and runs `git add` so the note is committed
   *with* its links. That `git add` writes to `GIT_INDEX_FILE` — **the temporary index**.

The commit is therefore **correct**: the tree contains the linked note. But the **real index was
never updated** — it still holds the blob staged in step 1, i.e. the note *before* the hook linked
it. The user's index now contains a **staged revert** of the hook's edit.

Nothing surfaces this. `git status` shows a modified file; a human reads that as "the hook touched
it" and thinks nothing of it. The stale entry then rides into **the next commit anyone makes** —
by a person, or by Claude Code adding an unrelated note — and quietly un-links the term.

```
  add_note                                       next commit (anyone)
  ─────────────────────────────────────────────  ─────────────────────────
  git add      -- foo.md   → REAL index: v1      git add unrelated.md
  git commit   -- foo.md   → temp index: v1
      pre-commit hook links term, git add
                           → TEMP index: v2      git commit
      commit created from TEMP index  ✅ v2        → commits REAL index,
  REAL index still holds ................ v1        which still says v1  ❌
                                                    → the link is reverted
```

## 3. The fix

Re-sync the real index to what was just committed, immediately after the partial commit:

```python
_git("add", "--", rel)
_git("commit", "-m", f"note: add {title}", "--", rel)
_git("add", "--", rel, check=False)   # ← the missing step
```

**Keep the pathspec.** It is not the bug; it is doing its job. The missing step is the refresh.
A no-op when no hook touched the file.

**Generalises:** *any* tool that does a partial commit while file-modifying hooks are installed
must re-sync the real index afterwards, or it leaves a staged revert of the hook's work behind.

## 4. Why the test suite missed it — the real lesson

`glossary_autolink` **defaults to `false`**. The golden, the template, and every harness run
therefore execute with **the only hook that edits a staged note switched off**. The `add_note`
write suite — which explicitly asserts that the tool never sweeps up the user's staged work — passed
for exactly this reason: *the condition that triggers the bug never occurred in the tests.*

**A test matrix that only exercises the default configuration does not test the product.** Every
non-default toggle is a code path with no coverage, and the bug will be found by the user, in
their brain, on their data. Generalised as task **#29**.

## 5. The regression test (now in `check_mcp_server.py`)

- The write suite's brain is created with **`glossary_autolink = true`** (the non-default config).
- The note body mentions a planted glossary term, so the hook *does* edit and re-stage it.
- After `add_note`: **`git diff --cached` must be empty** — no phantom staged change.
- Plus an anti-vacuity check: the committed note must actually contain `[[ablation]]`, proving the
  hook ran. Without it, the index assertion would pass trivially on a config where nothing edits.
- **Negative-tested:** removing the one-line fix turns the tier red with
  `add_note left a POISONED INDEX`.

## 6. For review (@david — this is the item to look at when you have time)

Confirm you agree with each of these; they are the load-bearing judgements, not the code:

- [ ] **The pathspec commit stays.** Alternative would be committing the whole index (simpler, no
      temp index, no bug) — but then an agent's commit could contain the user's unrelated staged
      work. The bug was worth having; the safety property is worth keeping.
- [ ] **The fix is a post-commit index refresh**, not a change to the hook or to the commit
      strategy.
- [ ] **The blast radius is bounded**: only notes a file-modifying hook touched, only with a
      non-default toggle on. Brains with `glossary_autolink = false` (the default) were never
      affected.
- [ ] **Anything already corrupted?** In the real brain, one link was reverted and has been
      restored. Worth a `git log -p vault/` skim if you want certainty for other notes — the
      signature is a commit that removes `[[…]]` from a note it otherwise doesn't touch.
