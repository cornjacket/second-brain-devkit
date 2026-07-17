# Claude Desktop e2e — canned prompts + side-effect verifiers (task #33)

**Status:** **BUILT 2026-07-16** — the suite lives at `desktop-e2e/` (5 pasteable prompts + 5
side-effect verifiers + `run_all.py` + protocol README). Validated against a simulated fixture:
the deterministic checks pass on a correct brain and fail when the side effect is absent. It is a
human-in-the-loop release-acceptance ritual, **not** a CI gate — running it needs the real Desktop
app and a person to paste the prompts. Devkit-only (outside `tests/golden/`, so no manifest entry
and no emission).

## 1. Why — the gap the SDK harness cannot close

`tools/check_mcp_server.py` (gate G6) drives the emitted stdio server with a **Python MCP
client** and asserts the tool contract, path-traversal refusal, and substrate isolation. That
proves the server *logic*, but it runs a **different client than Claude Desktop** — so it is
structurally blind to Desktop-client bugs. The live one that motivates this: Desktop **silently
dropped every tool advertising an `outputSchema`** (2026-07-04), so the model never called them,
while a same-SDK Python client saw them fine (see [mcp-server.md §11](mcp-server.md)). Only the
**real client** catches that class of fault. There is no API to drive Desktop's GUI, so the
driver has to be a human — but the *oracle* can still be a script.

This is the same shape as the repo's existing **Obsidian hand-tests** (the glossary
flashcard/graph acceptance in [PLAN.md](../PLAN.md)): acceptance that CI can never reach because
it lives in a GUI. This task formalizes that pattern for Desktop + MCP.

## 2. The load-bearing constraint — assert side effects, never prose

An LLM's chat text is non-deterministic; asserting it is a trap. So each prompt is engineered to
force an **observable, deterministic side effect**, and the verifier checks *that*, not the
reply:

- **Write-path effects** — `add_note` / `add_glossary_term` create a file with known frontmatter
  and make a git commit. The verifier checks the file exists, the `tags:`/`aliases:` match, and
  `git log` shows the commit. Fully deterministic.
- **Server-side log** — the server prints progress to **stderr** (stdout is the JSON-RPC
  channel), so a captured server log can confirm *which tool was called with which args*. The
  prompt is the trigger; the log is proof the model routed to the intended tool.
- **Refusals** — a prompt that asks for `get_note` on `/etc/passwd` must come back refused; the
  verifier checks the note was *not* read (no traversal), not the wording of the refusal.
- **Not assertable:** the exact ranking/prose of a search answer. At most assert "search was
  called and returned known vault paths in the top-k," and only with a fixed backend (below).

## 3. Shape (built)

```
desktop-e2e/
  README.md              # the human protocol: generate a fixture brain, point Desktop at it,
                         # paste prompts in order, run the verifiers
  prompts/               # one file per scenario — pasteable verbatim into Desktop
    01-add-note.md
    02-near-miss-tag.md  # exercises the #32 write-time TAG HINT (see §4)
    03-glossary-add.md
    04-path-traversal.md
    05-search-known.md
  verify/                # one script per scenario — checks brain state + server log, exit 0/1
    verify_01_add_note.py
    ...
```

Emission: **devkit-only** (a dev/release artifact, like the bench corpus) — never emitted into a
brain. Lives outside `tests/golden/`, so no manifest entry.

## 4. A concrete scenario (ties to #32)

Prompt `02-near-miss-tag.md`: *"Add a note titled 'Planner agents' to resources, body '…', tags:
[ai-agent]"* — into a fixture brain whose vocabulary already has `ai-agents`. Expected
observable outcome: the note is created **and** `add_note`'s reply carries the
`TAG HINT: 'ai-agent' is close to existing 'ai-agents' …` advisory. The verifier checks the note
landed and (from the captured server response/log) that the hint text was returned. This is how
we prove the write-time warning actually *reaches the model in Desktop*, not just the Python
client.

## 5. Open questions

- **Backend.** A `test`-backend fixture brain is deterministic but its search returns test
  vectors (meaningless ranking); a real `ollama` backend gives realistic search but non-stable
  ordering. Likely answer: **test backend for write-path/tool-routing/refusal scenarios** (the
  deterministic majority) and treat search-quality as a separate, looser eyeball.
- **Capturing the server log deterministically.** Desktop launches the server; how does the
  verifier get its stderr? Options: a wrapper `command` in `claude_desktop_config.json` that
  tees stderr to a file; or assert purely on brain state + git for scenarios that have a
  file/commit effect (most of them).
- **Prompt robustness vs model drift.** A prompt that reliably forces a tool call today may
  route differently after a model update. Keep prompts imperative and unambiguous ("Use add_note
  to create…"), and treat a routing change as a real signal, not noise.
- **Toolset evolution.** As tools are added/renamed the prompts + verifiers drift; pin each
  scenario to the tool it exercises so a stale one fails loudly.

## 6. Scope boundary

This is **release acceptance run by a human**, not a gate. It complements — does not replace —
G6 (`check_mcp_server.py`), which stays the fast, CI-able, SDK-client contract test. Value is
highest right after a Desktop update or an MCP-surface change, where a client-compat regression
would otherwise ship silently.
