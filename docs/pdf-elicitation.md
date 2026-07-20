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
immediate *cancelled* (Anthropic issue #56243). **Claude Code (the CLI) does** (since v2.1.76). So
elicitation is the "good experiment" for the CLI; Desktop keeps the chat baseline. See
[pdf-ingestion.md §2](pdf-ingestion.md).

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

- **Live pass on the Claude Code CLI** — the form UX itself can only be confirmed against a real
  elicitation-capable client; add it to the Desktop-e2e-style manual checklist.
- **Desktop, if it ever ships elicitation** — the same tool lights up with zero changes; watch
  issue #56243 and SEP-1306 (binary-mode elicitation for a true native file picker).
