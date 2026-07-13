# Claude Desktop workflow — end to end

The whole journey from *nothing* to *chatting with your brain in Claude Desktop*, in
order. This stitches together pieces that also live in the brain's README (user steps)
and [`mcp-server.md`](mcp-server.md) (design, verify recipe, the gotcha) — follow the
links rather than re-reading duplicated detail.

**Why Desktop at all?** The `second-brain` **skill** already serves any client that can
run a shell command (Claude Code, Gemini CLI) at near-zero cost. Claude Desktop can't
shell out — it reaches tools only over **MCP** — so a brain ships an optional MCP server
just for it. Local-only; read, plus `add_note` (which commits + pushes). See [mcp-server.md §1–2](mcp-server.md).

---

## The flow

```
own a brain ─▶ deps + Ollama ─▶ embed ─▶ install Desktop ─▶ register (config)
    ─▶ restart ─▶ enable connector ─▶ use in a plain Chat ─▶ (verify / troubleshoot)
```

### 1. Own a brain
Generate one with `python3 tools/create_second_brain.py ~/my-brain` (Mode B), or use an existing
brain. The MCP server resolves its own brain root, so it works wherever the brain lives.

### 2. Install dependencies
From the brain root: `pip install -r requirements.txt -r requirements-mcp.txt`. The
second file is the **optional** MCP SDK — install it into the **same interpreter** you'll
name in step 5.

### 3. Turn on Ollama and embed
Search needs real vectors. Start Ollama, pull `nomic-embed-text`, then embed + build the
cache — `python3 scripts/doctor.py --repair` does the embed + hydrate and reports
readiness (or `embed_vault.py` → `hydrate_cache.py`). `doctor.py` with no flag confirms
`brain healthy & consistent`.

### 4. Install Claude Desktop
Download from [claude.ai/download](https://claude.ai/download) and sign in.

### 5. Register the server (the gotcha step)
**Settings → Developer → Edit Config** opens `claude_desktop_config.json`. Add an
`mcpServers` entry (merge with any existing keys):

```json
{
  "mcpServers": {
    "second-brain": {
      "command": "/ABSOLUTE/PATH/TO/python3",
      "args": ["/ABSOLUTE/PATH/TO/brain/scripts/mcp_server.py"]
    }
  }
}
```

**Use the absolute interpreter path, not `python3`.** Desktop launches with a minimal
environment, so a bare `python3` — especially a **pyenv/conda shim** — may resolve to the
wrong Python or one without `mcp`. Resolve the real binary first (`pyenv which python3`,
etc.). This is the #1 "server won't start" cause.

### 6. Restart fully
**Cmd+Q** (closing the window isn't enough) and reopen, so Desktop launches the server
and reads its tools.

### 7. Enable the connector
**Customize → Connectors → `second-brain`** should list `search_second_brain` and
`get_note`.

> **"This connector has no tools available."** Claude Desktop's MCP client (as of
> 2026-07-04) silently drops tools that advertise an `outputSchema`. The shipped server
> already avoids this (`@mcp.tool(structured_output=False)`); you'd only hit it by
> re-enabling structured output. Full write-up: [mcp-server.md §11](mcp-server.md).

### 8. Use it
In a **plain Chat** (not Cowork/Code), point at the tool:
> *Use the second-brain tool to search my notes for X, then summarize what you find.*

Approve the one-time in-app **"Allow tool?"** prompt (a button, **not** a Finder folder
picker — that dialog belongs to Desktop's local-agent mode, not this server). Claude then
calls `search_second_brain`, optionally `get_note` on a hit, and answers from your notes.

### 9. Verify / troubleshoot
- **Verify without the app** — drive the stdio server with a tiny MCP client; recipe in
  [mcp-server.md §10](mcp-server.md) and the brain README.
- **Logs** — `~/Library/Logs/Claude/mcp-server-second-brain.log`. A clean handshake +
  `tools/list` is not enough; confirm a real `CallToolRequest` arrives when you ask.
- **Empty results** — Ollama down or cache unbuilt → `doctor.py --repair`.
- **Can't handshake** — something wrote to stdout (the JSON-RPC channel); the server
  keeps stdout clean by routing its own output to stderr.

---

## Lessons baked in (see [mcp-server.md §11](mcp-server.md))
1. **Test against the real client**, not just a same-SDK Python client — the same SDK
   speaks the newest protocol and hides version skew.
2. **Absolute interpreter path** for GUI-launched processes; never rely on a shim.
3. **"No tools available" ≠ broken server** — a clean handshake says nothing about
   callability; check for a real `CallToolRequest`.

## Adding a note from Desktop (task #5, built 2026-07-13)
`add_note(title, para_root, body, tags)` creates a note, **commits** it — which is what
embeds it, via the pre-commit hook, so it is searchable immediately — and **pushes** it,
so it reaches the brain's other clients instead of living on one laptop. Ask Claude to
save something and it will typically `list_vault` first (to see where it belongs), then
write. It only ever commits **its own file**, so work you have in progress is never swept
into a commit you didn't write, and it won't overwrite an existing note. See
[mcp-server.md §3.1](mcp-server.md).

## Not covered (by design)
**Editing or deleting** a note from Desktop — `add_note` is create-only; changing a note
you wrote stays a human/Obsidian job. Web chat (claude.ai) — a browser can't reach a local
stdio server; out of scope ([mcp-server.md §2](mcp-server.md)).
