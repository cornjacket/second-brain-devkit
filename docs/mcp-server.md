# MCP server — design & scoping

**Status:** **BUILT — v1 (2026-07-04, golden `4867eec`).** `scripts/mcp_server.py`
implements this design (stdio, read-only `search_second_brain` + `get_note`, thin
wrapper over the brain's own `embedder`/`db`/`search_vault`); the MCP SDK is an
isolated optional dep (`requirements-mcp.txt`). Registration is print-and-instruct in
the README for v1 (auto-insert deferred). Build-time decisions settled in
[OQ-6](../open-questions.md#oq-6); tracked in
[PLAN.md](../PLAN.md#milestone-g6--the-ai-interface-reach-the-brain-from-any-project).
This doc remains the design rationale. For the step-by-step user journey (install →
register → enable → use), see [claude-desktop-workflow.md](claude-desktop-workflow.md).

This document scopes an **MCP server** that lets a chat client reach the brain when
it **cannot shell out to local Python**. It is deliberately the *secondary* path —
the emitted `second-brain` skill (Bash → `query.py`) already serves every
CLI/agent client at near-zero standing token cost. Read [PLAN G6](../PLAN.md) first
for why the skill is primary.

---

## 1. Why (and why secondary)

The skill works by having the agent run `python3 query.py "…"` via its Bash tool.
That covers Claude Code, Gemini CLI, and any agent with shell access. It does **not**
cover a chat surface with no local shell — the motivating case is **Claude Desktop**,
where the user chats with the brain but the client can only call **MCP tools**, not
run arbitrary local commands.

Standing cost is the reason it stays secondary: an MCP server's tool schemas load
into context **every session** whether or not the brain is consulted, whereas the
skill uses progressive disclosure (only its name + description preload; the body
loads on invoke) and adds **zero** new tool schema by reusing the existing Bash
tool. So MCP is added *only* for clients the skill cannot serve — never as the
default.

## 2. The constraint that reshapes scope — local vs. web

MCP transport determines which clients are actually reachable, and this is the
single most important scoping decision:

- **`stdio` (local subprocess).** The client launches the server as a local
  process and talks over stdin/stdout. **Claude Desktop supports this.** The server
  runs on the user's machine, so it can read the local vault + `data/brain.db` and
  call the local Ollama server directly. **This is the realistic target.**
- **Remote (HTTP/SSE).** Required for **claude.ai in the browser** — a web page
  cannot spawn or reach a local `stdio` process. But a remote server contradicts the
  brain's **local-first, no-cloud** invariant (SPEC §7): it would mean hosting the
  vault + embeddings + Ollama somewhere reachable from the public web, with auth.

**Scoping conclusion:** target **`stdio` + Claude Desktop only**. Treat claude.ai
web as **out of scope** — serving it would require a hosted brain, which breaks
local-first. Document that limitation rather than pretend the skill/MCP split
covers web chat. (If web access is ever wanted, it's a separate "hosted brain"
project with its own security model, not this server.)

## 3. What it exposes (tools)

Mirror the skill's surface — read-only, minimal:

- **`search_second_brain(query: str, k: int = 5) -> [{source_file, distance, ...}]`**
  The core tool. Embeds `query` with the brain's configured backend and runs the
  same cosine-KNN as `search_vault.py`. Returns **absolute** note paths (the client
  isn't in the brain's cwd), matching what `query.py` already does.
- **`get_note(source_file: str) -> str`** *(optional, likely yes).* Return a note's
  Markdown so the model can read the hit without a second round-trip. Path must be
  validated to live under the brain's `vault/` (no arbitrary file reads).

**Read-only by default.** No note-creation/editing tool in v1 — writing goes through
the git-committed vault flow (pre/post-commit hooks embed + hydrate), which an MCP
write tool would bypass, risking drift. **There is currently no way to _add_ a note to
the brain from Claude Desktop** — a real gap tracked as a
[PLAN G6 task](../PLAN.md#milestone-g6--the-ai-interface-reach-the-brain-from-any-project):
a future `add_note`/`create_note` tool must write into a PARA root **and** run the
same embed → hydrate path the hooks do (or make a real commit), so the new note is
actually searchable and history stays consistent — not just drop a file on disk.

## 4. Architecture — thin wrapper over existing scripts

The server is a **thin adapter**, not new retrieval logic. It reuses the brain's
own modules so there is exactly one embedding/search implementation:

```
Claude Desktop ──stdio──▶ scripts/mcp_server.py
                              │  reuses, in-process:
                              ├─ embedder.py   (embed the query; same-model invariant)
                              ├─ db.py         (connect w/ WAL + busy_timeout, sqlite-vec)
                              └─ search_vault  (cosine-KNN over data/brain.db)
                                     │
                              Ollama (localhost:11434) + data/brain.db
```

- Resolve the brain root **relative to the server file** (like `query.py`'s
  `parents[2]`) so it works wherever it's installed/symlinked — no hardcoded path.
- Reuse `search_vault.py`'s query path. It's currently a CLI `main()`; scope a small
  refactor to expose a reusable `search(query, k) -> rows` function that both the
  CLI and the MCP server call (avoid shelling out from inside a long-lived server).
- Ensure-cache-on-start like `query.py` (hydrate if `data/brain.db` is missing).

## 5. Concurrency coupling — this is what unlocks OQ-5 layers 2 & 3

The MCP server is a **long-lived reader**: it holds a `db.connect()` open across
many queries while, in another process, a **post-commit `hydrate_cache.py`** may
fire and `unlink()`+rebuild `data/brain.db`. That is exactly the hazard
[OQ-5](../open-questions.md#oq-5) flagged and the reason layers 2 & 3 are scoped
**here**, not earlier:

- **Layer 1 (done)** — `db.connect()` already sets `journal_mode=WAL` +
  `busy_timeout`, so a reader and a writer no longer collide on locking.
- **Layer 2 (build with the server)** — replace `hydrate`'s `unlink()`+rebuild with
  an **in-transaction** rebuild (`DELETE FROM notes`, or temp-table swap) so the
  long-lived reader sees old rows until commit, then new, atomically. Without this,
  the server can observe a missing/half-built DB mid-rebuild.
- **Layer 3 (if needed)** — a `flock` writer lock if overlapping writers
  (post-commit vs. `doctor --repair`) prove real in practice.

**Sequencing:** land layer 2 **before or with** the server; ship layer 3 reactively.

## 6. Dependencies — keep the core lean and CI stdlib-only

The server needs an MCP SDK (the `mcp` Python package). Hard rules:

- **Optional, isolated dependency.** MCP must **not** enter the base
  `requirements.txt` (which the plumbing/CI rely on staying minimal —
  `sqlite-vec` + `apsw`). Put it in an **extra** (e.g. `requirements-mcp.txt` or an
  optional group) installed only by users who want the Desktop path.
- **CI never runs it.** Like `doctor.py`/`update_cache.py`, the emitted
  `mcp_server.py` is **byte-compared + forbidden-ref-scanned**, never executed in
  CI (CI is `test`-backend, no Ollama, no MCP SDK). Generation fires no server.
- **Zero forbidden references** (SPEC §5.2) — nothing devkit-internal leaks in.

## 7. Registration & install

Claude Desktop reads a JSON config (`claude_desktop_config.json`) listing MCP
servers to launch. Follow the installer philosophy already set by
`install_skill.py`: **detect + instruct, `--apply`-gated, never silently mutate a
user's config.**

- Extend `install_skill.py` (or a sibling) with an opt-in step that prints/inserts
  the server stanza — `command: python3`, `args: [<brain>/scripts/mcp_server.py]` —
  into the Desktop config, dry-run by default, idempotent (marker-guarded like the
  `--nudge` block), and reversible via `--uninstall`.
- Detect a missing config/app and instruct rather than create blindly.

## 8. Emission plan (when built)

- `scripts/mcp_server.py` → **verbatim** emit (manifest), like the other scripts.
- `requirements-mcp.txt` (or optional group) → verbatim.
- `search_vault.py` refactor to expose `search()` → still verbatim, byte-diffed.
- README: a short "Use from Claude Desktop (MCP)" section; installer `--help`.
- Prototype in the golden first (build a live server, point Claude Desktop at it,
  confirm a real query returns hits) → vendor → template → `ci.py` green.

## 9. Open questions → [OQ-6](../open-questions.md)

All five build-time sub-decisions are **settled** in
[OQ-6](../open-questions.md#oq-6) now that v1 is built: SDK = official `mcp`
(`mcp>=1.2`); `get_note` shipped in v1; per-brain root resolution; registration =
print-and-instruct for v1 (auto-insert deferred); claude.ai-web confirmed out of
scope. This section is retained as the original design record.

## 10. Verifying the server (dev recipe — no Claude Desktop needed)

An MCP server speaks JSON-RPC over stdin/stdout, so you don't test it by running it
and typing — a **client** launches it as a subprocess and calls its tools. This is
the exact recipe used to accept v1 (2026-07-04); keep it as the reproducible check.

```python
# mcp_smoke.py — drive the server the way Claude Desktop does.
#   pip install mcp            (already in the brain's requirements-mcp.txt)
#   python3 mcp_smoke.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = "/ABSOLUTE/PATH/TO/second-brain/scripts/mcp_server.py"

async def main():
    params = StdioServerParameters(command="python3", args=[SERVER])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()                                   # MCP handshake
            print("tools:", [t.name for t in (await s.list_tools()).tools])
            res = await s.call_tool("search_second_brain",
                                    {"query": "how do vector databases work?", "k": 3})
            hits = json.loads(res.content[0].text)                 # text block (see §11)
            for hit in hits:
                print(f"  {hit['distance']:.4f}  {hit['source_file']}")
            note = await s.call_tool("get_note", {"source_file": hits[0]["source_file"]})
            print("first note starts:", repr(note.content[0].text[:60]))
            bad = await s.call_tool("get_note", {"source_file": "/etc/passwd"})
            print("outside-vault refused:", bad.isError)           # -> True

asyncio.run(main())
```

(Import `json` at the top. The results arrive as a **text block**, not
`structuredContent`, because of the compatibility decision in §11.)

## 11. Compatibility gotcha — Claude Desktop drops tools with `outputSchema` (2026-07-04)

**Symptom found live:** the server connected, appeared in **Customize → Connectors**
as `second-brain (LOCAL DEV)`, and logged a clean `tools/list` — but the pane said
**"This connector has no tools available,"** so the model never called it. A
standalone Python MCP client (latest SDK) connected to the *same* server and saw
both tools, which localized the fault to Desktop's client.

**Cause:** the tools have typed returns (`-> list[dict]`, `-> str`), so modern
FastMCP auto-advertises an **`outputSchema`** ("structured output," a newer MCP
feature; the server negotiated protocol `2025-11-25`). Claude Desktop's embedded MCP
client (as of this date) predates that field and **silently discards any tool
carrying it**.

**Fix (shipped):** `@mcp.tool(structured_output=False)` on every tool. No
`outputSchema` is emitted; each tool becomes a classic text-output tool every client
accepts, and the return still reaches the model as a JSON text block. Verified end to
end in Claude Desktop after a full restart.

**Lessons for future MCP work here:** (1) **test against the real target client**, not
just a same-SDK Python client — the same SDK speaks the same newest protocol and hides
exactly this skew; (2) prefer classic text-output tools for broad client
compatibility; (3) *"no tools available"* ≠ *"server broken"* — a clean handshake
proves nothing about callability; confirm a real `CallToolRequest` reaches the server
log. Revisit `structured_output` once Desktop's MCP client supports `outputSchema`.
Expected: two tools listed; `search` returns absolute vault paths with cosine
distances (real Ollama backend clusters relevant notes near ~0.3–0.5; the `test`
backend is meaningless-but-nonzero); `get_note` returns Markdown; an out-of-vault
read is refused (`isError: True`). Requires Ollama running for a real brain. The
server prints its own progress to **stderr**, so stdout stays a clean JSON-RPC
channel — if a client ever fails to handshake, suspect something writing to stdout.
