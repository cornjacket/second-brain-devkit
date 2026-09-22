# Embed-budget audit — the ceiling nothing was watching (task #57)

A note that outgrows the embedding model's context does not degrade. It **fails**:

```
{"error":"the input length exceeds the context length"}
```

No vector, so the note is absent from semantic search entirely. `embed_staged.py` has
warned past `EMBED_TOKEN_BUDGET` since #39 — but only ever about **the note in front of
it**. A vault therefore approaches the ceiling one untouched file at a time, and the first
news is a commit that will not embed.

Found by measuring a real brain, which had **six notes above 85% of budget** and did not
know it. The largest sat roughly **87 words** from the hard limit.

## The number, measured rather than read

`nomic-embed-text` advertises two different context lengths and neither is obviously
authoritative — `ollama show` reports architecture context **2048** and a Modelfile
`num_ctx` of **8192**. Binary search settles it:

| words of filler | result |
| --- | --- |
| 2031 | embeds |
| 2046 | **fails** |

So the embeddings endpoint honours the **architecture's 2048**, not the parameter. The
shipped `EMBED_TOKEN_BUDGET = 1800` sits deliberately below it, leaving room for the
backend's task prefix and for `estimate_tokens()` to run a little low — that margin was
already right and is unchanged.

**It fails loudly rather than truncating.** Worth stating because the opposite would be far
worse: a silent truncation would leave a note *partly* searchable, findable by its opening
and invisible by its end, with nothing anywhere reporting it.

## What was actually missing

Little. The machinery all existed — `EMBED_TOKEN_BUDGET`, `estimate_tokens()`,
fence-aware `canonical_body()`, and the per-note warning. Two narrow gaps:

- **No standing audit.** Nothing answered "which notes are near the ceiling?" across the
  vault. `doctor.py` — the "is my brain ready?" preflight — never mentioned the budget.
- **The line-count nudge fired on `embed: false` files.** A transcription is *meant* to be
  long; splitting it serves nothing. The nudge was noise on every commit touching one, and
  noise is how a warning stops being read.

## doctor reports headroom

Notes at or above `BUDGET_WARN_FRACTION` (85%) are named, worst first; over-budget ones
are individually reported. Counted over `canonical_body`, so **fenced regions and
`embed: false` files correctly cost nothing** — that is the entire point of the fences, and
a file can be enormous while embedding almost nothing.

## `Report.needs_edit` — keeping the closing hint true

Every problem doctor reported before this was machine-fixable, so the summary could always
end with "re-run with `--repair` to fix". An over-budget note is the first kind that cannot
be: nothing but shortening it will do.

Telling someone to run a flag that will report the identical problem again is how a hint
stops being believed. So `needs_edit` counts toward the exit code like `fail`, and is
tallied separately purely so the tail can say **"these need a note edited, not `--repair`"** —
falling back to "to fix what it can" when both kinds are pending.

## Gated

- **Gate 11** (`check_doctor_stale.py`): an over-budget note is named; `--repair` is *not*
  offered for it; and fencing the bulk clears the warning, proving the audit counts the
  embed input rather than the file. The `--repair` assertion first repairs the pending stale
  sidecar — with a repairable problem also outstanding, offering `--repair` is correct, and
  the assertion would otherwise be testing the fixture.
- **Gate 20** (`check_embed_opt_out.py`): the nudge does not fire on an `embed: false` file,
  **and still fires on a real note of the same length** — without the second half the skip
  proves nothing, since disabling the check entirely would also pass.

Both mutation-tested.

## A note on the naming

`check_line_count.py` keeps its name though it now also documents what it is *not*. A
rename would dangle `tasks/0002-markdown-line-count-guard.md` and the PLAN entry recording
its origin, and in this repo history is the generator's source material. Its docstring now
says outright that it is a **readability** nudge and not the embed budget — the two are easy
to confuse because both fire on "the file is big", and they measure different things over
different inputs.
