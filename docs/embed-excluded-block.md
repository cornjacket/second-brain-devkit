# The embed-excluded (`no-embed`) block — task #39

**A note can now carry decorative content that the reader sees and the embedder never
does.** A region fenced between `<!-- second-brain:no-embed:begin -->` and
`<!-- second-brain:no-embed:end -->` is stored in the file verbatim, renders normally in
Obsidian, and is cut from the *canonical view* — so it is excluded from the embedding,
the content hash, and the lexical index alike.

Status: **built**, shipped in the golden and emitted into every brain. CI gate 15
(`tools/check_embed_excluded.py`).

## 1. Why — found by dogfooding, not by a test

Adding `projects/career-plan.md` to the real brain (2026-07-20) failed on commit. The
note was 148 lines — well inside the ~300-line guideline the pre-commit guard nudges at —
and contained a single ASCII roadmap. The embedder returned:

```
{"error":"the input length exceeds the context length"}
```

The art had to be stripped by hand before the note would ingest. Two distinct problems
were behind that, and only one of them is visible:

1. **Dilution (silent).** `canonical_body()` kept everything except frontmatter and
   wikilink markup, so the art was embedded. A note is **one** vector; box-drawing runs
   and column padding carry no meaning but still consume it, pulling the note away from
   what its prose is about. Nothing fails — retrieval just quietly gets worse.
2. **Overflow (loud).** Box-drawing and block characters are brutally token-dense —
   roughly **one token per character**, against ~4 characters per token for prose. So a
   note nowhere near the line guideline can still blow past `nomic-embed-text`'s 2048-token
   context and fail to embed at all.

The transferable half: **line count is the wrong proxy for the embed budget.** The
guideline exists for human readability; the budget is measured in tokens, and the two
diverge exactly where art is involved. `note_view.estimate_tokens` measures the right
thing (see §4).

## 2. The design choice: exclude, don't enlarge

The obvious alternative — raise `num_ctx` so the art fits — was **rejected**. It only
addresses problem 2, and it makes problem 1 worse by admitting more noise into the
vector. Even where a bigger context fits the diagram, **embedding decorative box-art
degrades retrieval quality**. Excluding the region fixes both at once, and costs nothing
at inference time.

The second choice worth naming: the block is cut in **`canonical_body()`**, not at the
embed call. That single choke point is what makes the exclusion consistent across the
three consumers — the embedding (`embed_staged`), the content hash (`embed_staged`'s
no-op gate and `doctor`'s stale detection), and the FTS body (`update_cache`,
`hydrate_cache`). Excluding at the embed call would have desynchronised them, and the
consequence is the nasty one: the hash would still cover the art, so **redrawing a diagram
would re-embed the note and doctor would report it stale on every scan thereafter**. As
built, editing inside the block is free.

Excluding it from the lexical index too is deliberate and follows from the same premise:
the region is decoration, so it should not be *retrievable* either. Only `source_file`
comes back from FTS (no snippets), so nothing about search output changes.

## 3. Why HTML comments as the marker

The marker had to be **Obsidian-benign** — visible junk in the reading view would make
users avoid it. HTML comments are hidden by Obsidian, so the human sees exactly the
fenced code block they wrote and pays nothing for the annotation.

The shape `<!-- second-brain:<feature>:begin -->` matches the markers already in the
system (`register.py`'s global-memory nudge, `autolink.py`'s `related_auto:` block, the
README managed region), and reuses `scripts/marked_block.py` rather than inventing a
parser. A test asserts it does not collide as a substring with the existing
`<!-- second-brain:begin -->` in either direction.

A fence info-string (```` ```no-embed ````) was the other candidate. Rejected: it needs a
real fence scanner rather than the shared marked-block logic, and it forces the excluded
region to *be* a code block — a hand-aligned table or a mermaid diagram could not use it.

### `marked_block.py` grew a read side

The module's documented stance was "raise rather than guess" — correct for **splicing**,
where guessing corrupts a user's file. It is wrong for a **projection**: `canonical_body`
is what `doctor.py` calls, and a diagnostic that throws on the malformed note it exists to
explain is worse than useless. So the two new functions are *total*:

- `remove_all_blocks` — strips **every** complete block (one note may hold several
  diagrams; handling only the first would embed the rest). A `begin` with no following
  `end` delimits nothing, so it is left as literal text and the scan stops.
- `unpaired_markers` — exact complement of what `remove_all_blocks` could strip, so a
  caller can *name* the typo. Not `count(begin) != count(end)`, which calls a stray
  `end … begin` pair balanced.

Failing open means a typo'd marker excludes nothing — the note commits, embeds and
searches fine, just polluted. That is precisely the silent failure worth a warning, which
is §4.

## 4. Warnings, not blocks

`embed_staged` prints two advisory warnings per staged note and never blocks. A
pre-commit hook that refuses a note is a note the user cannot save; the brain's whole
premise is that capture is cheap.

| Warning | Fires when | Why it exists |
|---|---|---|
| unpaired marker | `has_unpaired_no_embed(text)` | The block excluded nothing. Otherwise invisible. |
| over budget | `estimate_tokens(canonical_body(text)) > EMBED_TOKEN_BUDGET` (1800) | Said *before* the backend's opaque `input length exceeds the context length`, because this message can name the fix. |

`estimate_tokens` ships no tokenizer. It approximates from the one property that
separates the two cases — ASCII prose at ~4 characters per token, non-ASCII at ~1 token
each — and is deliberately biased to **over**-count art and **under**-count prose, since a
false warning on a diagram is cheap and a missed one is a failed embed. The budget is set
at 1800 against a 2048 context, leaving room for the backend's task prefix and for the
estimate to run low.

Verified against the motivating case: the reconstructed 50-line note with one roadmap
estimates at **1882 tokens**; fencing the diagram drops it to **10**.

## 5. What ships

Emitted into every brain:

- `scripts/note_view.py` — `NO_EMBED_BEGIN` / `NO_EMBED_END`, `strip_no_embed`,
  `has_unpaired_no_embed`, `estimate_tokens`, `EMBED_TOKEN_BUDGET`; `canonical_body`
  strips the block between frontmatter removal and wikilink stripping.
- `scripts/marked_block.py` — `remove_all_blocks`, `unpaired_markers`.
- `scripts/embed_staged.py` — `warn_embed_input` on every staged note.
- `scripts/self_test.py` — `check_no_embed_invariance`, so **every brain** self-checks
  that the art stays out of the vector and that editing it costs nothing.
- `scripts/mcp_server.py` — `add_note`'s docstring tells the model to fence art (the
  Claude Desktop write path).
- User-facing docs: README "Keep decorative content out of the vector", the note template
  (`seeds/templates/new-note.md`), the brain's `CLAUDE.md`, and SPEC §Note format / §4.

Dev-only:

- `tests/test_note_view.py` (21 tests) — multiple blocks, unpaired markers, hash
  invariance both ways, the Obsidian-benign marker shape, the estimator.
- `tools/check_embed_excluded.py` — **gate 15**. Runs the vendored suite, then asserts the
  three properties independently so a deleted test cannot take the gate with it,
  including the **unmarked** path pinned to a literal digest.

## 6. The compatibility trap this had to avoid

Any change to the canonical view of a note *without* markers would restamp every content
hash in every existing brain — and `update_brain` ships a new view but never re-embeds, so
doctor would report the entire vault stale after an upgrade. Exactly the #26 wikilink-view
episode that motivated task #30's stale detection.

So the unmarked path is bit-for-bit unchanged, and that is pinned twice: the golden's
committed sidecar fixtures still reproduce byte-for-byte (`self_test.py`), and gate 15
compares an unmarked note's hash to a hand-written literal digest that cannot drift with
the implementation.

## 7. Deliberately not done

- **No `doctor.py` finding for an unpaired marker.** A malformed marker cannot reach a
  committed note without passing `embed_staged`, which warns at the moment the fix is one
  edit away. Adding a scan pass would widen doctor's report shape for a case the write
  path already covers.
- **No block-aware rendering anywhere.** `get_note` and Obsidian return the file as
  written — the exclusion is a property of the *view*, never of storage.
- **No auto-fencing.** Nothing detects art and wraps it for you. Deciding what is
  decorative is the author's call, and a wrong guess silently drops meaning.
