# PDF ingestion — interactive selection via MCP elicitation (task #7 follow-up)

**Status:** Built 2026-07-19. A guided, form-driven PDF picker for clients that support MCP
**elicitation** — today that means the **Claude Code CLI**, not Claude Desktop's chat surface.
Emitted into every brain; falls back to the chat-baseline tools when elicitation is unsupported.

## TL;DR

M6 shipped PDF ingestion with a **chat-baseline** selection UI: `list_inbox_pdfs` returns a list,
you (or the model) read it, then call `add_pdf(path, para_root)`. That works everywhere but is not
*interactive* — nothing prompts you to pick.

This adds one tool, **`add_pdf_guided`**, that walks the choice interactively using MCP
**elicitation** (`ctx.elicit`): pick a **source folder**, then a **PDF in it**, then a **PARA
destination**, each as a small client-rendered form, then it ingests. On a client that does not
implement elicitation it **falls back at runtime** to instructing the chat-baseline flow — so the
same emitted tool is safe on Claude Desktop (chat) and richer on Claude Code (forms).

## Why this is Claude Code, not Desktop

MCP defines an elicitation capability (the server asks the client to render a form and return a
structured answer). **Claude Desktop's Chat surface does not implement it** — it returns an
immediate *cancelled*. **Claude Code (the CLI) is believed to implement it.** So elicitation is
the "good experiment" for the CLI; Desktop keeps the chat baseline. See
[pdf-ingestion.md §2](pdf-ingestion.md).

### Upstream status — rechecked 2026-07-20

The earlier citation of a single issue number was misleading; here is what the tracker actually
says, and what remains unknown.

| Issue | Subject | State |
| --- | --- | --- |
| [#2799](https://github.com/anthropics/claude-code/issues/2799) | Add support for MCP elicitation (the CLI) | **CLOSED / COMPLETED** 2026-04-25 |
| [#56243](https://github.com/anthropics/claude-code/issues/56243) | Desktop chat returns `cancel` without rendering; CLI works | **CLOSED as DUPLICATE** of #48164, then locked — *never fixed* |
| [#48164](https://github.com/anthropics/claude-code/issues/48164) | **URL-mode** elicitation not supported in the CLI | **OPEN** (reopened) |

Three things follow:

- **The Desktop gap is real but effectively untracked upstream.** #56243 was auto-closed as a
  duplicate of #48164 by a bot, and the two are not the same bug — #56243 is *form*-mode in
  Desktop, #48164 is *URL*-mode in the CLI. Do not read "closed" as "fixed"; nothing in the
  thread claims a fix. Cite it as history, not as a live tracking issue.
- **#48164 does not apply to us.** We use form mode (a one-field schema with a `Literal` enum),
  not URL mode. Its being open is not a blocker for this design.
- **The "since v2.1.76" version claim has been removed** — it could not be corroborated from a
  primary source, and it is inconsistent with #2799 closing on 2026-04-25. Moot in practice: the
  observed fallback below happened on **2.1.215**, far past any candidate version.

### The unexplained fallback (open — task #40)

On 2026-07-20, `add_pdf_guided` fell back to the chat flow on **Claude Code CLI 2.1.215**, with
#2799 closed as completed. That contradicts the table above, and **we cannot yet say why**:
`_elicit_choice` catches every exception and treats every non-`accept` action alike, so
"unsupported", "you cancelled", and "the request errored" are one indistinguishable outcome. The
fallback string asserts the *first* of those, which is a guess the code is not entitled to make.

Compounding it, a client lacking the capability returns a synthetic `{"action":"cancel"}` — byte
-identical to a human pressing Escape. So guessing is unavoidable *unless the server checks the
declared capability first*, which it does not. **Task #40 fixes the diagnostics; until it lands,
a live CLI pass cannot be interpreted** — a genuine failure and a stray Escape look the same.

## Design

- **One shared enumeration core, two front-ends.** The selection data comes from the same
  `add_pdf.inbox_folders()` / `add_pdf.list_pdfs()` the chat tools use — this is purely a second
  presentation, not a second code path.
- **Sequential elicitation.** The PDF list depends on the chosen folder, so the picks are
  sequential: folder → PDF-in-folder → PARA root. Each is one `ctx.elicit` call.
- **Enum forms via a dynamic schema.** MCP elicitation allows **primitive** fields only; a choice
  is a string field with an `enum`. The choices are runtime values (folder paths, filenames), so
  the Pydantic schema is built per call with `create_model(field=(Literal[tuple(choices)], ...))`.
- **Runtime fallback is the capability gate.** A client without elicitation returns a non-`accept`
  action (decline/cancel) or errors; either way the tool returns a short message pointing at the
  chat flow (`list_inbox_pdfs` → `add_pdf`). No hard dependency, no capability handshake to
  maintain — detect and adapt, never force (the brain's usual stance).
- **Reuses the ingest engine and its guards.** After the three picks it calls the same
  `add_pdf.add_pdf(path, para_root)` — same move/extract/chunk/embed/load, same no-commit/no-push,
  same "needs pypdf" message. The security boundary is implicit: choices come only from the
  configured source folders.

## Shape

```
add_pdf_guided(ctx)                      # no model-visible args — ctx is injected by FastMCP
  folders = inbox_folders() (existing)   # -> elicit "Which source folder?"  (enum)
  pdfs    = list_pdfs(folder)            # -> elicit "Which PDF?"             (enum)
  para    = PARA_ROOTS                   # -> elicit "Into which PARA folder?"(enum)
  add_pdf(folder/pdf, para)              # ingest; report chunks now searchable
  any non-accept  ->  fall back to the chat-baseline instructions
```

## Testing

The `ctx.elicit` round-trip needs a live elicitation-capable client, so it is not exercised in CI.
The **orchestration** is: a fake `ctx` whose `elicit` returns canned `accept`ed answers drives the
three-step flow and asserts it ingests the chosen file; a fake `ctx` whose `elicit` cancels (or
raises) asserts the fallback message and that nothing is ingested. `add_pdf.add_pdf` is stubbed so
the flow test needs no pypdf. (`tests/test_mcp_pdf.py`, gate 14.)

## Open items

- **Task #40 first — make the failure legible.** Blocks the live pass below: today a genuine
  "unsupported" and a stray Escape produce the same message, so a run cannot be interpreted.
- **Live pass on the Claude Code CLI** — the form UX itself can only be confirmed against a real
  elicitation-capable client; add it to the Desktop-e2e-style manual checklist. Note the observed
  2026-07-20 fallback happened on the CLI, so this is now a *diagnosis*, not a formality.
- **Desktop, if it ever ships elicitation** — the same tool lights up with zero changes. Do not
  watch #56243 (closed as a duplicate and locked); there is no live upstream issue tracking the
  Desktop form-mode gap. SEP-1306 (binary-mode elicitation, for a true native file picker) is
  separate and still of interest.
