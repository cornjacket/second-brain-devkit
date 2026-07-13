# MCP server — design & scoping

**Status:** **BUILT — v1 (2026-07-04, golden `4867eec`); glossary tools added (#20, 2026-07-12).**
`scripts/mcp_server.py` implements this design (stdio: `search_second_brain` + `get_note`,
plus the exact-match `list_glossary_terms` + `lookup_glossary_term` — §3, task #20), a thin
wrapper over the brain's own `embedder`/`db`/`search_vault`; the MCP SDK is an
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

Mirror the skill's surface, plus one writer (§3.1):

- **`search_second_brain(query: str, k: int = 5) -> [{source_file, distance, ...}]`**
  The core tool. Embeds `query` with the brain's configured backend and runs the
  same cosine-KNN as `search_vault.py`. Returns **absolute** note paths (the client
  isn't in the brain's cwd), matching what `query.py` already does.
- **`get_note(source_file: str) -> str`** *(optional, likely yes).* Return a note's
  Markdown so the model can read the hit without a second round-trip. Path must be
  validated to live under the brain's `vault/` (no arbitrary file reads).
- **`list_glossary_terms()` + `lookup_glossary_term(term)`** *(**BUILT** — task #20, 2026-07-12).*
  Exact-match, **no-embedding** access to `vault/glossary/` (a non-PARA sibling, kept out of the
  vector index by design — see [glossary.md](glossary.md)). `list_` returns all term names + aliases
  (call it first when unsure a term exists); `lookup_` normalizes (lowercase, strip punctuation,
  spaces/underscores → `-`) + alias-matches (frontmatter `aliases:`) and returns the whole short note,
  with a lead-in-strip miss-fallback (`what is X` → `X`) and `difflib` near-miss suggestions on a real
  miss. The index scans `glossary/*.md` on demand, **mtime-cached on the directory** so a new term
  appears without a restart. Descriptions scope them to explicit "what is X" intent and state the
  glossary is absent from `search_second_brain` — the tool-layer guard that keeps hub-avoidance
  intact. Both register `structured_output=False` like the two above. Behavioral coverage lives in
  `check_mcp_server.py` (the seven-tool surface + the six #20 acceptance checks); its failure modes —
  traversal, substrate disjointness, embedding-free — are the #21 negative suite (§11.1).

- **`add_note(title, para_root, body, tags)` + `list_vault(para_root)` + `get_note_template()`**
  *(**BUILT** — task #5, 2026-07-13; §3.1 below).* The write path, and the browse/template tools
  that let the model decide *where* a note belongs before writing it.

### 3.1 The write path — `add_note` commits **and pushes** (task #5)

v1 was read-only, on the reasoning that an MCP write tool would bypass the git-committed vault
flow and let the cache drift. **The resolution inverts that:** `add_note` doesn't bypass the flow,
it *uses* it. Writing the file and embedding it inline would have been the real bypass — a second
ingestion path forked from the hooks, to be kept in step with them forever. Instead:

- **The commit IS the embed.** `add_note` writes the note and commits it; the **pre-commit** hook
  embeds it and the **post-commit** hook re-hydrates the cache. The note is searchable at once,
  through the one ingestion path the brain already has. Nothing new to keep in sync.
- **The push is what makes it real for anyone else.** A note that lives only on the laptop that
  wrote it is invisible to every other client of the brain (a second machine, a shared or served
  brain — see [big-brain.md](big-brain.md)). Committing without pushing would be a half-measure.

Everything that follows is a consequence of writing to a repo a **human also uses**:

| Hazard | What `add_note` does |
| --- | --- |
| The user has work in progress | Stages **only its own file** and commits with a **pathspec** — never `git add -A`/`commit -a`. Their staged work stays staged, uncommitted. An agent must not author a commit containing someone else's changes. |
| Another client pushed first | Non-fast-forward rejection is *expected* in the multi-client story. Fetch, rebase, retry once. |
| ...and the tree is dirty | **Refuse to rebase** and say so. Rebasing over a user's uncommitted edits from a chat tool is worse than telling them. |
| The push fails anyway | Report it. **The note is committed and searchable locally regardless — a failed push is not a lost note.** Never roll back, never pretend. |
| No remote configured | Commit, and say the brain is local-only. Not an error. |
| Credentials needed, no terminal | `GIT_TERMINAL_PROMPT=0`. The server is headless under Desktop, so a credential prompt has nowhere to appear and would **hang the tool call forever**. Fail fast instead. |
| A traversal payload in the title | The filename comes from a strict **allow-list** slug (`[a-z0-9-]` only), so `../../../etc/passwd` collapses to a plain stem. A resolve-based guard backs it up (defense in depth — and the negative suite confirms *each* layer independently blocks an escape). |
| The note already exists | Refused. `add_note` is **create-only**; editing stays a human/Obsidian job. |
| The hooks aren't installed | Then the commit lands but the note is **not** embedded — a silent, confusing failure. Detected via the missing sidecar and reported loudly. |

**Still not offered:** editing or deleting a note. Create-only is the smallest surface that closes
the gap, and an agent that can silently rewrite a note you authored is a different risk class.

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

## 11.1 Negative / security suite — what the server must *refuse* or *survive* (task #21)

The checks in §10 are the happy path: they prove the server works when used correctly.
`check_mcp_server.py` also drives the failure modes — the security boundary and the
two-substrate isolation — because a contract nobody tests at the edges is a contract that
quietly rots. All of it stays `mcp`-gated (SKIP + exit 0 without the SDK), `test` backend,
no Ollama.

**Path traversal on `get_note`.** `get_note` takes a caller-supplied path, so it is the
server's only untrusted-input surface. The guard resolves the path first and then requires
`vault/` among its parents, which means `..` is collapsed *before* the check. Both halves of
that are asserted: every escape is refused (absolute `/etc/passwd`, a `..` climb out of the
vault, a hop to a real sibling like `config/embedder.toml`, and a relative path — which
resolves against the *brain root*, not `vault/`), **and** a `..` that stays inside the vault
(`<dir>/../<dir>/note.md`) is still served. Refusals must fail *on the vault guard*, not on
an incidental `FileNotFoundError` — a missing file would "pass" a naive test while proving
nothing about the guard. Known gap, out of scope: a symlink inside the vault pointing out
would resolve out and so be refused by the same guard, but nothing in a brain creates one.

**Substrate disjointness.** Semantic search returns only PARA notes; the glossary tools
return only glossary notes. Neither leaks into the other.

**The glossary is embedding-free.** This is the invariant that keeps the glossary out of the
vector index (see [glossary.md](glossary.md) — a definition sits semantically next to every
note that mentions the term, so embedding it would make it a retrieval hub). It is pinned
from two directions, and *both are needed*:

- **Behavioral** — a second server runs against a brain whose vector substrate is destroyed:
  sidecars deleted and `data/brain.db` **poisoned** with garbage bytes. Poisoned, not deleted,
  and that is the whole point: `main()` re-hydrates a *missing* cache on startup, so a deleted
  db is back — empty but valid — before the first tool call, and a glossary that secretly read
  it would still pass. A corrupt db cannot be opened, so any read of the cache now raises.
  Search fails; the glossary must still answer in full.
- **Static** — an AST check that the glossary functions do not so much as *name* `DB_PATH`,
  `brain.db`, `search_vault`, `hydrate_cache`, or `embedder`. This catches the coupling the
  behavioral test cannot see: gating the glossary on `DB_PATH.exists()` changes behavior
  without ever opening the file.

**The suite is itself negative-tested.** Each assertion was confirmed to *fail* when the
invariant it guards is deliberately broken: a naive `".." in path` reject (kills escape
detection), the vault guard removed entirely, the glossary gated on `DB_PATH.exists()`, the
glossary made to query `brain.db`, and `glossary/` added to `PARA_ROOTS` (breaching the
exclusion). A green suite that cannot go red is decoration — the first draft of the
embedding-free check passed against a glossary wired straight into the cache, which is
exactly how the poisoned-db design was found.
